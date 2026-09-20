from __future__ import annotations

import unittest

from rdflib import Graph

from rel2kg.config import LINKS_PATH
from rel2kg.expected import LINKED_CAMPUS_EMAIL, LINKED_PUBLISHER_EMAIL
from rel2kg.iris import OWL, person_iri


class TestIdentityLinks(unittest.TestCase):
    def test_sameas_file(self) -> None:
        graph = Graph().parse(LINKS_PATH, format="turtle")
        campus = person_iri(LINKED_CAMPUS_EMAIL)
        publisher = person_iri(LINKED_PUBLISHER_EMAIL)
        self.assertIn((campus, OWL.sameAs, publisher), graph)
        self.assertIn((publisher, OWL.sameAs, campus), graph)
