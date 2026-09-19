import os
from pathlib import Path


def _env(name: str, default: str) -> str:
    return os.environ.get(name, default)


POSTGRES = {
    "host": _env("POSTGRES_HOST", "postgres"),
    "port": int(_env("POSTGRES_PORT", "5432")),
    "user": _env("POSTGRES_USER", "rel2kg"),
    "password": _env("POSTGRES_PASSWORD", "rel2kg"),
    "dbname": _env("POSTGRES_DB", "campus"),
}

MYSQL = {
    "host": _env("MYSQL_HOST", "mysql"),
    "port": int(_env("MYSQL_PORT", "3306")),
    "user": _env("MYSQL_USER", "rel2kg"),
    "password": _env("MYSQL_PASSWORD", "rel2kg"),
    "database": _env("MYSQL_DATABASE", "library"),
}

SQLITE_PATH = Path(_env("SQLITE_PATH", "/data/courses.db"))
SQL_DIR = Path(_env("SQL_DIR", "/db"))
