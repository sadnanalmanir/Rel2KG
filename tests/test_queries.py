from __future__ import annotations

import unittest
from pathlib import Path

from rdflib.plugins.sparql import prepareQuery

from rel2kg.config import QUERIES_DIR
from rel2kg.expected import EXPECTED_ASK, EXPECTED_SELECT_ROWS, QUERY_FILES


class TestQueries(unittest.TestCase):
    def test_query_files_exist(self) -> None:
        for name in QUERY_FILES:
            path = QUERIES_DIR / name
            self.assertTrue(path.is_file(), path)

    def test_expectations_cover_files(self) -> None:
        stems = {Path(name).stem for name in QUERY_FILES}
        expected = set(EXPECTED_SELECT_ROWS) | set(EXPECTED_ASK)
        self.assertEqual(stems, expected)
        self.assertFalse(set(EXPECTED_SELECT_ROWS) & set(EXPECTED_ASK))

    def test_queries_parse(self) -> None:
        for name in QUERY_FILES:
            text = (QUERIES_DIR / name).read_text(encoding="utf-8")
            prepareQuery(text)

    def test_integration_query_mentions_all_sources(self) -> None:
        text = (QUERIES_DIR / "ada_across_sources.rq").read_text(encoding="utf-8")
        for source in ("hr", "library", "registrar"):
            self.assertIn(f"source/{source}", text)
