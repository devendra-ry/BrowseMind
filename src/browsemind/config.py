"""Configuration management for the BrowseMind agent."""

import logging
import os
from dataclasses import dataclass

from dotenv import load_dotenv

from browsemind.exceptions import ConfigurationError

logger = logging.getLogger(__name__)

# Load environment variables from a .env file if it exists
load_dotenv()


@dataclass
class AgentConfig:
    """
    Data class for storing agent and browser configuration.
    Provides a centralized and type-safe way to manage settings.
    """

    model_name: str = "gemini-1.5-flash"
    temperature: float = 0.7
    default_timeout: int = 120
    max_iterations: int = 20
    google_api_key: str = ""

    # Rate limiting and retry configuration
    llm_max_retries: int = 3
    llm_retry_delay: float = 1.0  # seconds
    llm_rate_limit_requests_per_minute: int = 60

    # Timeout configuration
    llm_request_timeout: int = 300  # seconds
    browser_navigation_timeout: int = 30000  # milliseconds
    browser_action_timeout: int = 30000  # milliseconds

    # Security configuration
    max_page_content_length: int = 1000000  # 1MB limit
    max_task_length: int = 1000  # characters

    @classmethod
    def from_env(cls) -> "AgentConfig":
        """
        Creates an AgentConfig instance by loading values from environment variables.
        Falls back to default values if environment variables are not set.

        Returns:
            An instance of AgentConfig.

        Raises:
            ConfigurationError: If the required GOOGLE_API_KEY is not set or if
                any environment variables have invalid values.
        """
        logger.info("Loading configuration from environment variables")

        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            logger.error("Missing required environment variable: GOOGLE_API_KEY")
            raise ConfigurationError(
                "Missing required environment variable: GOOGLE_API_KEY", "MISSING_API_KEY"
            )

        # Get optional environment variables with defaults
        model_name = os.getenv("MODEL_NAME", "gemini-1.5-flash")
        logger.info(f"Using model: {model_name}")

        # Parse temperature with validation
        try:
            temperature_str = os.getenv("TEMPERATURE", "0.7")
            temperature = float(temperature_str)
            if not (0.0 <= temperature <= 1.0):
                logger.error(f"Temperature must be between 0.0 and 1.0, got: {temperature}")
                raise ConfigurationError(
                    f"Temperature must be between 0.0 and 1.0, got: {temperature}",
                    "INVALID_TEMPERATURE",
                )
            logger.info(f"Using temperature: {temperature}")
        except ValueError as e:
            logger.error(f"Failed to parse TEMPERATURE as float: {temperature_str}")
            raise ConfigurationError(
                f"Failed to parse TEMPERATURE as float: {temperature_str}",
                "INVALID_TEMPERATURE_FORMAT",
            ) from e

        # Parse default_timeout with validation
        try:
            default_timeout_str = os.getenv("DEFAULT_TIMEOUT", "120")
            default_timeout = int(default_timeout_str)
            if default_timeout <= 0:
                logger.error(f"DEFAULT_TIMEOUT must be positive, got: {default_timeout}")
                raise ConfigurationError(
                    f"DEFAULT_TIMEOUT must be positive, got: {default_timeout}", "INVALID_TIMEOUT"
                )
            logger.info(f"Using default timeout: {default_timeout}")
        except ValueError as e:
            logger.error(f"Failed to parse DEFAULT_TIMEOUT as int: {default_timeout_str}")
            raise ConfigurationError(
                f"Failed to parse DEFAULT_TIMEOUT as int: {default_timeout_str}",
                "INVALID_TIMEOUT_FORMAT",
            ) from e

        # Parse max_iterations with validation
        try:
            max_iterations_str = os.getenv("MAX_ITERATIONS", "20")
            max_iterations = int(max_iterations_str)
            if max_iterations <= 0:
                logger.error(f"MAX_ITERATIONS must be positive, got: {max_iterations}")
                raise ConfigurationError(
                    f"MAX_ITERATIONS must be positive, got: {max_iterations}", "INVALID_ITERATIONS"
                )
            logger.info(f"Using max iterations: {max_iterations}")
        except ValueError as e:
            logger.error(f"Failed to parse MAX_ITERATIONS as int: {max_iterations_str}")
            raise ConfigurationError(
                f"Failed to parse MAX_ITERATIONS as int: {max_iterations_str}",
                "INVALID_ITERATIONS_FORMAT",
            ) from e

        # Parse LLM retry configuration
        try:
            llm_max_retries_str = os.getenv("LLM_MAX_RETRIES", "3")
            llm_max_retries = int(llm_max_retries_str)
            if llm_max_retries < 0:
                logger.error(f"LLM_MAX_RETRIES must be non-negative, got: {llm_max_retries}")
                raise ConfigurationError(
                    f"LLM_MAX_RETRIES must be non-negative, got: {llm_max_retries}",
                    "INVALID_LLM_MAX_RETRIES",
                )
            logger.info(f"Using LLM max retries: {llm_max_retries}")
        except ValueError as e:
            logger.error(f"Failed to parse LLM_MAX_RETRIES as int: {llm_max_retries_str}")
            raise ConfigurationError(
                f"Failed to parse LLM_MAX_RETRIES as int: {llm_max_retries_str}",
                "INVALID_LLM_MAX_RETRIES_FORMAT",
            ) from e

        try:
            llm_retry_delay_str = os.getenv("LLM_RETRY_DELAY", "1.0")
            llm_retry_delay = float(llm_retry_delay_str)
            if llm_retry_delay < 0:
                logger.error(f"LLM_RETRY_DELAY must be non-negative, got: {llm_retry_delay}")
                raise ConfigurationError(
                    f"LLM_RETRY_DELAY must be non-negative, got: {llm_retry_delay}",
                    "INVALID_LLM_RETRY_DELAY",
                )
            logger.info(f"Using LLM retry delay: {llm_retry_delay}")
        except ValueError as e:
            logger.error(f"Failed to parse LLM_RETRY_DELAY as float: {llm_retry_delay_str}")
            raise ConfigurationError(
                f"Failed to parse LLM_RETRY_DELAY as float: {llm_retry_delay_str}",
                "INVALID_LLM_RETRY_DELAY_FORMAT",
            ) from e

        try:
            llm_rate_limit_rpm_str = os.getenv("LLM_RATE_LIMIT_REQUESTS_PER_MINUTE", "60")
            llm_rate_limit_requests_per_minute = int(llm_rate_limit_rpm_str)
            if llm_rate_limit_requests_per_minute <= 0:
                logger.error(
                    f"LLM_RATE_LIMIT_REQUESTS_PER_MINUTE must be positive, got: {llm_rate_limit_requests_per_minute}"
                )
                raise ConfigurationError(
                    f"LLM_RATE_LIMIT_REQUESTS_PER_MINUTE must be positive, got: {llm_rate_limit_requests_per_minute}",
                    "INVALID_LLM_RATE_LIMIT",
                )
            logger.info(
                f"Using LLM rate limit: {llm_rate_limit_requests_per_minute} requests/minute"
            )
        except ValueError as e:
            logger.error(
                f"Failed to parse LLM_RATE_LIMIT_REQUESTS_PER_MINUTE as int: {llm_rate_limit_rpm_str}"
            )
            raise ConfigurationError(
                f"Failed to parse LLM_RATE_LIMIT_REQUESTS_PER_MINUTE as int: {llm_rate_limit_rpm_str}",
                "INVALID_LLM_RATE_LIMIT_FORMAT",
            ) from e

        # Parse timeout configuration
        try:
            llm_request_timeout_str = os.getenv("LLM_REQUEST_TIMEOUT", "300")
            llm_request_timeout = int(llm_request_timeout_str)
            if llm_request_timeout <= 0:
                logger.error(f"LLM_REQUEST_TIMEOUT must be positive, got: {llm_request_timeout}")
                raise ConfigurationError(
                    f"LLM_REQUEST_TIMEOUT must be positive, got: {llm_request_timeout}",
                    "INVALID_LLM_REQUEST_TIMEOUT",
                )
            logger.info(f"Using LLM request timeout: {llm_request_timeout} seconds")
        except ValueError as e:
            logger.error(f"Failed to parse LLM_REQUEST_TIMEOUT as int: {llm_request_timeout_str}")
            raise ConfigurationError(
                f"Failed to parse LLM_REQUEST_TIMEOUT as int: {llm_request_timeout_str}",
                "INVALID_LLM_REQUEST_TIMEOUT_FORMAT",
            ) from e

        try:
            browser_navigation_timeout_str = os.getenv("BROWSER_NAVIGATION_TIMEOUT", "30000")
            browser_navigation_timeout = int(browser_navigation_timeout_str)
            if browser_navigation_timeout <= 0:
                logger.error(
                    f"BROWSER_NAVIGATION_TIMEOUT must be positive, got: {browser_navigation_timeout}"
                )
                raise ConfigurationError(
                    f"BROWSER_NAVIGATION_TIMEOUT must be positive, got: {browser_navigation_timeout}",
                    "INVALID_BROWSER_NAVIGATION_TIMEOUT",
                )
            logger.info(
                f"Using browser navigation timeout: {browser_navigation_timeout} milliseconds"
            )
        except ValueError as e:
            logger.error(
                f"Failed to parse BROWSER_NAVIGATION_TIMEOUT as int: {browser_navigation_timeout_str}"
            )
            raise ConfigurationError(
                f"Failed to parse BROWSER_NAVIGATION_TIMEOUT as int: {browser_navigation_timeout_str}",
                "INVALID_BROWSER_NAVIGATION_TIMEOUT_FORMAT",
            ) from e

        try:
            browser_action_timeout_str = os.getenv("BROWSER_ACTION_TIMEOUT", "30000")
            browser_action_timeout = int(browser_action_timeout_str)
            if browser_action_timeout <= 0:
                logger.error(
                    f"BROWSER_ACTION_TIMEOUT must be positive, got: {browser_action_timeout}"
                )
                raise ConfigurationError(
                    f"BROWSER_ACTION_TIMEOUT must be positive, got: {browser_action_timeout}",
                    "INVALID_BROWSER_ACTION_TIMEOUT",
                )
            logger.info(f"Using browser action timeout: {browser_action_timeout} milliseconds")
        except ValueError as e:
            logger.error(
                f"Failed to parse BROWSER_ACTION_TIMEOUT as int: {browser_action_timeout_str}"
            )
            raise ConfigurationError(
                f"Failed to parse BROWSER_ACTION_TIMEOUT as int: {browser_action_timeout_str}",
                "INVALID_BROWSER_ACTION_TIMEOUT_FORMAT",
            ) from e

        # Parse security configuration
        try:
            max_page_content_length_str = os.getenv("MAX_PAGE_CONTENT_LENGTH", "1000000")
            max_page_content_length = int(max_page_content_length_str)
            if max_page_content_length <= 0:
                logger.error(
                    f"MAX_PAGE_CONTENT_LENGTH must be positive, got: {max_page_content_length}"
                )
                raise ConfigurationError(
                    f"MAX_PAGE_CONTENT_LENGTH must be positive, got: {max_page_content_length}",
                    "INVALID_MAX_PAGE_CONTENT_LENGTH",
                )
            logger.info(f"Using max page content length: {max_page_content_length} bytes")
        except ValueError as e:
            logger.error(
                f"Failed to parse MAX_PAGE_CONTENT_LENGTH as int: {max_page_content_length_str}"
            )
            raise ConfigurationError(
                f"Failed to parse MAX_PAGE_CONTENT_LENGTH as int: {max_page_content_length_str}",
                "INVALID_MAX_PAGE_CONTENT_LENGTH_FORMAT",
            ) from e

        try:
            max_task_length_str = os.getenv("MAX_TASK_LENGTH", "1000")
            max_task_length = int(max_task_length_str)
            if max_task_length <= 0:
                logger.error(f"MAX_TASK_LENGTH must be positive, got: {max_task_length}")
                raise ConfigurationError(
                    f"MAX_TASK_LENGTH must be positive, got: {max_task_length}",
                    "INVALID_MAX_TASK_LENGTH",
                )
            logger.info(f"Using max task length: {max_task_length} characters")
        except ValueError as e:
            logger.error(f"Failed to parse MAX_TASK_LENGTH as int: {max_task_length_str}")
            raise ConfigurationError(
                f"Failed to parse MAX_TASK_LENGTH as int: {max_task_length_str}",
                "INVALID_MAX_TASK_LENGTH_FORMAT",
            ) from e

        config = cls(
            model_name=model_name,
            temperature=temperature,
            default_timeout=default_timeout,
            max_iterations=max_iterations,
            google_api_key=google_api_key,
            llm_max_retries=llm_max_retries,
            llm_retry_delay=llm_retry_delay,
            llm_rate_limit_requests_per_minute=llm_rate_limit_requests_per_minute,
            llm_request_timeout=llm_request_timeout,
            browser_navigation_timeout=browser_navigation_timeout,
            browser_action_timeout=browser_action_timeout,
            max_page_content_length=max_page_content_length,
            max_task_length=max_task_length,
        )
        logger.info("Configuration loaded successfully")
        return config
