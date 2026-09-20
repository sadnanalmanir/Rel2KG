from __future__ import annotations

from pathlib import Path
from urllib.parse import quote_plus

from rdflib import RDF, RDFS, Dataset, Graph, URIRef

from rel2kg.config import (
    KG_NQUADS,
    KG_OUTPUT,
    LINKS_PATH,
    MAPPINGS_DIR,
    MYSQL,
    POSTGRES,
    SQLITE_PATH,
    VOCAB_PATH,
)
from rel2kg.expected import (
    EXPECTED_BOOK_COUNT,
    EXPECTED_COURSE_COUNT,
    EXPECTED_DEPARTMENT_COUNT,
    EXPECTED_ENROLLMENT_COUNT,
    EXPECTED_LOAN_COUNT,
    EXPECTED_NAMED_GRAPHS,
    EXPECTED_PERSON_COUNT,
    INTEGRATED_PERSON_EMAIL,
    LINKED_CAMPUS_EMAIL,
    LINKED_PUBLISHER_EMAIL,
)
from rel2kg.iris import (
    DCTERMS,
    FOAF,
    GRAPH_HR,
    GRAPH_IDENTITY,
    GRAPH_LIBRARY,
    GRAPH_REGISTRAR,
    GRAPH_VOCAB,
    OWL,
    SCHEMA,
    VOCAB,
    book_iri,
    course_iri,
    department_iri,
    person_iri,
)

SOURCE_MAPPINGS: tuple[tuple[str, URIRef, str, str], ...] = (
    ("postgres", GRAPH_HR, "postgres.ttl", "postgres"),
    ("mysql", GRAPH_LIBRARY, "mysql.ttl", "mysql"),
    ("sqlite", GRAPH_REGISTRAR, "sqlite.ttl", "sqlite"),
)


def _db_url() -> dict[str, str]:
    pg = (
        f"postgresql+psycopg://{quote_plus(POSTGRES.user)}:{quote_plus(POSTGRES.password)}"
        f"@{POSTGRES.host}:{POSTGRES.port}/{POSTGRES.dbname}"
    )
    my = (
        f"mysql+pymysql://{quote_plus(MYSQL.user)}:{quote_plus(MYSQL.password)}"
        f"@{MYSQL.host}:{MYSQL.port}/{MYSQL.database}"
    )
    sqlite = f"sqlite:///{SQLITE_PATH}"
    return {"postgres": pg, "mysql": my, "sqlite": sqlite}


def morph_config_for(section: str, mapping: str, db_url: str) -> str:
    return f"""
[CONFIGURATION]
output_format=N-TRIPLES
number_of_processes=1
logging_level=WARNING
infer_sql_datatypes=no

[{section}]
mappings={MAPPINGS_DIR / mapping}
db_url={db_url}
"""


def morph_config() -> str:
    """Combined config used by tests; materialize() still runs per source."""
    urls = _db_url()
    return f"""
[CONFIGURATION]
output_format=N-TRIPLES
number_of_processes=1
logging_level=WARNING
infer_sql_datatypes=no

[postgres]
mappings={MAPPINGS_DIR / "postgres.ttl"}
db_url={urls["postgres"]}

[mysql]
mappings={MAPPINGS_DIR / "mysql.ttl"}
db_url={urls["mysql"]}

[sqlite]
mappings={MAPPINGS_DIR / "sqlite.ttl"}
db_url={urls["sqlite"]}
"""


def _bind(graph: Graph) -> None:
    graph.bind("rel2kg", VOCAB)
    graph.bind("foaf", FOAF)
    graph.bind("schema", SCHEMA)
    graph.bind("dcterms", DCTERMS)
    graph.bind("owl", OWL)
    graph.bind("rdfs", RDFS)


def union_graph(dataset: Dataset) -> Graph:
    graph = Graph()
    _bind(graph)
    for context in dataset.contexts():
        for triple in context:
            graph.add(triple)
    return graph


def materialize_dataset() -> Dataset:
    import morph_kgc

    urls = _db_url()
    dataset = Dataset()
    for section, graph_iri, mapping, url_key in SOURCE_MAPPINGS:
        source = morph_kgc.materialize(morph_config_for(section, mapping, urls[url_key]))
        named = dataset.graph(graph_iri)
        for triple in source:
            named.add(triple)
    if VOCAB_PATH.is_file():
        vocab = dataset.graph(GRAPH_VOCAB)
        vocab.parse(VOCAB_PATH, format="turtle")
    if LINKS_PATH.is_file():
        identity = dataset.graph(GRAPH_IDENTITY)
        identity.parse(LINKS_PATH, format="turtle")
    return dataset


def _count_type(graph: Graph, class_iri: URIRef) -> int:
    return sum(1 for _ in graph.subjects(RDF.type, class_iri))


