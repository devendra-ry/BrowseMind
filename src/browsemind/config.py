"""Configuration management for the BrowseMind agent."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

from browsemind.exceptions import ConfigurationError

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
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            raise ConfigurationError(
                "Missing required environment variable: GOOGLE_API_KEY", "MISSING_API_KEY"
            )

        # Get optional environment variables with defaults
        model_name = os.getenv("MODEL_NAME", "gemini-1.5-flash")

        # Parse temperature with validation
        try:
            temperature_str = os.getenv("TEMPERATURE", "0.7")
            temperature = float(temperature_str)
            if not (0.0 <= temperature <= 1.0):
                raise ConfigurationError(
                    f"Temperature must be between 0.0 and 1.0, got: {temperature}",
                    "INVALID_TEMPERATURE",
                )
        except ValueError as e:
            raise ConfigurationError(
                f"Failed to parse TEMPERATURE as float: {temperature_str}",
                "INVALID_TEMPERATURE_FORMAT",
            ) from e

        # Parse default_timeout with validation
        try:
            default_timeout_str = os.getenv("DEFAULT_TIMEOUT", "120")
            default_timeout = int(default_timeout_str)
            if default_timeout <= 0:
                raise ConfigurationError(
                    f"DEFAULT_TIMEOUT must be positive, got: {default_timeout}", "INVALID_TIMEOUT"
                )
        except ValueError as e:
            raise ConfigurationError(
                f"Failed to parse DEFAULT_TIMEOUT as int: {default_timeout_str}",
                "INVALID_TIMEOUT_FORMAT",
            ) from e

        # Parse max_iterations with validation
        try:
            max_iterations_str = os.getenv("MAX_ITERATIONS", "20")
            max_iterations = int(max_iterations_str)
            if max_iterations <= 0:
                raise ConfigurationError(
                    f"MAX_ITERATIONS must be positive, got: {max_iterations}", "INVALID_ITERATIONS"
                )
        except ValueError as e:
            raise ConfigurationError(
                f"Failed to parse MAX_ITERATIONS as int: {max_iterations_str}",
                "INVALID_ITERATIONS_FORMAT",
            ) from e

        return cls(
            model_name=model_name,
            temperature=temperature,
            default_timeout=default_timeout,
            max_iterations=max_iterations,
            google_api_key=google_api_key,
        )
