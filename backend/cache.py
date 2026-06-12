import os
import json
import hashlib
from functools import wraps

REDIS_URL = os.getenv("REDIS_URL", None)

if REDIS_URL:
    import redis
    _redis = redis.from_url(REDIS_URL)
else:
    import fakeredis
    _redis = fakeredis.FakeRedis()

def make_key(prefix, *args, **kwargs):
    """Generate a consistent cache key."""
    raw = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
    return f"aegis:{prefix}:{hashlib.md5(raw.encode()).hexdigest()}"

def cached(prefix, ttl=300):
    """
    Decorator to cache function results.
    Usage: @cached("my_prefix", ttl=60)
    """
    def deco(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = make_key(prefix, *args, **kwargs)
            val = _redis.get(key)
            if val:
                return json.loads(val)
            res = func(*args, **kwargs)
            _redis.setex(key, ttl, json.dumps(res, default=str))
            return res
        return wrapper
    return deco

def clear_prefix(prefix):
    """Delete all cached keys with a given prefix."""
    keys = _redis.keys(f"aegis:{prefix}:*")
    if keys:
        _redis.delete(*keys)