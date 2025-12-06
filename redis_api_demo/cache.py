# cache.py
import redis
from typing import Optional


def get_redis_client(db: int = 0) -> redis.Redis:
    """
    Returns a Redis client using a connection pool.
    Assumes Redis is running on localhost:6379 with no password.
    """
    pool = redis.ConnectionPool(
        host="127.0.0.1",
        port=6379,
        db=db,
        decode_responses=True,  # return string instead of bytes
    )
    return redis.Redis(connection_pool=pool)


def ping_redis() -> bool:
    client = get_redis_client()
    return client.ping()

