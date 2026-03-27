"""Simple in-memory cache for wallet data."""

import time
from typing import Any, Dict, Optional
from threading import Lock


class WalletCache:
    """Simple thread-safe cache for wallet data."""

    def __init__(self, ttl_seconds: int = 30):
        self._cache: Dict[int, Dict[str, Any]] = {}
        self._timestamps: Dict[int, float] = {}
        self._ttl = ttl_seconds
        self._lock = Lock()

    def get(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get cached wallet data for user."""
        with self._lock:
            if user_id not in self._cache:
                return None

            # Check if expired
            if time.time() - self._timestamps[user_id] > self._ttl:
                del self._cache[user_id]
                del self._timestamps[user_id]
                return None

            return self._cache[user_id].copy()

    def set(self, user_id: int, data: Dict[str, Any]) -> None:
        """Cache wallet data for user."""
        with self._lock:
            self._cache[user_id] = data.copy()
            self._timestamps[user_id] = time.time()

    def invalidate(self, user_id: int) -> None:
        """Remove cached data for user."""
        with self._lock:
            self._cache.pop(user_id, None)
            self._timestamps.pop(user_id, None)

    def clear(self) -> None:
        """Clear all cached data."""
        with self._lock:
            self._cache.clear()
            self._timestamps.clear()


# Global cache instance
wallet_cache = WalletCache(ttl_seconds=30)  # Cache for 30 seconds
