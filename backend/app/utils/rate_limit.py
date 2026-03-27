"""Rate limiting utilities for API endpoints."""

import time
from typing import Dict, Optional
from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class RateLimitInfo:
    """Information about rate limit state."""

    requests: list = field(default_factory=list)
    window_seconds: int = 300  # 5 minutes default
    max_requests: int = 5


class InMemoryRateLimiter:
    """Simple in-memory rate limiter for development/testing."""

    def __init__(self):
        self._storage: Dict[str, RateLimitInfo] = defaultdict(lambda: RateLimitInfo())

    def is_allowed(
        self, key: str, max_requests: int = 5, window_seconds: int = 300
    ) -> tuple[bool, Optional[int]]:
        """
        Check if request is allowed under rate limit.

        Args:
            key: Unique identifier for the rate limit (e.g., IP address, user ID)
            max_requests: Maximum number of requests allowed in the window
            window_seconds: Time window in seconds

        Returns:
            Tuple of (is_allowed, retry_after_seconds)
        """
        current_time = time.time()
        rate_limit = self._storage[key]

        # Update rate limit config if different
        rate_limit.max_requests = max_requests
        rate_limit.window_seconds = window_seconds

        # Remove old requests outside the window
        cutoff_time = current_time - window_seconds
        rate_limit.requests = [
            req_time for req_time in rate_limit.requests if req_time > cutoff_time
        ]

        # Check if under limit
        if len(rate_limit.requests) < max_requests:
            rate_limit.requests.append(current_time)
            return True, None

        # Calculate retry after time
        oldest_request = min(rate_limit.requests)
        retry_after = int(oldest_request + window_seconds - current_time) + 1

        return False, retry_after

    def reset(self, key: str) -> None:
        """Reset rate limit for a key."""
        if key in self._storage:
            del self._storage[key]


# Global rate limiter instance
rate_limiter = InMemoryRateLimiter()


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""

    def __init__(self, message: str, retry_after: int):
        self.message = message
        self.retry_after = retry_after
        super().__init__(message)
