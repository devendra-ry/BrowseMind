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

        # Reliability defaults
        assert config.llm_max_retries == 3
        assert config.llm_retry_delay == 1.0
        assert config.llm_rate_limit_requests_per_minute == 60
        assert config.llm_request_timeout == 300
        assert config.browser_navigation_timeout == 30000
        assert config.browser_action_timeout == 30000
        assert config.max_page_content_length == 1000000
        assert config.max_task_length == 1000

    @patch.dict(
        os.environ,
        {
            "GOOGLE_API_KEY": "test-key",
            "MODEL_NAME": "test-model",
            "TEMPERATURE": "0.5",
            "DEFAULT_TIMEOUT": "60",
            "MAX_ITERATIONS": "10",
            "LLM_MAX_RETRIES": "5",
            "LLM_RETRY_DELAY": "2.0",
            "LLM_RATE_LIMIT_REQUESTS_PER_MINUTE": "30",
            "LLM_REQUEST_TIMEOUT": "120",
            "BROWSER_NAVIGATION_TIMEOUT": "15000",
            "BROWSER_ACTION_TIMEOUT": "15000",
            "MAX_PAGE_CONTENT_LENGTH": "500000",
            "MAX_TASK_LENGTH": "500",
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

        # Reliability settings
        assert config.llm_max_retries == 5
        assert config.llm_retry_delay == 2.0
        assert config.llm_rate_limit_requests_per_minute == 30
        assert config.llm_request_timeout == 120
        assert config.browser_navigation_timeout == 15000
        assert config.browser_action_timeout == 15000
        assert config.max_page_content_length == 500000
        assert config.max_task_length == 500

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

        # Reliability defaults
        assert config.llm_max_retries == 3
        assert config.llm_retry_delay == 1.0
        assert config.llm_rate_limit_requests_per_minute == 60
        assert config.llm_request_timeout == 300
        assert config.browser_navigation_timeout == 30000
        assert config.browser_action_timeout == 30000
        assert config.max_page_content_length == 1000000
        assert config.max_task_length == 1000

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

    @patch.dict(
        os.environ, {"GOOGLE_API_KEY": "test-key", "LLM_MAX_RETRIES": "-1"}  # Invalid retries
    )
    def test_from_env_invalid_llm_max_retries(self) -> None:
        """Test that invalid LLM max retries raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            AgentConfig.from_env()
        assert exc_info.value.error_code == "INVALID_LLM_MAX_RETRIES"

    @patch.dict(
        os.environ, {"GOOGLE_API_KEY": "test-key", "LLM_RETRY_DELAY": "-1"}  # Invalid retry delay
    )
    def test_from_env_invalid_llm_retry_delay(self) -> None:
        """Test that invalid LLM retry delay raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            AgentConfig.from_env()
        assert exc_info.value.error_code == "INVALID_LLM_RETRY_DELAY"

    @patch.dict(
        os.environ,
        {
            "GOOGLE_API_KEY": "test-key",
            "LLM_RATE_LIMIT_REQUESTS_PER_MINUTE": "0",  # Invalid rate limit
        },
    )
    def test_from_env_invalid_llm_rate_limit(self) -> None:
        """Test that invalid LLM rate limit raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            AgentConfig.from_env()
        assert exc_info.value.error_code == "INVALID_LLM_RATE_LIMIT"

    @patch.dict(
        os.environ,
        {"GOOGLE_API_KEY": "test-key", "LLM_REQUEST_TIMEOUT": "0"},  # Invalid request timeout
    )
    def test_from_env_invalid_llm_request_timeout(self) -> None:
        """Test that invalid LLM request timeout raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            AgentConfig.from_env()
        assert exc_info.value.error_code == "INVALID_LLM_REQUEST_TIMEOUT"

    @patch.dict(
        os.environ,
        {
            "GOOGLE_API_KEY": "test-key",
            "BROWSER_NAVIGATION_TIMEOUT": "0",  # Invalid navigation timeout
        },
    )
    def test_from_env_invalid_browser_navigation_timeout(self) -> None:
        """Test that invalid browser navigation timeout raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            AgentConfig.from_env()
        assert exc_info.value.error_code == "INVALID_BROWSER_NAVIGATION_TIMEOUT"

    @patch.dict(
        os.environ,
        {"GOOGLE_API_KEY": "test-key", "BROWSER_ACTION_TIMEOUT": "0"},  # Invalid action timeout
    )
    def test_from_env_invalid_browser_action_timeout(self) -> None:
        """Test that invalid browser action timeout raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            AgentConfig.from_env()
        assert exc_info.value.error_code == "INVALID_BROWSER_ACTION_TIMEOUT"

    @patch.dict(
        os.environ,
        {"GOOGLE_API_KEY": "test-key", "MAX_PAGE_CONTENT_LENGTH": "0"},  # Invalid content length
    )
    def test_from_env_invalid_max_page_content_length(self) -> None:
        """Test that invalid max page content length raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            AgentConfig.from_env()
        assert exc_info.value.error_code == "INVALID_MAX_PAGE_CONTENT_LENGTH"

    @patch.dict(
        os.environ, {"GOOGLE_API_KEY": "test-key", "MAX_TASK_LENGTH": "0"}  # Invalid task length
    )
    def test_from_env_invalid_max_task_length(self) -> None:
        """Test that invalid max task length raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            AgentConfig.from_env()
        assert exc_info.value.error_code == "INVALID_MAX_TASK_LENGTH"
