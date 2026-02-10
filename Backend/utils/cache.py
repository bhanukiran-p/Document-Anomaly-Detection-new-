"""
Distributed Caching Layer
Provides caching for OCR, ML predictions, and API responses using Redis
"""

import json
import hashlib
import logging
from typing import Optional, Any, Dict
from functools import wraps
import pickle

logger = logging.getLogger(__name__)

# Try to import Redis, fallback to in-memory cache if not available
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available, using in-memory cache fallback")

# In-memory cache fallback
_memory_cache: Dict[str, Any] = {}


class CacheManager:
    """
    Distributed cache manager using Redis with in-memory fallback
    """
    
    def __init__(self, redis_host: str = 'localhost', redis_port: int = 6379, 
                 redis_db: int = 0, redis_password: Optional[str] = None,
                 default_ttl: int = 3600):
        """
        Initialize cache manager
        
        Args:
            redis_host: Redis server host
            redis_port: Redis server port
            redis_db: Redis database number
            redis_password: Redis password (if required)
            default_ttl: Default TTL in seconds (1 hour)
        """
        self.default_ttl = default_ttl
        self.redis_client = None
        self.use_redis = False
        
        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    db=redis_db,
                    password=redis_password,
                    decode_responses=False,  # We'll handle encoding ourselves
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
                # Test connection
                self.redis_client.ping()
                self.use_redis = True
                logger.info(f"Redis cache initialized: {redis_host}:{redis_port}")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}. Using in-memory cache.")
                self.use_redis = False
        else:
            logger.info("Using in-memory cache (Redis not installed)")
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """
        Generate cache key from arguments
        
        Args:
            prefix: Cache key prefix
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Cache key string
        """
        # Create a hash of all arguments
        key_data = {
            'args': args,
            'kwargs': kwargs
        }
        key_str = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.md5(key_str.encode()).hexdigest()
        return f"{prefix}:{key_hash}"
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        try:
            if self.use_redis and self.redis_client:
                cached = self.redis_client.get(key)
                if cached:
                    return pickle.loads(cached)
            else:
                # In-memory cache
                if key in _memory_cache:
                    value, expiry = _memory_cache[key]
                    import time
                    if expiry is None or time.time() < expiry:
                        return value
                    else:
                        del _memory_cache[key]
        except Exception as e:
            logger.warning(f"Cache get error for key {key}: {e}")
        
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (uses default if None)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            ttl = ttl or self.default_ttl
            
            if self.use_redis and self.redis_client:
                serialized = pickle.dumps(value)
                self.redis_client.setex(key, ttl, serialized)
                return True
            else:
                # In-memory cache
                import time
                expiry = time.time() + ttl if ttl else None
                _memory_cache[key] = (value, expiry)
                return True
        except Exception as e:
            logger.warning(f"Cache set error for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete key from cache
        
        Args:
            key: Cache key
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.use_redis and self.redis_client:
                self.redis_client.delete(key)
            else:
                _memory_cache.pop(key, None)
            return True
        except Exception as e:
            logger.warning(f"Cache delete error for key {key}: {e}")
            return False
    
    def clear(self, pattern: Optional[str] = None) -> int:
        """
        Clear cache entries matching pattern
        
        Args:
            pattern: Key pattern (e.g., 'ocr:*'). If None, clears all.
            
        Returns:
            Number of keys deleted
        """
        try:
            if self.use_redis and self.redis_client:
                if pattern:
                    keys = self.redis_client.keys(pattern)
                    if keys:
                        return self.redis_client.delete(*keys)
                else:
                    self.redis_client.flushdb()
                    return -1  # Unknown count
            else:
                # In-memory cache
                if pattern:
                    prefix = pattern.replace('*', '')
                    keys_to_delete = [k for k in _memory_cache.keys() if k.startswith(prefix)]
                    for k in keys_to_delete:
                        del _memory_cache[k]
                    return len(keys_to_delete)
                else:
                    count = len(_memory_cache)
                    _memory_cache.clear()
                    return count
        except Exception as e:
            logger.warning(f"Cache clear error: {e}")
            return 0


# Global cache instance (initialized on first use)
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """
    Get or create global cache manager instance
    
    Returns:
        CacheManager instance
    """
    global _cache_manager
    
    if _cache_manager is None:
        import os
        redis_host = os.getenv('REDIS_HOST', 'localhost')
        redis_port = int(os.getenv('REDIS_PORT', '6379'))
        redis_db = int(os.getenv('REDIS_DB', '0'))
        redis_password = os.getenv('REDIS_PASSWORD')
        default_ttl = int(os.getenv('CACHE_TTL', '3600'))
        
        _cache_manager = CacheManager(
            redis_host=redis_host,
            redis_port=redis_port,
            redis_db=redis_db,
            redis_password=redis_password,
            default_ttl=default_ttl
        )
    
    return _cache_manager


def cached(prefix: str, ttl: int = 3600):
    """
    Decorator to cache function results
    
    Args:
        prefix: Cache key prefix
        ttl: Time to live in seconds
        
    Usage:
        @cached('ocr', ttl=7200)
        def extract_with_mindee(image_path):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_cache_manager()
            
            # Generate cache key
            cache_key = cache._generate_key(prefix, *args, **kwargs)
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache HIT: {cache_key}")
                return cached_result
            
            # Cache miss - execute function
            logger.debug(f"Cache MISS: {cache_key}")
            result = func(*args, **kwargs)
            
            # Store in cache
            cache.set(cache_key, result, ttl=ttl)
            
            return result
        
        return wrapper
    return decorator

