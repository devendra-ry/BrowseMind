"""BrowseMind - AI-powered browser automation agent using Google's Gemini."""

__version__ = "0.2.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

# Export key modules for easier imports
from .agent import Agent
from .config import AgentConfig
from .exceptions import BrowseMindError, BrowserError, ConfigurationError, LLMError
from .reliability import CircuitBreaker, RateLimiter, retry_with_backoff, timeout_wrapper

__all__ = [
    "Agent",
    "AgentConfig",
    "BrowseMindError",
    "ConfigurationError",
    "BrowserError",
    "LLMError",
    "RateLimiter",
    "CircuitBreaker",
    "retry_with_backoff",
    "timeout_wrapper",
]
