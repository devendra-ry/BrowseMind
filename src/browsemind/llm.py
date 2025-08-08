import json
import logging
import re
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from browsemind.config import AgentConfig
from browsemind.exceptions import LLMError
from browsemind.reliability import CircuitBreaker, RateLimiter, retry_with_backoff, timeout_wrapper

logger = logging.getLogger(__name__)

# Global rate limiter and circuit breaker for LLM calls
_llm_rate_limiter = None
_llm_circuit_breaker = None

SYSTEM_PROMPT = """You are an expert AI browsing agent. Your goal is to perform a task based on the user's request.
You will be given the current page content and a list of interactable elements, each with a unique `browsemind-id`.
Your response must be a JSON object wrapped in a ```json ... ``` code block with the following schema:
{
    "action": "action_name",
    "args": {
        "arg_name": "arg_value"
    }
}

Available actions:
- navigate(url: str): Navigates to the given URL.
- type(id: int, text: str, press_enter_after: bool): Types text into the element with the specified `browsemind-id`. Set `press_enter_after` to true to submit a form or search.
- click(id: int): Clicks on the element with the specified `browsemind-id`.
- summarize(): Summarizes the current page content.
- finish(result: str): Finishes the task and returns the result.

Based on the current page content and the user's goal, choose the best action to take.
"""


def _initialize_reliability_components(config: AgentConfig) -> None:
    """Initialize global reliability components."""
    global _llm_rate_limiter, _llm_circuit_breaker

    if _llm_rate_limiter is None:
        # Initialize rate limiter: X requests per minute
        requests_per_minute = config.llm_rate_limit_requests_per_minute
        time_window = 60.0  # 1 minute
        _llm_rate_limiter = RateLimiter(requests_per_minute, time_window)
        logger.info(f"Initialized LLM rate limiter: {requests_per_minute} requests per minute")

    if _llm_circuit_breaker is None:
        # Initialize circuit breaker
        _llm_circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60.0)
        logger.info("Initialized LLM circuit breaker")


def get_llm(config: AgentConfig) -> ChatGoogleGenerativeAI:
    """
    Initializes and returns the ChatGoogleGenerativeAI instance.

    Args:
        config: The agent configuration.

    Returns:
        A ChatGoogleGenerativeAI instance.

    Raises:
        LLMError: If the LLM fails to initialize.
    """
    try:
        # Initialize reliability components if not already done
        _initialize_reliability_components(config)

        logger.info(f"Initializing LLM with model: {config.model_name}")
        llm = ChatGoogleGenerativeAI(
            model=config.model_name,
            temperature=config.temperature,
            google_api_key=config.google_api_key,
        )
        logger.info("LLM initialized successfully")
        return llm
    except Exception as e:
        logger.error(f"Failed to initialize LLM: {e}")
        raise LLMError(f"Failed to initialize LLM: {e}", "LLM_INIT_ERROR") from e


