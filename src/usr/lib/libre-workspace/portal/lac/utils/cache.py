import os
import redis
import json


if os.getenv("REDIS_ADDRESS", "") != "":
    redis_client = redis.Redis.from_url(os.getenv("REDIS_ADDRESS"))
else:
    redis_client = None
    local_cache = {}

def get_value_from_cache(key, default=None):
    if redis_client:
        value = redis_client.get(key)
        if value:
            return value.decode("utf-8").strip("\"")
        else:
            return default
    else:
        return local_cache.get(key, default)
    
def set_value_in_cache(key, value, expiration_seconds=None):
    if redis_client:
        redis_client.set(key, json.dumps(value), ex=expiration_seconds)
    else:
        local_cache[key] = value

def append_to_list_in_cache(key, value, max_length=None):
    if redis_client:
        redis_client.rpush(key, json.dumps(value))
        if max_length:
            redis_client.ltrim(key, -max_length, -1)
    else:
        if key not in local_cache:
            local_cache[key] = []
        local_cache[key].append(value)
        if max_length and len(local_cache[key]) > max_length:
            local_cache[key] = local_cache[key][-max_length:]

def get_list_from_cache(key):
    if redis_client:
        values = redis_client.lrange(key, 0, -1)
        return [json.loads(v.decode("utf-8")) for v in values]
    else:
        return local_cache.get(key, [])
    

def remove_from_list_in_cache(key, value):
    if redis_client:
        redis_client.lrem(key, 0, value)
    else:
        if key in local_cache and value in local_cache[key]:
            local_cache[key].remove(value)


def clear_cache_key(key):
    if redis_client:
        redis_client.delete(key)
    else:
        if key in local_cache:
            del local_cache[key]