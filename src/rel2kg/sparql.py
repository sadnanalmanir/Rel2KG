from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from rel2kg.config import KG_OUTPUT, OXIGRAPH_URL, QUERIES_DIR
from rel2kg.db import wait_for
from rel2kg.expected import EXPECTED_ASK, EXPECTED_SELECT_ROWS


def _url(path: str) -> str:
    return f"{OXIGRAPH_URL.rstrip('/')}{path}"


def _request(
    path: str,
    *,
    method: str = "GET",
    data: bytes | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 30,
) -> tuple[int, bytes, str]:
    req = Request(_url(path), data=data, method=method, headers=headers or {})
    with urlopen(req, timeout=timeout) as resp:
        body = resp.read()
        content_type = resp.headers.get("Content-Type", "")
        return resp.status, body, content_type


def ping() -> None:
    status, _, _ = _request("/")
    if status >= 400:
        raise RuntimeError(f"Oxigraph returned HTTP {status}")


def wait_for_oxigraph() -> None:
    wait_for("Oxigraph", ping)


def load_graph(path: Path | None = None) -> int:
    graph_path = path or KG_OUTPUT
    if not graph_path.is_file():
        print(f"Graph file missing: {graph_path}")
        print("Run `rel2kg materialize` first.")
        return 1

    wait_for_oxigraph()
    data = graph_path.read_bytes()
    try:
        status, _, _ = _request(
            "/store?default",
            method="PUT",
            data=data,
            headers={"Content-Type": "text/turtle; charset=utf-8"},
        )
    except HTTPError as exc:
        print(f"Oxigraph rejected the graph: HTTP {exc.code} {exc.reason}")
        return 1
    except URLError as exc:
        print(f"Cannot reach Oxigraph at {OXIGRAPH_URL}: {exc.reason}")
        return 1

    count = _triple_count()
    print(f"Loaded {graph_path} into {OXIGRAPH_URL}/store?default (HTTP {status})")
    print(f"Default graph triples: {count}")
    print(f"SPARQL UI: {OXIGRAPH_URL}/")
    return 0


def _triple_count() -> int:
    payload = post_query("SELECT (COUNT(*) AS ?n) WHERE { ?s ?p ?o }")
    bindings = payload.get("results", {}).get("bindings", [])
    if not bindings:
        return 0
    return int(bindings[0]["n"]["value"])


def post_query(sparql: str) -> dict[str, Any]:
    wait_for_oxigraph()
    try:
        _, body, _ = _request(
            "/query",
            method="POST",
            data=sparql.encode("utf-8"),
            headers={
                "Content-Type": "application/sparql-query; charset=utf-8",
                "Accept": "application/sparql-results+json",
            },
        )
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"SPARQL failed: HTTP {exc.code}\n{detail}") from exc
    return json.loads(body.decode("utf-8"))


def resolve_query(name: str) -> Path:
    candidate = Path(name)
    if candidate.is_file():
        return candidate
    in_dir = QUERIES_DIR / name
    if in_dir.is_file():
        return in_dir
    if not name.endswith(".rq"):
        with_ext = QUERIES_DIR / f"{name}.rq"
        if with_ext.is_file():
            return with_ext
    raise FileNotFoundError(f"SPARQL query not found: {name}")


def list_queries() -> list[Path]:
    return sorted(QUERIES_DIR.glob("*.rq"))


def query_title(path: Path) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            title = stripped.lstrip("#").strip()
            if title:
                return title.split("Expected:")[0].strip().rstrip(".")
    return path.stem.replace("_", " ")


def query_catalog() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for path in list_queries():
        kind = "ask" if path.stem in EXPECTED_ASK else "select"
        items.append(
            {
                "name": path.stem,
                "file": path.name,
                "title": query_title(path),
                "kind": kind,
                "expected_rows": EXPECTED_SELECT_ROWS.get(path.stem),
                "expected_ask": EXPECTED_ASK.get(path.stem),
            }
        )
    return items


def bindings_to_rows(payload: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in payload.get("results", {}).get("bindings", []):
        rows.append({key: cell.get("value", "") for key, cell in row.items()})
    return rows


def run_named_query(name: str) -> dict[str, Any]:
    path = resolve_query(name)
    sparql = path.read_text(encoding="utf-8")
    payload = post_query(sparql)
    if "boolean" in payload:
        return {
            "ok": True,
            "name": path.stem,
            "kind": "ask",
            "boolean": bool(payload["boolean"]),
            "rows": [],
            "sparql": sparql,
        }
    rows = bindings_to_rows(payload)
    return {
        "ok": True,
        "name": path.stem,
        "kind": "select",
        "boolean": None,
        "vars": payload.get("head", {}).get("vars", []),
        "rows": rows,
        "sparql": sparql,
    }


def _print_select(payload: dict[str, Any]) -> int:
    variables = payload.get("head", {}).get("vars", [])
    rows = payload.get("results", {}).get("bindings", [])
    print("\t".join(variables))
    for row in rows:
        cells = [row.get(var, {}).get("value", "") for var in variables]
        print("\t".join(cells))
    return len(rows)


def _print_ask(payload: dict[str, Any]) -> bool:
    value = bool(payload.get("boolean"))
    print("true" if value else "false")
    return value


def _check(stem: str, n_rows: int | None, ask: bool | None) -> str | None:
    if stem in EXPECTED_ASK:
        expected = EXPECTED_ASK[stem]
        if ask is None:
            return f"{stem}: expected ASK, got SELECT"
        if ask is not expected:
            return f"{stem}: expected ASK {expected}, got {ask}"
        return None
    if stem in EXPECTED_SELECT_ROWS:
        expected = EXPECTED_SELECT_ROWS[stem]
        if n_rows is None:
            return f"{stem}: expected SELECT, got ASK"
        if n_rows != expected:
            return f"{stem}: expected {expected} rows, got {n_rows}"
        return None
    return None


def run_one(path: Path, *, check: bool) -> str | None:
    sparql = path.read_text(encoding="utf-8")
    payload = post_query(sparql)
    print(f"=== {path.stem} ===")
    if "boolean" in payload:
        ask = _print_ask(payload)
        print()
        return _check(path.stem, None, ask) if check else None
    n_rows = _print_select(payload)
    print(f"({n_rows} rows)")
    print()
    return _check(path.stem, n_rows, None) if check else None


def query(names: list[str], *, check: bool) -> int:
    if names:
        try:
            paths = [resolve_query(name) for name in names]
        except FileNotFoundError as exc:
            print(exc)
            return 1
    else:
        paths = list_queries()
        if not paths:
            print(f"No SPARQL files in {QUERIES_DIR}")
            return 1

    errors: list[str] = []
    for path in paths:
        try:
            err = run_one(path, check=check)
        except RuntimeError as exc:
            print(exc)
            return 1
        if err:
            errors.append(err)

    if errors:
        print("SPARQL checks failed:")
        for err in errors:
            print(f"  - {err}")
        return 1
    if check:
        print("All SPARQL competency questions passed.")
    return 0
