from __future__ import annotations

import unittest

from rdflib import RDF, Graph, Literal, URIRef
from rdflib.namespace import XSD

from rel2kg.config import SHAPES_PATH
from rel2kg.iris import DCTERMS, FOAF, SCHEMA, SOURCE_HR, VOCAB, person_iri
from rel2kg.shacl import SHAPE_IRIS, load_shapes, validate_graph


class TestShapesFile(unittest.TestCase):
    def test_shapes_parse(self) -> None:
        graph = load_shapes()
        self.assertTrue(SHAPES_PATH.is_file())
        for name in SHAPE_IRIS:
            self.assertTrue(
                list(graph.triples((VOCAB[name], None, None))),
                f"missing shape {name}",
            )


class TestValidate(unittest.TestCase):
    def test_person_without_email_fails(self) -> None:
        data = Graph()
        person = person_iri("ghost@campus.example")
        data.add((person, RDF.type, VOCAB.Person))
        data.add((person, DCTERMS.source, SOURCE_HR))
        conforms, _, _ = validate_graph(data)
        self.assertFalse(conforms)

    def test_minimal_person_passes(self) -> None:
        data = Graph()
        person = person_iri("ada@campus.example")
        data.add((person, RDF.type, VOCAB.Person))
        data.add((person, SCHEMA.email, Literal("ada@campus.example")))
        data.add((person, DCTERMS.source, SOURCE_HR))
        conforms, report, _ = validate_graph(data)
        self.assertTrue(conforms, report)

    def test_employee_without_department_fails(self) -> None:
        data = Graph()
        person = person_iri("ada@campus.example")
        data.add((person, RDF.type, VOCAB.Person))
        data.add((person, SCHEMA.email, Literal("ada@campus.example")))
        data.add((person, DCTERMS.source, SOURCE_HR))
        data.add((person, FOAF.givenName, Literal("Ada")))
        data.add((person, FOAF.familyName, Literal("Lovelace")))
        data.add((person, VOCAB.hiredOn, Literal("2018-03-01", datatype=XSD.date)))
        conforms, _, _ = validate_graph(data)
        self.assertFalse(conforms)

    def test_loan_requires_borrower(self) -> None:
        data = Graph()
        loan = URIRef("https://rel2kg.example/id/loan/99")
        book = URIRef("https://rel2kg.example/id/book/x")
        data.add((loan, RDF.type, VOCAB.Loan))
        data.add((loan, VOCAB.borrowed, book))
        data.add((book, RDF.type, VOCAB.Book))
        conforms, _, _ = validate_graph(data)
        self.assertFalse(conforms)
