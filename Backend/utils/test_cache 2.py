"""
Test script to verify Redis caching is working
Run with: python -m utils.test_cache
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.cache import get_cache_manager
from config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_cache():
    """Test cache functionality"""
    print("=" * 60)
    print("Testing Redis Cache Implementation")
    print("=" * 60)
    
    # Get cache manager
    cache = get_cache_manager()
    
    # Check cache status
    print(f"\n1. Cache Status:")
    print(f"   - Using Redis: {cache.use_redis}")
    print(f"   - Redis Available: {cache.redis_client is not None}")
    print(f"   - Cache Enabled: {Config.CACHE_ENABLED}")
    
    if not Config.CACHE_ENABLED:
        print("\n⚠️  WARNING: CACHE_ENABLED is False in config!")
        print("   Set CACHE_ENABLED=true in .env to enable caching")
    
    # Test basic operations
    print(f"\n2. Testing Basic Cache Operations:")
    
    # Test set/get
    test_key = "test:cache:key"
    test_value = {"data": "test", "number": 123}
    
    print(f"   Setting cache key: {test_key}")
    success = cache.set(test_key, test_value, ttl=60)
    print(f"   Set result: {success}")
    
    print(f"   Getting cache key: {test_key}")
    retrieved = cache.get(test_key)
    print(f"   Retrieved: {retrieved}")
    
    if retrieved == test_value:
        print("   ✅ Cache GET/SET working correctly!")
    else:
        print("   ❌ Cache GET/SET failed!")
        print(f"   Expected: {test_value}")
        print(f"   Got: {retrieved}")
    
    # Test cache miss
    print(f"\n3. Testing Cache Miss:")
    missing = cache.get("test:cache:missing")
    if missing is None:
        print("   ✅ Cache miss handled correctly (returns None)")
    else:
        print(f"   ❌ Cache miss should return None, got: {missing}")
    
    # Test cache expiration simulation
    print(f"\n4. Testing Cache TTL:")
    expiring_key = "test:cache:expiring"
    cache.set(expiring_key, "will expire", ttl=1)
    print(f"   Set key with 1 second TTL")
    import time
    time.sleep(2)
    expired = cache.get(expiring_key)
    if expired is None:
        print("   ✅ Cache expiration working (key expired)")
    else:
        print(f"   ⚠️  Cache expiration: key still exists (may be in-memory cache)")
    
    # Test cache clear
    print(f"\n5. Testing Cache Clear:")
    cache.set("test:clear:1", "value1")
    cache.set("test:clear:2", "value2")
    cleared = cache.clear("test:clear:*")
    print(f"   Cleared {cleared} keys matching pattern")
    
    # Summary
    print("\n" + "=" * 60)
    print("Cache Test Summary:")
    print("=" * 60)
    
    if cache.use_redis:
        print("✅ Redis cache is ACTIVE")
        print("   - Using distributed Redis cache")
        print("   - Cache is shared across instances")
    else:
        print("⚠️  Using IN-MEMORY cache fallback")
        print("   - Redis not available or connection failed")
        print("   - Cache is local to this process only")
        print("\n   To enable Redis:")
        print("   1. Install Redis: brew install redis (Mac) or apt-get install redis (Linux)")
        print("   2. Start Redis: redis-server")
        print("   3. Set REDIS_HOST in .env (default: localhost)")
    
    if Config.CACHE_ENABLED:
        print("\n✅ Caching is ENABLED in configuration")
    else:
        print("\n⚠️  Caching is DISABLED in configuration")
        print("   Set CACHE_ENABLED=true in .env to enable")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_cache()

