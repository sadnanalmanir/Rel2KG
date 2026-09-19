from __future__ import annotations

import sqlite3
import time
from collections.abc import Callable

import psycopg2
import pymysql
from pymysql.cursors import DictCursor

from rel2kg.config import MYSQL, POSTGRES, SQLITE_PATH


def wait_for[T](name: str, fn: Callable[[], T], attempts: int = 30, delay: float = 2.0) -> T:
    last: Exception | None = None
    for i in range(1, attempts + 1):
        try:
            return fn()
        except Exception as exc:
            last = exc
            print(f"  waiting for {name} ({i}/{attempts}): {exc}")
            time.sleep(delay)
    raise RuntimeError(f"{name} not reachable") from last


def connect_postgres():
    conn = psycopg2.connect(**POSTGRES.connect_kwargs())
    with conn.cursor() as cur:
        cur.execute("SELECT 1")
    return conn


def connect_mysql():
    conn = pymysql.connect(cursorclass=DictCursor, **MYSQL.connect_kwargs())
    with conn.cursor() as cur:
        cur.execute("SELECT 1")
    return conn


def connect_sqlite() -> sqlite3.Connection:
    if not SQLITE_PATH.exists():
        raise FileNotFoundError(f"SQLite database missing: {SQLITE_PATH}")
    conn = sqlite3.connect(SQLITE_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
