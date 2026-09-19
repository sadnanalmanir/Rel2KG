from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _env(name: str, default: str) -> str:
    value = os.environ.get(name)
    return default if value is None or value == "" else value


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class PostgresSettings:
    host: str
    port: int
    user: str
    password: str
    dbname: str

    @classmethod
    def from_env(cls) -> PostgresSettings:
        return cls(
            host=_env("POSTGRES_HOST", "postgres"),
            port=int(_env("POSTGRES_PORT", "5432")),
            user=_env("POSTGRES_USER", "rel2kg"),
            password=_env("POSTGRES_PASSWORD", "rel2kg"),
            dbname=_env("POSTGRES_DB", "campus"),
        )

    def connect_kwargs(self) -> dict[str, object]:
        return {
            "host": self.host,
            "port": self.port,
            "user": self.user,
            "password": self.password,
            "dbname": self.dbname,
            "connect_timeout": 5,
            "application_name": "rel2kg",
        }


@dataclass(frozen=True)
class MysqlSettings:
    host: str
    port: int
    user: str
    password: str
    database: str

    @classmethod
    def from_env(cls) -> MysqlSettings:
        return cls(
            host=_env("MYSQL_HOST", "mysql"),
            port=int(_env("MYSQL_PORT", "3306")),
            user=_env("MYSQL_USER", "rel2kg"),
            password=_env("MYSQL_PASSWORD", "rel2kg"),
            database=_env("MYSQL_DATABASE", "library"),
        )

    def connect_kwargs(self) -> dict[str, object]:
        return {
            "host": self.host,
            "port": self.port,
            "user": self.user,
            "password": self.password,
            "database": self.database,
            "connect_timeout": 5,
            "charset": "utf8mb4",
        }


POSTGRES = PostgresSettings.from_env()
MYSQL = MysqlSettings.from_env()
SQLITE_PATH = Path(_env("SQLITE_PATH", str(_repo_root() / "data" / "courses.db")))
SQL_DIR = Path(_env("SQL_DIR", str(_repo_root() / "db")))
