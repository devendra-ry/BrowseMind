import asyncio
import logging
import time
from collections import deque
from collections.abc import Awaitable, Callable
from typing import TypeVar

from browsemind.exceptions import LLMError

logger = logging.getLogger(__name__)

T = TypeVar("T")


class RateLimiter:
    """A simple rate limiter that limits the number of requests per time period."""

    def __init__(self, max_requests: int, time_window: float) -> None:
        """
        Initialize the rate limiter.

        Args:
            max_requests: Maximum number of requests allowed
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: deque[float] = deque()

    async def acquire(self) -> None:
        """Acquire a permit, waiting if necessary."""
        now = time.time()

        # Remove old requests outside the time window
        while self.requests and self.requests[0] <= now - self.time_window:
            self.requests.popleft()

        # If we've hit the limit, wait
        if len(self.requests) >= self.max_requests:
            sleep_time = self.time_window - (now - self.requests[0])
            if sleep_time > 0:
                logger.info(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
                await asyncio.sleep(sleep_time)

        # Record this request
        self.requests.append(now)


class CircuitBreaker:
    """A circuit breaker that prevents cascading failures."""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0) -> None:
        """
        Initialize the circuit breaker.

        Args:
            failure_threshold: Number of failures before opening the circuit
            recovery_timeout: Time in seconds before attempting recovery
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time: float | None = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def can_execute(self) -> bool:
        """Check if a request can be executed."""
        if self.state == "CLOSED":
            return True
        elif self.state == "OPEN":
            # Check if we should try to recover
            if (
                self.last_failure_time
                and time.time() - self.last_failure_time >= self.recovery_timeout
            ):
                self.state = "HALF_OPEN"
                return True
            return False
        elif self.state == "HALF_OPEN":
            return True
        return False

    def on_success(self) -> None:
        """Record a successful request."""
        self.failure_count = 0
        self.state = "CLOSED"
        logger.info("Circuit breaker closed due to successful request")

    def on_failure(self) -> None:
        """Record a failed request."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")

    def is_open(self) -> bool:
        """Check if the circuit breaker is open."""
        return self.state == "OPEN"


async def retry_with_backoff(
    func: Callable[[], Awaitable[T]],
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
) -> T:
    """
    Execute a function with exponential backoff retry logic.

    Args:
        func: The async function to execute
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff
        jitter: Whether to add jitter to delays

    Returns:
        The result of the function call

    Raises:
        The last exception raised by the function after all retries are exhausted
    """
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            return await func()
        except Exception as e:
            last_exception = e
            if attempt == max_retries:
                logger.error(f"Max retries ({max_retries}) exceeded. Last error: {e}")
                raise LLMError(
                    f"Operation failed after {max_retries} retries: {e}", "RETRY_EXHAUSTED"
                ) from e

            # Calculate delay with exponential backoff
            delay = min(base_delay * (exponential_base**attempt), max_delay)

            # Add jitter if requested
            if jitter:
                import random

                delay *= 0.5 + random.random() * 0.5  # 0.5 to 1.0 multiplier

            logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.2f} seconds...")
            await asyncio.sleep(delay)

    # This should never be reached due to the early return/raise above
    if last_exception is not None:
        raise last_exception
    else:
        raise Exception("Retry failed for unknown reasons")


async def timeout_wrapper(func: Callable[[], Awaitable[T]], timeout: float) -> T:
    """
    Execute a function with a timeout.

    Args:
        func: The async function to execute
        timeout: Timeout in seconds

    Returns:
        The result of the function call

    Raises:
        TimeoutError: If the function times out
    """
    try:
        return await asyncio.wait_for(func(), timeout)
    except TimeoutError:
        logger.error(f"Operation timed out after {timeout} seconds")
        raise LLMError(f"Operation timed out after {timeout} seconds", "TIMEOUT_ERROR") from None
