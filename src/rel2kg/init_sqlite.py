from __future__ import annotations

import sqlite3

from rel2kg.config import SQL_DIR, SQLITE_PATH


def init_sqlite() -> None:
    sql_file = SQL_DIR / "sqlite" / "init.sql"
    if not sql_file.is_file():
        raise FileNotFoundError(f"SQLite init script not found: {sql_file}")

    SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)
    sql = sql_file.read_text(encoding="utf-8")

    conn = sqlite3.connect(SQLITE_PATH)
    try:
        conn.executescript(sql)
        conn.commit()
    finally:
        conn.close()

    print(f"SQLite ready at {SQLITE_PATH}")
