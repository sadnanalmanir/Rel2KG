from __future__ import annotations

import unittest
from pathlib import Path

from rel2kg.config import SQL_DIR
from rel2kg.expected import MYSQL_TABLES, POSTGRES_TABLES, SQLITE_TABLES


class TestSqlSeeds(unittest.TestCase):
    def test_sql_dir_exists(self) -> None:
        self.assertTrue(SQL_DIR.is_dir(), f"SQL_DIR missing: {SQL_DIR}")

    def test_postgres_defines_tables(self) -> None:
        text = _read("postgres")
        for table in POSTGRES_TABLES:
            self.assertIn(f"CREATE TABLE {table}", text)

    def test_mysql_defines_tables(self) -> None:
        text = _read("mysql")
        for table in MYSQL_TABLES:
            self.assertIn(f"CREATE TABLE {table}", text)

    def test_sqlite_defines_tables(self) -> None:
        text = _read("sqlite")
        for table in SQLITE_TABLES:
            self.assertIn(f"CREATE TABLE IF NOT EXISTS {table}", text)

    def test_seed_sizes_are_documented(self) -> None:
        for engine in ("postgres", "mysql", "sqlite"):
            self.assertIn("Seed size:", _read(engine))


def _read(engine: str) -> str:
    path = Path(SQL_DIR) / engine / "init.sql"
    self_msg = f"missing seed file: {path}"
    if not path.is_file():
        raise AssertionError(self_msg)
    return path.read_text(encoding="utf-8")
