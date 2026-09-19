"""Stable IRIs for the lab vocabulary, individuals, and sources."""

from __future__ import annotations

from urllib.parse import quote

from rdflib import Namespace, URIRef

BASE = "https://rel2kg.example/"
VOCAB = Namespace(f"{BASE}vocab#")
FOAF = Namespace("http://xmlns.com/foaf/0.1/")
SCHEMA = Namespace("https://schema.org/")
DCTERMS = Namespace("http://purl.org/dc/terms/")
RR = Namespace("http://www.w3.org/ns/r2rml#")

SOURCE_HR = URIRef(f"{BASE}source/hr")
SOURCE_LIBRARY = URIRef(f"{BASE}source/library")
SOURCE_REGISTRAR = URIRef(f"{BASE}source/registrar")


def iri_safe(value: str) -> str:
    """Percent-encode the way R2RML templates encode IRI components."""
    return quote(value, safe="-._~")


def person_iri(email: str) -> URIRef:
    return URIRef(f"{BASE}id/person/{iri_safe(email)}")


def department_iri(code: str) -> URIRef:
    return URIRef(f"{BASE}id/department/{iri_safe(code)}")


def book_iri(isbn: str) -> URIRef:
    return URIRef(f"{BASE}id/book/{iri_safe(isbn)}")


def course_iri(code: str) -> URIRef:
    return URIRef(f"{BASE}id/course/{iri_safe(code)}")
