"""
Caching module with TTL (Time To Live) support.

This module provides a simple in-memory caching system
with TTL for repeated queries.
"""

import time
from typing import Any, Dict, Optional, Callable, TypeVar
from functools import wraps
import hashlib
import json


T = TypeVar('T')


class CacheEntry:
    """Cache entry with value and expiration time."""
    
    def __init__(self, value: Any, ttl: Optional[int] = None):
        """
        Create a cache entry.
        
        Args:
            value: The cached value
            ttl: Time to live in seconds (None for no expiration)
        """
        self.value = value
        self.created_at = time.time()
        self.ttl = ttl
    
    def is_expired(self) -> bool:
        """Check if the entry has expired."""
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl


class SimpleCache:
    """
    Simple in-memory cache with TTL support.
    
    Features:
    - TTL support for automatic expiration
    - LRU eviction when max size reached
    - Thread-safe operations (basic)
    """
    
    def __init__(self, max_size: int = 100, default_ttl: int = 3600):
        """
        Initialize the cache.
        
        Args:
            max_size: Maximum number of entries
            default_ttl: Default TTL in seconds (1 hour)
        """
        self._cache: Dict[str, CacheEntry] = {}
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._hits = 0
        self._misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        entry = self._cache.get(key)
        
        if entry is None:
            self._misses += 1
            return None
        
        if entry.is_expired():
            del self._cache[key]
            self._misses += 1
            return None
        
        self._hits += 1
        return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set a value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: TTL in seconds (uses default if None)
        """
        # Evict if at max size
        if len(self._cache) >= self._max_size:
            self._evict_lru()
        
        if ttl is None:
            ttl = self._default_ttl
        
        self._cache[key] = CacheEntry(value, ttl)
    
    def delete(self, key: str) -> bool:
        """
        Delete a key from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key existed, False otherwise
        """
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0
    
    def _evict_lru(self) -> None:
        """Evict least recently used entry."""
        if not self._cache:
            return
        
        # Find entry with oldest access (simplified - just remove oldest)
        oldest_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k].created_at
        )
        del self._cache[oldest_key]
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dict with hit/miss stats
        """
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 0
        
        return {
            "size": len(self._cache),
            "max_size": self._max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(hit_rate, 3)
        }
    
    def cleanup_expired(self) -> int:
        """
        Remove all expired entries.
        
        Returns:
            Number of entries removed
        """
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.is_expired()
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        return len(expired_keys)


# Create global caches for different purposes
_role_cache = SimpleCache(max_size=50, default_ttl=1800)  # 30 min for roles
_skill_cache = SimpleCache(max_size=100, default_ttl=3600)  # 1 hour for skills
_subjects_cache = SimpleCache(max_size=50, default_ttl=1800)  # 30 min for subjects


def get_role_cache() -> SimpleCache:
    """Get the role cache."""
    return _role_cache


def get_skill_cache() -> SimpleCache:
    """Get the skill cache."""
    return _skill_cache


def get_subjects_cache() -> SimpleCache:
    """Get the subjects cache."""
    return _subjects_cache


def cached(cache: SimpleCache, key_generator: Optional[Callable] = None):
    """
    Decorator for caching function results.
    
    Args:
        cache: Cache instance to use
        key_generator: Function to generate cache key from args
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            # Generate cache key
            if key_generator:
                cache_key = key_generator(*args, **kwargs)
            else:
                # Default key generation using function name and args
                key_data = json.dumps({
                    "func": func.__name__,
                    "args": str(args),
                    "kwargs": str(sorted(kwargs.items()))
                }, sort_keys=True)
                cache_key = hashlib.md5(key_data.encode()).hexdigest()
            
            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Call function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result)
            
            return result
        
        return wrapper
    return decorator


def get_cache_stats() -> Dict[str, Dict[str, Any]]:
    """
    Get statistics for all caches.
    
    Returns:
        Dict of cache name -> stats
    """
    return {
        "role_cache": get_role_cache().get_stats(),
        "skill_cache": get_skill_cache().get_stats(),
        "subjects_cache": get_subjects_cache().get_stats()
    }