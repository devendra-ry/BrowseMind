"""Custom exception types for the BrowseMind application."""


class BrowseMindError(Exception):
    """Base exception for all application-specific errors."""


class ConfigurationError(BrowseMindError):
    """Raised for configuration-related errors."""


class BrowserError(BrowseMindError):
    """Raised for browser-related errors, such as creation or interaction failures."""


class LLMError(BrowseMindError):
    """Raised for errors related to the Language Model."""
