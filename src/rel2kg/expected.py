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

MAPPING_FILES: tuple[str, ...] = ("postgres.ttl", "mysql.ttl", "sqlite.ttl")

# Distinct resources after R2RML materialization of the seed data.
EXPECTED_PERSON_COUNT = 7
EXPECTED_DEPARTMENT_COUNT = 3
EXPECTED_BOOK_COUNT = 4
EXPECTED_COURSE_COUNT = 4
EXPECTED_LOAN_COUNT = 4
EXPECTED_ENROLLMENT_COUNT = 6
INTEGRATED_PERSON_EMAIL = "ada@campus.example"

QUERY_FILES: tuple[str, ...] = (
    "ada_across_sources.rq",
    "ada_is_one_person.rq",
    "class_counts.rq",
    "cs_enrollments.rq",
    "open_loans.rq",
    "people.rq",
)

EXPECTED_SELECT_ROWS: dict[str, int] = {
    "ada_across_sources": 1,
    "class_counts": 6,
    "cs_enrollments": 5,
    "open_loans": 2,
    "people": 7,
}

EXPECTED_ASK: dict[str, bool] = {
    "ada_is_one_person": True,
}
