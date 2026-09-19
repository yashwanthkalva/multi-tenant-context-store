import os
import redis
import json

redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6380/0')

try:
    redis_client = redis.Redis.from_url(redis_url, decode_responses=True)
except Exception as e:
    print(f"Failed to connect to Redis: {e}")
    redis_client = None

def get_tenant_cache_key(tenant_id: str) -> str:
    return f"tenant:{tenant_id}:context"

def get_cached_context(tenant_id: str) -> dict:
    if not redis_client:
        return None
    try:
        cached_data = redis_client.get(get_tenant_cache_key(tenant_id))
        if cached_data:
            return json.loads(cached_data)
    except Exception as e:
        print(f"Redis get error: {e}")
    return None

def set_cached_context(tenant_id: str, context_dict: dict, ttl_seconds: int = 3600):
    if not redis_client:
        return
    try:
        redis_client.setex(
            name=get_tenant_cache_key(tenant_id),
            time=ttl_seconds,
            value=json.dumps(context_dict)
        )
    except Exception as e:
        print(f"Redis set error: {e}")
