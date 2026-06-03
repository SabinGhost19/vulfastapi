from fastapi import FastAPI, HTTPException, Query
import sqlite3
from pathlib import Path

app = FastAPI(title="Demo Vulnerable FastAPI", version="1.0.2")
DB_PATH = Path("/tmp/app-data/demo.db")


@app.on_event("startup")
def startup() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, password TEXT)")
    cur.execute("INSERT OR IGNORE INTO users (id, username, password) VALUES (1, 'admin', 'admin123')")
    cur.execute("INSERT OR IGNORE INTO users (id, username, password) VALUES (2, 'alice', 'alice123')")
    conn.commit()
    conn.close()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}

@app.get("/healthz")
def health() -> dict:
    return {"status": "ok"}

@app.get("/healthy")
def health() -> dict:
    return {"status": "ok"}


@app.get("/users/search")
def search_users(username: str = Query(..., min_length=1)) -> dict:
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    query = f"SELECT id, username FROM users WHERE username = '{username}'"
    try:
        rows = cur.execute(query).fetchall()
        return {"query": query, "results": rows}
    except sqlite3.Error as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        conn.close()


@app.post("/debug/eval")
def debug_eval(payload: dict) -> dict:
    expr = payload.get("expr", "")
    if not expr:
        raise HTTPException(status_code=400, detail="expr is required")
    result = eval(expr)
    return {"result": str(result)}


@app.post("/stats")
def stats(payload: dict) -> dict:
    """Compute basic descriptive statistics over a list of numbers.

    Pure, side-effect-free numeric endpoint (no eval/SQL) — used as the
    well-behaved compute path that the unit tests exercise.
    """
    values = payload.get("values")
    if not isinstance(values, list) or not values:
        raise HTTPException(status_code=400, detail="values must be a non-empty list")
    try:
        nums = [float(v) for v in values]
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="values must be numeric") from exc
    return {
        "count": len(nums),
        "sum": sum(nums),
        "mean": sum(nums) / len(nums),
        "min": min(nums),
        "max": max(nums),
    }
