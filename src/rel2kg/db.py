from __future__ import annotations

import sqlite3
import time
from collections.abc import Callable
from typing import TypeVar

import pymysql
import psycopg2
from pymysql.cursors import DictCursor

from rel2kg.config import MYSQL, POSTGRES, SQLITE_PATH

T = TypeVar("T")


def wait_for(name: str, fn: Callable[[], T], attempts: int = 30, delay: float = 2.0) -> T:
    last: Exception | None = None
    for i in range(1, attempts + 1):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 — retry any connect failure
            last = exc
            print(f"  waiting for {name} ({i}/{attempts}): {exc}")
            time.sleep(delay)
    raise RuntimeError(f"{name} not reachable") from last


def connect_postgres():
    return psycopg2.connect(**POSTGRES)


def connect_mysql():
    return pymysql.connect(cursorclass=DictCursor, **MYSQL)


def connect_sqlite() -> sqlite3.Connection:
    if not SQLITE_PATH.exists():
        raise FileNotFoundError(f"SQLite database missing: {SQLITE_PATH}")
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
