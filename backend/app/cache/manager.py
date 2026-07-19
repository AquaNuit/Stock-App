"""Two-layer cache: L1 in-process TTL dict (thread-safe) → optional L2 Redis.

Design notes (docs/architecture.md §6):
- L1 always available — guarantees zero-dependency dev/test.
- L2 activates only when ``REDIS_URL`` is set and the client imports/连接s.
- Values are pickled for L2; L1 stores objects directly.
"""

from __future__ import annotations

import pickle
import threading
import time
from typing import Any

from backend.app.core.config import Settings, get_settings
from backend.app.core.logging import get_logger

log = get_logger(__name__)


class _MemoryBackend:
    def __init__(self, max_items: int = 2048):
        self._store: dict[str, tuple[float, Any]] = {}
        self._lock = threading.RLock()
        self._max = max_items

    def get(self, key: str) -> Any | None:
        with self._lock:
            item = self._store.get(key)
            if item is None:
                return None
            expires, value = item
            if expires < time.time():
                self._store.pop(key, None)
                return None
            return value

    def set(self, key: str, value: Any, ttl_s: int) -> None:
        with self._lock:
            if len(self._store) >= self._max:
                # Evict the oldest-expiring 10% (cheap LRU-ish sweep).
                for k, _ in sorted(self._store.items(), key=lambda kv: kv[1][0])[: self._max // 10]:
                    self._store.pop(k, None)
            self._store[key] = (time.time() + ttl_s, value)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()


class CacheManager:
    """Facade with graceful Redis degradation (ADR-0008 pattern)."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self._l1 = _MemoryBackend()
        self._redis = None
        if self.settings.use_redis:
            try:  # pragma: no cover - requires a live Redis
                import redis

                client = redis.Redis.from_url(self.settings.redis_url, socket_timeout=1.5)
                client.ping()
                self._redis = client
                log.info("redis cache enabled")
            except Exception as exc:  # noqa: BLE001
                log.warning("redis unavailable, falling back to memory-only cache: %s", exc)
                self._redis = None

    # -- public API ---------------------------------------------------------
    def get(self, key: str) -> Any | None:
        value = self._l1.get(key)
        if value is not None:
            return value
        if self._redis is not None:
            try:  # pragma: no cover
                blob = self._redis.get(key)
                if blob is not None:
                    value = pickle.loads(blob)
                    self._l1.set(key, value, ttl_s=60)
                    return value
            except Exception as exc:
                log.debug("redis get failed: %s", exc)
        return None

    def set(self, key: str, value: Any, ttl_s: int) -> None:
        self._l1.set(key, value, ttl_s)
        if self._redis is not None:
            try:  # pragma: no cover
                self._redis.setex(key, ttl_s, pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL))
            except Exception as exc:
                log.debug("redis set failed: %s", exc)

    def get_or_set(self, key: str, producer, ttl_s: int) -> Any:  # type: ignore[no-untyped-def]
        value = self.get(key)
        if value is not None:
            return value
        value = producer()
        self.set(key, value, ttl_s)
        return value

    def clear(self) -> None:
        self._l1.clear()

    def status(self) -> dict[str, Any]:
        return {"l1": "memory", "redis": bool(self._redis)}
