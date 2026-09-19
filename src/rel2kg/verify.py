from __future__ import annotations

from collections.abc import Iterable

from rel2kg.config import MYSQL, POSTGRES, SQLITE_PATH
from rel2kg.db import connect_mysql, connect_postgres, connect_sqlite, wait_for


def _count(cur, table: str) -> int:
    cur.execute(f"SELECT COUNT(*) AS n FROM {table}")
    row = cur.fetchone()
    if isinstance(row, dict):
        return int(row["n"])
    return int(row[0])


def _emails(cur, sql: str) -> set[str]:
    cur.execute(sql)
    rows = cur.fetchall()
    out: set[str] = set()
    for row in rows:
        value = row["email"] if isinstance(row, dict) else row[0]
        if value:
            out.add(value)
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

    pg = wait_for("PostgreSQL", connect_postgres)
    my = wait_for("MySQL", connect_mysql)
    sl = wait_for("SQLite", connect_sqlite)

    try:
        with pg.cursor() as cur:
            pg_counts = {
                "department": _count(cur, "department"),
                "employee": _count(cur, "employee"),
            }
            pg_emails = _emails(cur, "SELECT email FROM employee")

        with my.cursor() as cur:
            my_counts = {
                "author": _count(cur, "author"),
                "book": _count(cur, "book"),
                "loan": _count(cur, "loan"),
            }
            author_emails = _emails(cur, "SELECT email FROM author WHERE email IS NOT NULL")
            loan_emails = _emails(cur, "SELECT borrower_email AS email FROM loan")
            my_emails = author_emails | loan_emails

        sl_cur = sl.cursor()
        sl_counts = {
            "course": _count(sl_cur, "course"),
            "enrollment": _count(sl_cur, "enrollment"),
        }
        sl_emails = _emails(sl_cur, "SELECT student_email AS email FROM enrollment")
    finally:
        pg.close()
        my.close()
        sl.close()

    pg_label = f"{POSTGRES['dbname']} @ {POSTGRES['host']}:{POSTGRES['port']}"
    my_label = f"{MYSQL['database']} @ {MYSQL['host']}:{MYSQL['port']}"
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

    expected = {
        "department": 3,
        "employee": 5,
        "author": 4,
        "book": 4,
        "loan": 4,
        "course": 4,
        "enrollment": 6,
    }
    actual = {**pg_counts, **my_counts, **sl_counts}
    mismatches = [name for name, n in expected.items() if actual.get(name) != n]
    if mismatches:
        print("Row-count mismatches:", ", ".join(mismatches))
        return 1

    print("All three databases are up and seeded.")
    return 0