def _check(graph: Graph, dataset: Dataset) -> list[str]:
    errors: list[str] = []
    got = {
        "Person": _count_type(graph, VOCAB.Person),
        "Department": _count_type(graph, VOCAB.Department),
        "Book": _count_type(graph, VOCAB.Book),
        "Course": _count_type(graph, VOCAB.Course),
        "Loan": _count_type(graph, VOCAB.Loan),
        "Enrollment": _count_type(graph, VOCAB.Enrollment),
    }
    expected = {
        "Person": EXPECTED_PERSON_COUNT,
        "Department": EXPECTED_DEPARTMENT_COUNT,
        "Book": EXPECTED_BOOK_COUNT,
        "Course": EXPECTED_COURSE_COUNT,
        "Loan": EXPECTED_LOAN_COUNT,
        "Enrollment": EXPECTED_ENROLLMENT_COUNT,
    }
    for name, n in expected.items():
        if got[name] != n:
            errors.append(f"{name}: expected {n} instances, got {got[name]}")

    ada = person_iri(INTEGRATED_PERSON_EMAIL)
    cs = department_iri("CS")
    if (ada, VOCAB.memberOf, cs) not in graph:
        errors.append(f"{ada} is not a member of {cs}")

    loans = list(graph.subjects(VOCAB.borrower, ada))
    if not loans:
        errors.append(f"no loan has borrower {ada}")
    elif (loans[0], VOCAB.borrowed, book_iri("978-0-201-89683")) not in graph:
        errors.append(f"{ada} did not borrow Knuth vol. 1")

    enrollments = list(graph.subjects(VOCAB.student, ada))
    if not any((enr, VOCAB.course, course_iri("SEMWEB101")) in graph for enr in enrollments):
        errors.append(f"{ada} is not enrolled in SEMWEB101")

    named = {ctx.identifier for ctx in dataset.contexts() if ctx.identifier}
    for iri in (GRAPH_HR, GRAPH_LIBRARY, GRAPH_REGISTRAR, GRAPH_VOCAB, GRAPH_IDENTITY):
        if iri not in named:
            errors.append(f"missing named graph {iri}")
    campus_graphs = [iri for iri in named if str(iri).startswith("https://rel2kg.example/graph/")]
    if len(campus_graphs) < EXPECTED_NAMED_GRAPHS:
        errors.append(f"expected {EXPECTED_NAMED_GRAPHS} campus named graphs, got {named}")

    if (ada, RDF.type, VOCAB.Person) not in dataset.graph(GRAPH_HR):
        errors.append("Ada is not typed Person in the HR graph")
    if (ada, RDF.type, VOCAB.Person) not in dataset.graph(GRAPH_LIBRARY):
        errors.append("Ada is not typed Person in the library graph")
    if (ada, RDF.type, VOCAB.Person) not in dataset.graph(GRAPH_REGISTRAR):
        errors.append("Ada is not typed Person in the registrar graph")

    campus = person_iri(LINKED_CAMPUS_EMAIL)
    publisher = person_iri(LINKED_PUBLISHER_EMAIL)
    identity = dataset.graph(GRAPH_IDENTITY)
    if (campus, OWL.sameAs, publisher) not in identity:
        errors.append("missing owl:sameAs from campus Knuth to publisher Knuth")
    if (publisher, RDF.type, VOCAB.Person) not in dataset.graph(GRAPH_LIBRARY):
        errors.append("publisher Knuth is not a Person in the library graph")
    if (campus, RDF.type, VOCAB.Person) not in dataset.graph(GRAPH_HR):
        errors.append("campus Knuth is not a Person in the HR graph")

    return errors


def _print_report(graph: Graph, dataset: Dataset) -> None:
    print("Rel2KG — R2RML materialization")
    print("=" * 40)
    print(f"triples      {len(graph)}")
    print(f"Person       {_count_type(graph, VOCAB.Person)}")
    print(f"Department   {_count_type(graph, VOCAB.Department)}")
    print(f"Book         {_count_type(graph, VOCAB.Book)}")
    print(f"Course       {_count_type(graph, VOCAB.Course)}")
    print(f"Loan         {_count_type(graph, VOCAB.Loan)}")
    print(f"Enrollment   {_count_type(graph, VOCAB.Enrollment)}")
    print("named graphs")
    for context in sorted(dataset.contexts(), key=lambda ctx: str(ctx.identifier)):
        ident = context.identifier
        if ident and str(ident).startswith("https://rel2kg.example/graph/"):
            print(f"  {ident}  {len(context)} triples")
    print()


def materialize(output: Path | None = None) -> int:
    from rel2kg.init_sqlite import init_sqlite

    if not SQLITE_PATH.exists():
        init_sqlite()

    dataset = materialize_dataset()
    graph = union_graph(dataset)

    dest = output or KG_OUTPUT
    dest.parent.mkdir(parents=True, exist_ok=True)
    graph.serialize(dest, format="turtle")
    nquads = dest.with_suffix(".nq") if dest.suffix else KG_NQUADS
    if dest == KG_OUTPUT:
        nquads = KG_NQUADS
    dataset.serialize(nquads, format="nquads")
    print(f"Wrote {dest}")
    print(f"Wrote {nquads}")
    _print_report(graph, dataset)

    errors = _check(graph, dataset)
    if errors:
        print("Materialization checks failed:")
        for err in errors:
            print(f"  - {err}")
        return 1

    from rel2kg.shacl import validate_graph

    conforms, report, violations = validate_graph(graph)
    if not conforms:
        print(f"SHACL failed ({violations} results)")
        print(report)
        return 1

    print("R2RML mappings produced a consistent graph.")
    print("Named graphs: hr, library, registrar, vocab, identity.")
    print("Graph conforms to the campus SHACL shapes.")
    print(f"{INTEGRATED_PERSON_EMAIL} is a Person in HR, a borrower, and a student.")
    return 0
