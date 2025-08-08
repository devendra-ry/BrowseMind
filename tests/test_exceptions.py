"""Tests for the exceptions module."""

from browsemind.exceptions import BrowseMindError, BrowserError, ConfigurationError, LLMError


class TestExceptions:
    """Test cases for custom exceptions."""

    def test_browse_mind_error(self) -> None:
        """Test BrowseMindError creation and attributes."""
        error = BrowseMindError("Test error message")
        assert str(error) == "Test error message"
        assert error.error_code is None

        error_with_code = BrowseMindError("Test error message", "TEST_ERROR")
        assert str(error_with_code) == "Test error message"
        assert error_with_code.error_code == "TEST_ERROR"

    def test_configuration_error(self) -> None:
        """Test ConfigurationError creation and attributes."""
        error = ConfigurationError("Test config error")
        assert str(error) == "Test config error"
        assert error.error_code == "CONFIG_ERROR"

        error_with_code = ConfigurationError("Test config error", "CUSTOM_CONFIG_ERROR")
        assert str(error_with_code) == "Test config error"
        assert error_with_code.error_code == "CUSTOM_CONFIG_ERROR"

    def test_browser_error(self) -> None:
        """Test BrowserError creation and attributes."""
        error = BrowserError("Test browser error")
        assert str(error) == "Test browser error"
        assert error.error_code == "BROWSER_ERROR"

        error_with_code = BrowserError("Test browser error", "CUSTOM_BROWSER_ERROR")
        assert str(error_with_code) == "Test browser error"
        assert error_with_code.error_code == "CUSTOM_BROWSER_ERROR"

    def test_llm_error(self) -> None:
        """Test LLMError creation and attributes."""
        error = LLMError("Test LLM error")
        assert str(error) == "Test LLM error"
        assert error.error_code == "LLM_ERROR"

        error_with_code = LLMError("Test LLM error", "CUSTOM_LLM_ERROR")
        assert str(error_with_code) == "Test LLM error"
        assert error_with_code.error_code == "CUSTOM_LLM_ERROR"
