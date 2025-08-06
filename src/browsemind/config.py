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
            ConfigurationError: If the required GOOGLE_API_KEY is not set.
        """
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            raise ConfigurationError("Missing required environment variable: GOOGLE_API_KEY")

        return cls(
            model_name=os.getenv("MODEL_NAME", "gemini-1.5-flash"),
            temperature=float(os.getenv("TEMPERATURE", 0.7)),
            default_timeout=int(os.getenv("DEFAULT_TIMEOUT", 120)),
            max_iterations=int(os.getenv("MAX_ITERATIONS", 20)),
            google_api_key=google_api_key,
        )
