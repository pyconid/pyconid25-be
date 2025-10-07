import asyncio
import time
from collections import defaultdict
from typing import Dict, List, Optional


class InMemoryRateLimiter:
    """In-memory rate limiter using sliding window algorithm"""

    def __init__(self):
        self._requests: Dict[str, List[float]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def is_allowed(
        self, key: str, limit: int, window: int
    ) -> tuple[bool, Optional[int]]:
        """
        Check if request is allowed using sliding window algorithm

        Args:
            key: Unique identifier for the rate limit
            limit: Maximum number of requests allowed
            window: Time window in seconds

        Returns:
            Tuple of (is_allowed, retry_after_seconds)
        """
        async with self._lock:
            current_time = time.time()
            cutoff_time = current_time - window

            # Remove expired timestamps
            self._requests[key] = [ts for ts in self._requests[key] if ts > cutoff_time]

            # Check if under limit
            if len(self._requests[key]) < limit:
                self._requests[key].append(current_time)
                return True, None

            # Calculate retry_after
            oldest_request = min(self._requests[key])
            retry_after = window - (current_time - oldest_request)

            return False, max(0, retry_after)

    async def reset(self, key: str) -> None:
        """Reset rate limit for a key"""
        async with self._lock:
            if key in self._requests:
                del self._requests[key]

    async def get_remaining(self, key: str, limit: int) -> int:
        """Get remaining requests for a key"""
        async with self._lock:
            current_count = len(self._requests.get(key, []))
            return max(0, limit - current_count)

    async def cleanup_expired(self, window: int) -> None:
        """
        Cleanup expired entries to prevent memory bloat
        Should be called periodically by a background task
        """
        async with self._lock:
            current_time = time.time()
            cutoff_time = current_time - window

            keys_to_delete = []
            for key, timestamps in self._requests.items():
                # Filter out expired timestamps
                valid_timestamps = [ts for ts in timestamps if ts > cutoff_time]
                if valid_timestamps:
                    self._requests[key] = valid_timestamps
                else:
                    keys_to_delete.append(key)

            # Remove empty keys
            for key in keys_to_delete:
                del self._requests[key]
