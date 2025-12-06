### FastAPI–Redis–SQLite User Cache Demo | Real-life example

A minimal real-life example of a read-heavy API where requests flow through:

> **Client → API Server (FastAPI) → Redis Cache → DB (SQLite)**

---

## 🔁 Request Flow

1. Client calls `GET /users/{id}`
2. API checks **Redis** for user data
3. If **cache miss**:
   - Load user from **SQLite DB**
   - Store user in **Redis** with TTL
   - Return response
4. Next requests for the same user are served **directly from Redis** (faster)

---

## 📁 Project Layout

Create a folder, e.g. `redis_api_demo`:

```text
redis_api_demo/
├─ requirements.txt
├─ main.py          # FastAPI app (API server)
├─ cache.py         # Redis client helper
└─ db.py            # SQLite "database"
```

You should already have **Redis** installed and running on your local Linux machine.

---

## 📦 Dependencies (`requirements.txt`)

```text
fastapi
uvicorn[standard]
redis==5.0.1
```

### Install

```bash
cd redis_api_demo
python3.8 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 🗄️ `db.py` – Simple SQLite Database

We’ll use SQLite as our DB and pre-load a few demo users.

```python
# db.py
import sqlite3
from typing import Optional, Dict, Any

DB_PATH = "app.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # return rows as dict-like
    return conn


def init_db() -> None:
    """
    Create the users table and insert some demo data if empty.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                active INTEGER NOT NULL
            )
            """
        )
        conn.commit()

        # Check if table is empty
        cur.execute("SELECT COUNT(*) AS cnt FROM users")
        count = cur.fetchone()["cnt"]

        if count == 0:
            print("[DB] Seeding demo data...")
            demo_users = [
                (1, "Alice", "alice@example.com", 1),
                (2, "Bob", "bob@example.com", 1),
                (3, "Charlie", "charlie@example.com", 0),
            ]
            cur.executemany(
                "INSERT INTO users (id, name, email, active) VALUES (?, ?, ?, ?)",
                demo_users,
            )
            conn.commit()
    finally:
        conn.close()


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """
    Load a user from the database by ID.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, name, email, active FROM users WHERE id = ?",
            (user_id,),
        )
        row = cur.fetchone()
        if row is None:
            return None

        # Convert SQLite Row to normal dict
        return {
            "id": row["id"],
            "name": row["name"],
            "email": row["email"],
            "active": bool(row["active"]),
        }
    finally:
        conn.close()
```

---

## 🧰 `cache.py` – Redis Client Helper

```python
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
```

> 💡 If you set a password in `redis.conf`, add `password="yourpass"` to `ConnectionPool(...)`.

---

## 🌐 `main.py` – FastAPI Server Using Redis + SQLite

```python
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
```

---

## 🚀 Run the API Server

From inside the virtualenv:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

You should see logs like:

```text
[DB] Seeding demo data...
[REDIS] Connection OK
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

## ✅ Test the Full Flow (API → Redis → DB)

### 1. Health Check

```bash
curl http://127.0.0.1:8000/health
```

Expected:

```json
{
  "status": "ok",
  "redis": true,
  "db": true
}
```

---

### 2. First Request for a User (Hits DB)

```bash
curl http://127.0.0.1:8000/users/1
```

First hit should return:

```json
{
  "source": "database",
  "user": {
    "id": 1,
    "name": "Alice",
    "email": "alice@example.com",
    "active": true
  }
}
```

---

### 3. Second Request (Served from Redis)

Run the same request again:

```bash
curl http://127.0.0.1:8000/users/1
```

Now you should get:

```json
{
  "source": "redis_cache",
  "user": {
    "id": 1,
    "name": "Alice",
    "email": "alice@example.com",
    "active": true
  }
}
```

So the path is:

> **Client → FastAPI → Redis (hit) → return (DB skipped)**

---

## 🔍 Verify in Redis (Optional)

From terminal:

```bash
redis-cli
127.0.0.1:6379> KEYS "user:*"
# Should show something like:
# 1) "user:1"

127.0.0.1:6379> GET "user:1"
# You’ll see JSON string for the user
```

Check TTL:

```bash
127.0.0.1:6379> TTL "user:1"
```

---

## 🧾 Summary

You now have a simple but realistic chain:

- **API server (FastAPI)** exposes `GET /users/{id}`
- **Redis** used as a **read cache**
- **SQLite** as the **persistent database**
- First request:
  - Comes from **DB**, then cached in **Redis**
- Next requests:
  - Served from **Redis** until the TTL expires

---

## 📛 Suggested Repository Name

**`fastapi-redis-sqlite-cache-demo`**
