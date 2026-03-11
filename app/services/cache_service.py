import json
import time

import redis
from flask import current_app


_fallback_cache = {}
_redis_unavailable_until = 0.0
_cache_stats = {
    "hits": 0,
    "misses": 0,
    "set_calls": 0,
    "backend_errors": 0,
}


def _build_redis_client():
    password = current_app.config["REDIS_PASSWORD"] or None
    return redis.Redis(
        host=current_app.config["REDIS_HOST"],
        port=current_app.config["REDIS_PORT"],
        db=current_app.config["REDIS_DB"],
        password=password,
        decode_responses=True,
        socket_timeout=0.1,
        socket_connect_timeout=0.1,
    )


def get_cache(key):
    global _redis_unavailable_until
    try:
        if _redis_unavailable_until > time.time():
            raise RuntimeError("redis temporarily unavailable")
        client = _build_redis_client()
        value = client.get(key)
        if value:
            _cache_stats["hits"] += 1
            return json.loads(value)
        _cache_stats["misses"] += 1
        return None
    except Exception:
        _redis_unavailable_until = time.time() + 5
        _cache_stats["backend_errors"] += 1
        item = _fallback_cache.get(key)
        if not item:
            _cache_stats["misses"] += 1
            return None
        if item["expired_at"] < time.time():
            _fallback_cache.pop(key, None)
            _cache_stats["misses"] += 1
            return None
        _cache_stats["hits"] += 1
        return item["value"]


def set_cache(key, value, ttl=60):
    global _redis_unavailable_until
    _cache_stats["set_calls"] += 1
    try:
        if _redis_unavailable_until > time.time():
            raise RuntimeError("redis temporarily unavailable")
        client = _build_redis_client()
        client.setex(key, ttl, json.dumps(value, ensure_ascii=False, default=str))
        return
    except Exception:
        _redis_unavailable_until = time.time() + 5
        _cache_stats["backend_errors"] += 1
        _fallback_cache[key] = {"value": value, "expired_at": time.time() + ttl}


def get_cache_stats():
    total = _cache_stats["hits"] + _cache_stats["misses"]
    hit_rate = round((_cache_stats["hits"] / total) * 100, 2) if total else 0.0
    return {
        **_cache_stats,
        "hit_rate": hit_rate,
        "in_memory_keys": len(_fallback_cache),
    }


def reset_cache_stats():
    for k in _cache_stats.keys():
        _cache_stats[k] = 0