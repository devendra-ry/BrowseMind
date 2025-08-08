"""Tests for the reliability module."""

import asyncio
import time

import pytest

from browsemind.exceptions import LLMError
from browsemind.reliability import CircuitBreaker, RateLimiter, retry_with_backoff, timeout_wrapper


class TestRateLimiter:
    """Test cases for the RateLimiter class."""

    def test_rate_limiter_initialization(self) -> None:
        """Test RateLimiter initialization."""
        limiter = RateLimiter(max_requests=10, time_window=60.0)
        assert limiter.max_requests == 10
        assert limiter.time_window == 60.0

    @pytest.mark.asyncio
    async def test_rate_limiter_allows_requests_within_limit(self) -> None:
        """Test that requests within the limit are allowed immediately."""
        limiter = RateLimiter(max_requests=5, time_window=1.0)

        # Should allow 5 requests immediately
        start_time = time.time()
        for _ in range(5):
            await limiter.acquire()
        end_time = time.time()

        # Should take very little time (much less than 1 second)
        assert end_time - start_time < 0.1

    @pytest.mark.asyncio
    async def test_rate_limiter_delays_when_limit_exceeded(self) -> None:
        """Test that requests exceeding the limit are delayed."""
        limiter = RateLimiter(max_requests=2, time_window=0.1)  # 2 requests per 0.1 seconds

        # First 2 requests should be immediate
        start_time = time.time()
        await limiter.acquire()
        await limiter.acquire()
        mid_time = time.time()

        # Third request should be delayed
        await limiter.acquire()
        end_time = time.time()

        # First two should be immediate
        assert mid_time - start_time < 0.05

        # Third should be delayed (but not necessarily the full window)
        # It might be slightly less due to timing, so we check it's delayed somewhat
        assert end_time - mid_time > 0.01


class TestCircuitBreaker:
    """Test cases for the CircuitBreaker class."""

    def test_circuit_breaker_initialization(self) -> None:
        """Test CircuitBreaker initialization."""
        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30.0)
        assert breaker.failure_threshold == 3
        assert breaker.recovery_timeout == 30.0
        assert breaker.failure_count == 0
        assert breaker.state == "CLOSED"

    def test_circuit_breaker_allows_execution_when_closed(self) -> None:
        """Test that requests are allowed when circuit is closed."""
        breaker = CircuitBreaker()
        assert breaker.can_execute() is True

    def test_circuit_breaker_opens_after_failures(self) -> None:
        """Test that circuit opens after threshold failures."""
        breaker = CircuitBreaker(failure_threshold=2)

        # Record failures
        breaker.on_failure()
        assert breaker.state == "CLOSED"  # Not yet open
        assert breaker.can_execute() is True

        breaker.on_failure()
        assert breaker.state == "OPEN"  # Now open
        assert breaker.can_execute() is False

    def test_circuit_breaker_closes_after_success(self) -> None:
        """Test that circuit closes after success."""
        breaker = CircuitBreaker(failure_threshold=2)

        # Open the circuit
        breaker.on_failure()
        breaker.on_failure()
        assert breaker.state == "OPEN"

        # Success should close it
        breaker.on_success()
        assert breaker.state == "CLOSED"
        assert breaker.failure_count == 0


class TestRetryWithBackoff:
    """Test cases for the retry_with_backoff function."""

    @pytest.mark.asyncio
    async def test_retry_with_backoff_success(self) -> None:
        """Test that successful functions return immediately."""

        async def successful_func() -> str:
            return "success"

        result = await retry_with_backoff(successful_func, max_retries=3)
        assert result == "success"

    @pytest.mark.asyncio
    async def test_retry_with_backoff_eventual_success(self) -> None:
        """Test that functions eventually succeed after retries."""
        attempt_count = 0

        async def sometimes_failing_func() -> str:
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise Exception("Temporary failure")
            return "success"

        result = await retry_with_backoff(sometimes_failing_func, max_retries=5)
        assert result == "success"
        assert attempt_count == 3

    @pytest.mark.asyncio
    async def test_retry_with_backoff_exhausts_retries(self) -> None:
        """Test that functions fail after exhausting retries."""

        async def always_failing_func() -> None:
            raise Exception("Permanent failure")

        with pytest.raises(LLMError) as exc_info:
            await retry_with_backoff(always_failing_func, max_retries=2)

        assert exc_info.value.error_code == "RETRY_EXHAUSTED"


class TestTimeoutWrapper:
    """Test cases for the timeout_wrapper function."""

    @pytest.mark.asyncio
    async def test_timeout_wrapper_success(self) -> None:
        """Test that fast functions complete successfully."""

        async def fast_func() -> str:
            return "success"

        result = await timeout_wrapper(fast_func, timeout=1.0)
        assert result == "success"

    @pytest.mark.asyncio
    async def test_timeout_wrapper_timeout(self) -> None:
        """Test that slow functions timeout."""

        async def slow_func() -> None:
            await asyncio.sleep(0.1)
            # No return value expected

        with pytest.raises(LLMError) as exc_info:
            await timeout_wrapper(slow_func, timeout=0.01)  # 10ms timeout for 100ms function

        assert exc_info.value.error_code == "TIMEOUT_ERROR"
