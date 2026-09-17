"""
Response caching to reduce API calls and improve performance
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

class ResponseCache:
    """Simple cache for LLM responses"""

    def __init__(self, cache_dir: str = ".cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.memory_cache = {}

    def _hash_key(self, text: str) -> str:
        """Generate cache key from text"""
        return hashlib.md5(text.lower().encode()).hexdigest()[:16]

    def get(self, question: str) -> Optional[Dict[str, Any]]:
        """Get cached response"""
        key = self._hash_key(question)

        # Check memory cache first
        if key in self.memory_cache:
            return self.memory_cache[key]

        # Check disk cache
        cache_file = self.cache_dir / f"{key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, "r") as f:
                    data = json.load(f)
                    # Cache in memory
                    self.memory_cache[key] = data
                    return data
            except:
                pass

        return None

    def set(self, question: str, response: Dict[str, Any]) -> None:
        """Cache a response"""
        key = self._hash_key(question)
        response["cached_at"] = datetime.now().isoformat()

        # Cache in memory
        self.memory_cache[key] = response

        # Cache to disk
        try:
            cache_file = self.cache_dir / f"{key}.json"
            with open(cache_file, "w") as f:
                json.dump(response, f, indent=2, default=str)
        except:
            pass

    def clear(self) -> None:
        """Clear all caches"""
        self.memory_cache.clear()
        for f in self.cache_dir.glob("*.json"):
            f.unlink()


# Global cache instance
_cache = ResponseCache()


def get_cached_response(question: str) -> Optional[Dict[str, Any]]:
    """Get cached response for a question"""
    return _cache.get(question)


def cache_response(question: str, response: Dict[str, Any]) -> None:
    """Cache a response"""
    _cache.set(question, response)


def clear_cache() -> None:
    """Clear all caches"""
    _cache.clear()
