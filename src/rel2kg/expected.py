"""Seed sizes and table names. Keep in sync with db/*/init.sql."""

from __future__ import annotations

EXPECTED_ROW_COUNTS: dict[str, int] = {
    "department": 3,
    "employee": 5,
    "author": 4,
    "book": 4,
    "loan": 4,
    "course": 4,
    "enrollment": 6,
}

POSTGRES_TABLES: tuple[str, ...] = ("department", "employee")
MYSQL_TABLES: tuple[str, ...] = ("author", "book", "loan")
SQLITE_TABLES: tuple[str, ...] = ("course", "enrollment")
