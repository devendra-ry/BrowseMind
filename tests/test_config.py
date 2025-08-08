"""Tests for the configuration module."""

import os
from unittest.mock import patch

import pytest

from browsemind.config import AgentConfig
from browsemind.exceptions import ConfigurationError


class TestAgentConfig:
    """Test cases for the AgentConfig class."""

    def test_default_values(self) -> None:
        """Test that default values are correctly set."""
        config = AgentConfig()
        assert config.model_name == "gemini-1.5-flash"
        assert config.temperature == 0.7
        assert config.default_timeout == 120
        assert config.max_iterations == 20
        assert config.google_api_key == ""

    @patch.dict(
        os.environ,
        {
            "GOOGLE_API_KEY": "test-key",
            "MODEL_NAME": "test-model",
            "TEMPERATURE": "0.5",
            "DEFAULT_TIMEOUT": "60",
            "MAX_ITERATIONS": "10",
        },
    )
    def test_from_env_with_all_vars(self) -> None:
        """Test loading config from environment variables."""
        config = AgentConfig.from_env()
        assert config.google_api_key == "test-key"
        assert config.model_name == "test-model"
        assert config.temperature == 0.5
        assert config.default_timeout == 60
        assert config.max_iterations == 10

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"}, clear=True)
    def test_from_env_with_required_only(self) -> None:
        """Test loading config with only required environment variable."""
        config = AgentConfig.from_env()
        assert config.google_api_key == "test-key"
        # Should use defaults for other values
        assert config.model_name == "gemini-1.5-flash"
        assert config.temperature == 0.7
        assert config.default_timeout == 120
        assert config.max_iterations == 20

    @patch.dict(os.environ, {}, clear=True)
    def test_from_env_missing_api_key(self) -> None:
        """Test that missing API key raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            AgentConfig.from_env()
        assert exc_info.value.error_code == "MISSING_API_KEY"

    @patch.dict(
        os.environ, {"GOOGLE_API_KEY": "test-key", "TEMPERATURE": "1.5"}  # Invalid temperature
    )
    def test_from_env_invalid_temperature(self) -> None:
        """Test that invalid temperature raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            AgentConfig.from_env()
        assert exc_info.value.error_code == "INVALID_TEMPERATURE"

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key", "TEMPERATURE": "not-a-number"})
    def test_from_env_invalid_temperature_format(self) -> None:
        """Test that invalid temperature format raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            AgentConfig.from_env()
        assert exc_info.value.error_code == "INVALID_TEMPERATURE_FORMAT"

    @patch.dict(
        os.environ, {"GOOGLE_API_KEY": "test-key", "DEFAULT_TIMEOUT": "-1"}  # Invalid timeout
    )
    def test_from_env_invalid_timeout(self) -> None:
        """Test that invalid timeout raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            AgentConfig.from_env()
        assert exc_info.value.error_code == "INVALID_TIMEOUT"

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key", "DEFAULT_TIMEOUT": "not-a-number"})
    def test_from_env_invalid_timeout_format(self) -> None:
        """Test that invalid timeout format raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            AgentConfig.from_env()
        assert exc_info.value.error_code == "INVALID_TIMEOUT_FORMAT"

    @patch.dict(
        os.environ, {"GOOGLE_API_KEY": "test-key", "MAX_ITERATIONS": "0"}  # Invalid iterations
    )
    def test_from_env_invalid_iterations(self) -> None:
        """Test that invalid iterations raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            AgentConfig.from_env()
        assert exc_info.value.error_code == "INVALID_ITERATIONS"

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key", "MAX_ITERATIONS": "not-a-number"})
    def test_from_env_invalid_iterations_format(self) -> None:
        """Test that invalid iterations format raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            AgentConfig.from_env()
        assert exc_info.value.error_code == "INVALID_ITERATIONS_FORMAT"
