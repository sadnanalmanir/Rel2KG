from __future__ import annotations

from pathlib import Path

from rdflib import RDF, Graph
from rdflib.namespace import SH

from rel2kg.config import KG_OUTPUT, SHAPES_PATH

SHAPE_IRIS = (
    "PersonShape",
    "EmployeeShape",
    "DepartmentShape",
    "BookShape",
    "CourseShape",
    "LoanShape",
    "EnrollmentShape",
)


def load_shapes(path: Path | None = None) -> Graph:
    shapes_path = path or SHAPES_PATH
    if not shapes_path.is_file():
        raise FileNotFoundError(f"SHACL shapes missing: {shapes_path}")
    graph = Graph()
    graph.parse(shapes_path, format="turtle")
    return graph


def validate_graph(data: Graph, shapes: Graph | None = None) -> tuple[bool, str, int]:
    from pyshacl import validate

    shacl_graph = shapes if shapes is not None else load_shapes()
    conforms, report_graph, report_text = validate(
        data_graph=data,
        shacl_graph=shacl_graph,
        inference="none",
        abort_on_first=False,
        allow_infos=True,
        allow_warnings=False,
    )
    violations = sum(1 for _ in report_graph.subjects(RDF.type, SH.ValidationResult))
    return bool(conforms), str(report_text), violations


def validate_file(data_path: Path | None = None, shapes_path: Path | None = None) -> int:
    graph_path = data_path or KG_OUTPUT
    if not graph_path.is_file():
        print(f"Graph file missing: {graph_path}")
        print("Run `rel2kg materialize` first.")
        return 1

    data = Graph()
    data.parse(graph_path, format="turtle")
    try:
        shapes = load_shapes(shapes_path)
    except FileNotFoundError as exc:
        print(exc)
        return 1

    conforms, report, violations = validate_graph(data, shapes)
    print("Rel2KG — SHACL")
    print("=" * 40)
    print(f"data     {graph_path}")
    print(f"shapes   {shapes_path or SHAPES_PATH}")
    print(f"conforms {conforms}")
    print(f"results  {violations}")
    print()
    if not conforms:
        print(report)
        return 1
    print("Graph conforms to the campus SHACL shapes.")
    return 0
