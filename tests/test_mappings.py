from __future__ import annotations

import unittest
from pathlib import Path

from rdflib import RDF, RDFS, Graph

from rel2kg.config import MAPPINGS_DIR, VOCAB_PATH
from rel2kg.expected import MAPPING_FILES
from rel2kg.iris import RR, VOCAB, person_iri


class TestIris(unittest.TestCase):
    def test_person_iri_percent_encodes_at(self) -> None:
        self.assertEqual(
            str(person_iri("ada@campus.example")),
            "https://rel2kg.example/id/person/ada%40campus.example",
        )


class TestVocab(unittest.TestCase):
    def test_vocab_parses(self) -> None:
        graph = Graph().parse(VOCAB_PATH, format="turtle")
        for name in ("Person", "Department", "Book", "Course", "Loan", "Enrollment"):
            self.assertIn((VOCAB[name], RDF.type, RDFS.Class), graph)


class TestMappings(unittest.TestCase):
    def test_mapping_files_exist(self) -> None:
        for name in MAPPING_FILES:
            path = Path(MAPPINGS_DIR) / name
            self.assertTrue(path.is_file(), path)

    def test_each_mapping_is_r2rml(self) -> None:
        for name in MAPPING_FILES:
            graph = Graph().parse(MAPPINGS_DIR / name, format="turtle")
            tables = list(graph.objects(None, RR.logicalTable))
            templates = [str(value) for value in graph.objects(None, RR.template)]
            self.assertTrue(tables, f"{name} has no rr:logicalTable")
            self.assertTrue(
                any("https://rel2kg.example/id/person/" in value for value in templates),
                f"{name} does not mint Person IRIs from email",
            )

    def test_person_template_is_shared(self) -> None:
        needle = "https://rel2kg.example/id/person/{email}"
        sqlite_needle = "https://rel2kg.example/id/person/{student_email}"
        mysql_loan = "https://rel2kg.example/id/person/{borrower_email}"
        postgres = (MAPPINGS_DIR / "postgres.ttl").read_text(encoding="utf-8")
        mysql = (MAPPINGS_DIR / "mysql.ttl").read_text(encoding="utf-8")
        sqlite = (MAPPINGS_DIR / "sqlite.ttl").read_text(encoding="utf-8")
        self.assertIn(needle, postgres)
        self.assertIn(needle, mysql)
        self.assertIn(mysql_loan, mysql)
        self.assertIn(sqlite_needle, sqlite)
