import json
import re
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from browsemind.config import AgentConfig
from browsemind.exceptions import LLMError

SYSTEM_PROMPT = """You are an expert AI browsing agent. Your goal is to perform a task based on the user's request.
You will be given the current page content and a list of interactable elements, each with a unique `browsemind-id`.
Your response must be a JSON object wrapped in a ```json ... ``` code block with the following schema:
{{
    "action": "action_name",
    "args": {{
        "arg_name": "arg_value"
    }}
}}

Available actions:
- navigate(url: str): Navigates to the given URL.
- type(id: int, text: str, press_enter_after: bool): Types text into the element with the specified `browsemind-id`. Set `press_enter_after` to true to submit a form or search.
- click(id: int): Clicks on the element with the specified `browsemind-id`.
- summarize(): Summarizes the current page content.
- finish(result: str): Finishes the task and returns the result.

Based on the current page content and the user's goal, choose the best action to take.
"""


def get_llm(config: AgentConfig) -> ChatGoogleGenerativeAI:
    """
    Initializes and returns the ChatGoogleGenerativeAI instance.
    """
    return ChatGoogleGenerativeAI(
        model=config.model_name,
        temperature=config.temperature,
        google_api_key=config.google_api_key,
    )


async def get_next_action(
    llm: ChatGoogleGenerativeAI, page_content: str, task: str
) -> dict[str, Any]:
    """
    Gets the next action from the LLM based on the current page content and task.

    Args:
        llm: The ChatGoogleGenerativeAI instance.
        page_content: The content of the current web page.
        task: The user's task description.

    Returns:
        A dictionary representing the next action to take.
    """
    try:
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SYSTEM_PROMPT),
                ("human", "Page Content:\n{page_content}\n\nTask: {task}"),
            ]
        )
        chain = prompt | llm
        response = await chain.ainvoke({"page_content": page_content, "task": task})

        content = response.content
        content_str = str(content)

        # Use a regex to find the JSON object within the ```json ... ``` block
        json_match = re.search(r"```json\n(.*?)\n```", content_str, re.DOTALL)
        if not json_match:
            raise LLMError(f"No JSON object found in LLM response. Response was: {content_str}")

        json_string = json_match.group(1)
        result = json.loads(json_string)
        # Ensure we return a dict
        if isinstance(result, dict):
            return result
        else:
            raise LLMError(f"LLM response is not a dictionary: {result}")
    except json.JSONDecodeError as e:
        raise LLMError(
            f"Failed to decode JSON from LLM. Response: {content_str}. Error: {e}"
        ) from e
    except Exception as e:
        raise LLMError(f"Failed to get next action from LLM: {e}") from e
