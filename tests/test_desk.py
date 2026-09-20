from __future__ import annotations

import unittest
from pathlib import Path

from rel2kg.config import WEB_DIR
from rel2kg.desk import (
    EMAIL_RE,
    STATIC_FILES,
    _kind_from_iri,
    _sparql_string,
    parse_map_graphs,
    web_files,
)
from rel2kg.expected import QUERY_FILES
from rel2kg.sparql import query_catalog, query_title


class TestDeskStatic(unittest.TestCase):
    def test_web_files_exist(self) -> None:
        self.assertTrue(WEB_DIR.is_dir(), WEB_DIR)
        for path in web_files().values():
            self.assertTrue(path.is_file(), path)

    def test_index_mentions_sources(self) -> None:
        text = (WEB_DIR / "index.html").read_text(encoding="utf-8")
        self.assertIn("Integration desk", text)
        self.assertIn('id="people"', text)
        self.assertIn('id="sources"', text)
        self.assertIn('id="graphs"', text)
        self.assertIn('id="graph-canvas"', text)
        self.assertIn('data-view="map"', text)


class TestDeskHelpers(unittest.TestCase):
    def test_email_guard(self) -> None:
        self.assertEqual(_sparql_string("ada@campus.example"), '"ada@campus.example"')
        with self.assertRaises(ValueError):
            _sparql_string('ada@" OR "1')
        self.assertTrue(EMAIL_RE.fullmatch("timbl@w3.example"))
        self.assertFalse(EMAIL_RE.fullmatch("not-an-email"))

    def test_static_allowlist(self) -> None:
        self.assertEqual(STATIC_FILES["/"], "index.html")
        self.assertEqual(STATIC_FILES["/static/app.js"], "app.js")
        self.assertEqual(STATIC_FILES["/static/graph.js"], "graph.js")

    def test_parse_map_graphs(self) -> None:
        self.assertEqual(parse_map_graphs(""), ["hr", "library", "registrar", "identity"])
        self.assertEqual(parse_map_graphs("hr"), ["hr"])
        self.assertEqual(parse_map_graphs("library,hr,library"), ["library", "hr"])
        with self.assertRaises(ValueError):
            parse_map_graphs("vocab")

    def test_kind_from_iri(self) -> None:
        self.assertEqual(_kind_from_iri("https://rel2kg.example/id/person/x"), "person")
        self.assertEqual(_kind_from_iri("https://rel2kg.example/id/book/x"), "book")

    def test_query_titles(self) -> None:
        catalog = {item["name"]: item for item in query_catalog()}
        self.assertEqual(set(catalog), {Path(name).stem for name in QUERY_FILES})
        self.assertIn("Ada", catalog["ada_across_sources"]["title"])
        self.assertEqual(catalog["ada_is_one_person"]["kind"], "ask")
        people = WEB_DIR.parent / "queries" / "people.rq"
        self.assertTrue(query_title(people).startswith("All people"))
