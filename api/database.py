"""Gerenciador de conexões PostgreSQL e Redis"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
import redis
from typing import Optional

POSTGRES_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", 5435)),
    "database": os.getenv("POSTGRES_DB", "investai"),
    "user": os.getenv("POSTGRES_USER", "investai"),
    "password": os.getenv("POSTGRES_PASSWORD", "investai123")
}

REDIS_CONFIG = {
    "host": os.getenv("REDIS_HOST", "localhost"),
    "port": int(os.getenv("REDIS_PORT", 6380)),
    "password": os.getenv("REDIS_PASSWORD", "investai_redis_2026"),
    "decode_responses": True
}

redis_client: Optional[redis.Redis] = None

def get_redis():
    global redis_client
    if redis_client is None:
        redis_client = redis.Redis(**REDIS_CONFIG)
    return redis_client

@contextmanager
def get_db():
    conn = psycopg2.connect(**POSTGRES_CONFIG, cursor_factory=RealDictCursor)
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def execute_query(query: str, params: tuple = None, fetch_one: bool = False):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            # Only fetch results for SELECT queries
            if cur.description:
                if fetch_one:
                    return cur.fetchone()
                return cur.fetchall()
            # For INSERT/UPDATE/DELETE, return affected rows count
            return cur.rowcount
