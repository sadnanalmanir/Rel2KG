from __future__ import annotations

from pathlib import Path
from urllib.parse import quote_plus

from rdflib import RDF, RDFS, Graph, URIRef

from rel2kg.config import (
    KG_OUTPUT,
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
    EXPECTED_PERSON_COUNT,
    INTEGRATED_PERSON_EMAIL,
)
from rel2kg.iris import (
    DCTERMS,
    FOAF,
    SCHEMA,
    VOCAB,
    book_iri,
    course_iri,
    department_iri,
    person_iri,
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


def morph_config() -> str:
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
    graph.bind("rdfs", RDFS)


def _count_type(graph: Graph, class_iri: URIRef) -> int:
    return sum(1 for _ in graph.subjects(RDF.type, class_iri))


def _check(graph: Graph) -> list[str]:
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

    return errors


def _print_report(graph: Graph) -> None:
    print("Rel2KG — R2RML materialization")
    print("=" * 40)
    print(f"triples      {len(graph)}")
    print(f"Person       {_count_type(graph, VOCAB.Person)}")
    print(f"Department   {_count_type(graph, VOCAB.Department)}")
    print(f"Book         {_count_type(graph, VOCAB.Book)}")
    print(f"Course       {_count_type(graph, VOCAB.Course)}")
    print(f"Loan         {_count_type(graph, VOCAB.Loan)}")
    print(f"Enrollment   {_count_type(graph, VOCAB.Enrollment)}")
    print()


def materialize(output: Path | None = None) -> int:
    import morph_kgc

    from rel2kg.init_sqlite import init_sqlite

    if not SQLITE_PATH.exists():
        init_sqlite()

    graph = morph_kgc.materialize(morph_config())
    if VOCAB_PATH.is_file():
        graph.parse(VOCAB_PATH, format="turtle")
    _bind(graph)

    dest = output or KG_OUTPUT
    dest.parent.mkdir(parents=True, exist_ok=True)
    graph.serialize(dest, format="turtle")
    print(f"Wrote {dest}")
    _print_report(graph)

    errors = _check(graph)
    if errors:
        print("Materialization checks failed:")
        for err in errors:
            print(f"  - {err}")
        return 1

    print("R2RML mappings produced a consistent graph.")
    print(f"{INTEGRATED_PERSON_EMAIL} is a Person in HR, a borrower, and a student.")
    return 0
