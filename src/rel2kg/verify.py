from __future__ import annotations

from collections.abc import Iterable
from contextlib import ExitStack
from typing import Any

from rel2kg.config import MYSQL, POSTGRES, SQLITE_PATH
from rel2kg.db import connect_mysql, connect_postgres, connect_sqlite, wait_for
from rel2kg.expected import (
    EXPECTED_ROW_COUNTS,
    MYSQL_TABLES,
    POSTGRES_TABLES,
    SQLITE_TABLES,
)


def _count(cur: Any, table: str, allowed: tuple[str, ...]) -> int:
    if table not in allowed:
        raise ValueError(f"refusing to count unknown table: {table}")
    cur.execute(f"SELECT COUNT(*) AS n FROM {table}")
    row = cur.fetchone()
    if isinstance(row, dict):
        return int(row["n"])
    return int(row[0])


def _emails(cur: Any, sql: str) -> set[str]:
    cur.execute(sql)
    rows = cur.fetchall()
    out: set[str] = set()
    for row in rows:
        value = row["email"] if isinstance(row, dict) else row[0]
        if value:
            out.add(str(value))
    return out


def _print_table(title: str, status: str, lines: Iterable[str]) -> None:
    print(f"{title:<12} {status}")
    for line in lines:
        print(f"  {line}")
    print()


def verify() -> int:
    print("Rel2KG — relational sources")
    print("=" * 40)
    print()

    with ExitStack() as stack:
        pg = wait_for("PostgreSQL", connect_postgres)
        stack.callback(pg.close)
        my = wait_for("MySQL", connect_mysql)
        stack.callback(my.close)
        sl = wait_for("SQLite", connect_sqlite)
        stack.callback(sl.close)

        with pg.cursor() as cur:
            pg_counts = {name: _count(cur, name, POSTGRES_TABLES) for name in POSTGRES_TABLES}
            pg_emails = _emails(cur, "SELECT email FROM employee")

        with my.cursor() as cur:
            my_counts = {name: _count(cur, name, MYSQL_TABLES) for name in MYSQL_TABLES}
            author_emails = _emails(cur, "SELECT email FROM author WHERE email IS NOT NULL")
            loan_emails = _emails(cur, "SELECT borrower_email AS email FROM loan")
            my_emails = author_emails | loan_emails

        sl_cur = sl.cursor()
        sl_counts = {name: _count(sl_cur, name, SQLITE_TABLES) for name in SQLITE_TABLES}
        sl_emails = _emails(sl_cur, "SELECT student_email AS email FROM enrollment")

    pg_label = f"{POSTGRES.dbname} @ {POSTGRES.host}:{POSTGRES.port}"
    my_label = f"{MYSQL.database} @ {MYSQL.host}:{MYSQL.port}"
    sl_label = str(SQLITE_PATH)

    _print_table(
        "PostgreSQL",
        f"ok  {pg_label}",
        [f"{name:<12} {n} rows" for name, n in pg_counts.items()],
    )
    _print_table(
        "MySQL",
        f"ok  {my_label}",
        [f"{name:<12} {n} rows" for name, n in my_counts.items()],
    )
    _print_table(
        "SQLite",
        f"ok  {sl_label}",
        [f"{name:<12} {n} rows" for name, n in sl_counts.items()],
    )

    all_emails = sorted(pg_emails | my_emails | sl_emails)
    print("Shared identifiers (email) across sources")
    print("-" * 40)
    print(f"{'email':<28} {'HR':<5} {'lib':<5} {'reg'}")
    for email in all_emails:
        hr = "yes" if email in pg_emails else "-"
        lib = "yes" if email in my_emails else "-"
        reg = "yes" if email in sl_emails else "-"
        print(f"{email:<28} {hr:<5} {lib:<5} {reg}")
    print()

    actual = {**pg_counts, **my_counts, **sl_counts}
    mismatches = [name for name, n in EXPECTED_ROW_COUNTS.items() if actual.get(name) != n]
    if mismatches:
        print("Row-count mismatches:", ", ".join(mismatches))
        return 1

    print("All three databases are up and seeded.")
    return 0