async def get_next_action(
    llm: ChatGoogleGenerativeAI, page_content: str, task: str, config: AgentConfig | None = None
) -> dict[str, Any]:
    """
    Gets the next action from the LLM based on the current page content and task.

    Args:
        llm: The ChatGoogleGenerativeAI instance.
        page_content: The content of the current web page.
        task: The user's task description.
        config: The agent configuration (optional, for reliability settings).

    Returns:
        A dictionary representing the next action to take.

    Raises:
        LLMError: If the LLM fails to generate a response or if the response is invalid.
    """
    # Validate inputs
    if not isinstance(task, str):
        raise LLMError("Task must be a string", "INVALID_TASK_TYPE")

    if config and len(task) > config.max_task_length:
        raise LLMError(
            f"Task length ({len(task)}) exceeds maximum allowed length ({config.max_task_length})",
            "TASK_TOO_LONG",
        )

    if config and len(page_content) > config.max_page_content_length:
        raise LLMError(
            f"Page content length ({len(page_content)}) exceeds maximum allowed length ({config.max_page_content_length})",
            "PAGE_CONTENT_TOO_LONG",
        )

    logger.info(f"Requesting next action from LLM for task: {task}")
    logger.debug(f"Page content length: {len(page_content)}")

    # Check circuit breaker
    if _llm_circuit_breaker and not _llm_circuit_breaker.can_execute():
        logger.error("LLM circuit breaker is open")
        raise LLMError("LLM service is temporarily unavailable", "LLM_CIRCUIT_BREAKER_OPEN")

    async def _invoke_llm_with_retry() -> dict[str, Any]:
        """Inner function to invoke LLM with retry logic."""
        nonlocal llm, page_content, task, config

        try:
            # Acquire rate limiter permit
            if _llm_rate_limiter:
                await _llm_rate_limiter.acquire()

            try:
                logger.debug("Creating prompt")
                prompt = ChatPromptTemplate.from_messages(
                    [
                        ("system", SYSTEM_PROMPT),
                        ("human", "Page Content:\n{page_content}\n\nTask: {task}"),
                    ]
                )
                logger.debug("Prompt created successfully")
            except Exception as e:
                logger.error(f"Failed to create prompt: {e}")
                raise LLMError(f"Failed to create prompt: {e}", "PROMPT_ERROR") from e

            try:
                logger.debug("Creating chain")
                chain = prompt | llm
                logger.debug("Chain created successfully")
            except Exception as e:
                logger.error(f"Failed to create chain: {e}")
                raise LLMError(f"Failed to create chain: {e}", "CHAIN_ERROR") from e

            async def _invoke_chain() -> Any:
                """Inner function to invoke the chain with timeout."""
                return await chain.ainvoke({"page_content": page_content, "task": task})

            # Apply timeout if configured
            timeout = config.llm_request_timeout if config else 300
            try:
                logger.debug(f"Invoking LLM with timeout: {timeout} seconds")
                response = await timeout_wrapper(_invoke_chain, timeout)
                logger.debug("LLM invoked successfully")
            except Exception as e:
                logger.error(f"Failed to invoke LLM: {e}")
                raise LLMError(f"Failed to invoke LLM: {e}", "LLM_INVOKE_ERROR") from e

            try:
                content = response.content
                content_str = str(content)
                logger.debug(f"Response content length: {len(content_str)}")
            except Exception as e:
                logger.error(f"Failed to extract content from response: {e}")
                raise LLMError(
                    f"Failed to extract content from response: {e}", "CONTENT_EXTRACTION_ERROR"
                ) from e

            # Use a regex to find the JSON object within the ```json ... ``` block
            try:
                logger.debug("Searching for JSON in response")
                json_match = re.search(r"```json\n(.*?)\n```", content_str, re.DOTALL)
                logger.debug("JSON search completed")
            except Exception as e:
                logger.error(f"Failed to search for JSON in response: {e}")
                raise LLMError(
                    f"Failed to search for JSON in response: {e}", "JSON_SEARCH_ERROR"
                ) from e

            if not json_match:
                logger.error(f"No JSON object found in LLM response. Response was: {content_str}")
                raise LLMError(
                    f"No JSON object found in LLM response. Response was: {content_str}",
                    "MISSING_JSON_ERROR",
                )

            try:
                json_string = json_match.group(1)
                logger.debug(f"Extracted JSON string length: {len(json_string)}")
            except Exception as e:
                logger.error(f"Failed to extract JSON string: {e}")
                raise LLMError(
                    f"Failed to extract JSON string: {e}", "JSON_EXTRACTION_ERROR"
                ) from e

            try:
                logger.debug("Parsing JSON")
                result = json.loads(json_string)
                logger.debug("JSON parsed successfully")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to decode JSON from LLM. Response: {content_str}. Error: {e}")
                raise LLMError(
                    f"Failed to decode JSON from LLM. Response: {content_str}. Error: {e}",
                    "JSON_DECODE_ERROR",
                ) from e
            except Exception as e:
                logger.error(f"Failed to parse JSON from LLM: {e}. Response: {content_str}")
                raise LLMError(
                    f"Failed to parse JSON from LLM: {e}. Response: {content_str}",
                    "JSON_PARSE_ERROR",
                ) from e

            # Ensure we return a dict
            if isinstance(result, dict):
                logger.info(f"Successfully extracted action: {result.get('action')}")
                return result
            else:
                logger.error(f"LLM response is not a dictionary: {result} (type: {type(result)})")
                raise LLMError(
                    f"LLM response is not a dictionary: {result} (type: {type(result)})",
                    "INVALID_RESPONSE_TYPE",
                )

        except Exception as e:
            # Record failure in circuit breaker
            if _llm_circuit_breaker:
                _llm_circuit_breaker.on_failure()
            raise e

    try:
        # Apply retry logic if configured
        if config and config.llm_max_retries > 0:
            result = await retry_with_backoff(
                _invoke_llm_with_retry,
                max_retries=config.llm_max_retries,
                base_delay=config.llm_retry_delay,
                max_delay=60.0,
                exponential_base=2.0,
                jitter=True,
            )
        else:
            result = await _invoke_llm_with_retry()

        # Record success in circuit breaker
        if _llm_circuit_breaker:
            _llm_circuit_breaker.on_success()

        return result

    except LLMError:
        # Re-raise LLMErrors as they are already properly formatted
        raise
    except Exception as e:
        logger.error(f"Failed to get next action from LLM: {e}")
        raise LLMError(f"Failed to get next action from LLM: {e}", "LLM_ACTION_ERROR") from e
