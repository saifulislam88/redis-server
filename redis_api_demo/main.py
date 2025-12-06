# main.py
import json
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from cache import get_redis_client, ping_redis
from db import init_db, get_user_by_id

app = FastAPI(title="Redis API Demo")


@app.on_event("startup")
async def startup_event() -> None:
    # Initialize DB and seed data
    init_db()

    # Test Redis connection on startup
    try:
        if ping_redis():
            print("[REDIS] Connection OK")
    except Exception as e:
        print(f"[REDIS] Connection failed: {e}")


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Simple health check for API, Redis and DB (basic).
    """
    redis_ok = False
    try:
        redis_ok = ping_redis()
    except Exception:
        redis_ok = False

    return {
        "status": "ok",
        "redis": redis_ok,
        "db": True,  # if init_db didn't crash, we assume basic DB ok
    }


@app.get("/users/{user_id}")
async def get_user(user_id: int) -> JSONResponse:
    """
    Get user by ID:
    1) Try Redis cache
    2) If not found, load from DB and cache it
    """
    redis_client = get_redis_client(db=0)
    cache_key = f"user:{user_id}"

    # 1) Try Redis cache
    cached = redis_client.get(cache_key)
    if cached is not None:
        user_data = json.loads(cached)
        return JSONResponse(
            content={"source": "redis_cache", "user": user_data},
            status_code=200,
        )

    # 2) Load from DB
    user = get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # 3) Store in Redis with TTL (e.g., 60 seconds)
    redis_client.setex(cache_key, 60, json.dumps(user))

    return JSONResponse(
        content={"source": "database", "user": user},
        status_code=200,
    )

