import hashlib
import time
import json
import threading
from typing import Optional, Dict, Any
from .models import AnalysisResult


class AnalysisCache:
    """In-memory cache for image analysis results with TTL."""

    def __init__(self, ttl_seconds: int = 3600, max_entries: int = 100):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._ttl = ttl_seconds
        self._max = max_entries
        self._lock = threading.Lock()

    def _key(self, image_bytes: bytes) -> str:
        return hashlib.sha256(image_bytes).hexdigest()

    def get(self, image_bytes: bytes) -> Optional[AnalysisResult]:
        key = self._key(image_bytes)
        with self._lock:
            entry = self._cache.get(key)
            if entry and (time.time() - entry["ts"]) < self._ttl:
                result: AnalysisResult = entry["result"]
                result.cached = True
                return result
            if entry:
                del self._cache[key]
        return None

    def put(self, image_bytes: bytes, result: AnalysisResult):
        key = self._key(image_bytes)
        with self._lock:
            if len(self._cache) >= self._max:
                oldest = min(self._cache, key=lambda k: self._cache[k]["ts"])
                del self._cache[oldest]
            self._cache[key] = {"result": result, "ts": time.time()}

    def clear(self):
        with self._lock:
            self._cache.clear()

    @property
    def size(self) -> int:
        with self._lock:
            return len(self._cache)
