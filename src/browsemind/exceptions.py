"""Custom exception types for the BrowseMind application."""


class BrowseMindError(Exception):
    """Base exception for all application-specific errors."""

    def __init__(self, message: str, error_code: str | None = None):
        super().__init__(message)
        self.error_code = error_code


class ConfigurationError(BrowseMindError):
    """Raised for configuration-related errors."""

    def __init__(self, message: str, error_code: str = "CONFIG_ERROR"):
        super().__init__(message, error_code)


class BrowserError(BrowseMindError):
    """Raised for browser-related errors, such as creation or interaction failures."""

    def __init__(self, message: str, error_code: str = "BROWSER_ERROR"):
        super().__init__(message, error_code)


class LLMError(BrowseMindError):
    """Raised for errors related to the Language Model."""

    def __init__(self, message: str, error_code: str = "LLM_ERROR"):
        super().__init__(message, error_code)
