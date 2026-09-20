from __future__ import annotations

import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.parse import parse_qs, urlparse

from rel2kg.config import DESK_HOST, DESK_PORT, OXIGRAPH_PUBLIC_URL, WEB_DIR
from rel2kg.expected import INTEGRATED_PERSON_EMAIL
from rel2kg.iris import person_iri
from rel2kg.sparql import (
    bindings_to_rows,
    ping,
    post_query,
    query_catalog,
    run_named_query,
)

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
QUERY_NAME_RE = re.compile(r"^[a-z0-9_]+$")
SOURCE_PREFIX = "https://rel2kg.example/source/"
GRAPH_PREFIX = "https://rel2kg.example/graph/"

STATIC_FILES = {
    "/": "index.html",
    "/index.html": "index.html",
    "/static/style.css": "style.css",
    "/static/app.js": "app.js",
    "/static/graph.js": "graph.js",
}

ALLOWED_MAP_GRAPHS = ("hr", "library", "registrar", "identity")

MIME = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
}


def _sparql_string(value: str) -> str:
    if not EMAIL_RE.fullmatch(value):
        raise ValueError("invalid email")
    return f'"{value}"'


def people_with_sources() -> list[dict[str, Any]]:
    payload = post_query(
        """
        PREFIX schema: <https://schema.org/>
        PREFIX rel2kg: <https://rel2kg.example/vocab#>
        SELECT DISTINCT ?email ?g WHERE {
          GRAPH ?g {
            { ?person a rel2kg:Person }
            UNION { ?loan rel2kg:borrower ?person }
            UNION { ?enrollment rel2kg:student ?person }
          }
          ?person schema:email ?email .
          FILTER(STRSTARTS(STR(?g), "https://rel2kg.example/graph/"))
          FILTER(!CONTAINS(STR(?g), "/vocab"))
        }
        ORDER BY ?email ?g
        """
    )
    rows = bindings_to_rows(payload)
    grouped: dict[str, list[str]] = {}
    if rows and "g" in rows[0]:
        for row in rows:
            email = row["email"]
            source = row["g"].removeprefix(GRAPH_PREFIX)
            grouped.setdefault(email, [])
            if source not in grouped[email]:
                grouped[email].append(source)
    else:
        payload = post_query(
            """
            PREFIX schema: <https://schema.org/>
            PREFIX dcterms: <http://purl.org/dc/terms/>
            PREFIX rel2kg: <https://rel2kg.example/vocab#>
            SELECT DISTINCT ?email ?source WHERE {
              ?person a rel2kg:Person ; schema:email ?email .
              {
                ?person dcterms:source ?source .
              } UNION {
                ?loan rel2kg:borrower ?person .
                BIND(<https://rel2kg.example/source/library> AS ?source)
              } UNION {
                ?enrollment rel2kg:student ?person .
                BIND(<https://rel2kg.example/source/registrar> AS ?source)
              }
            }
            ORDER BY ?email ?source
            """
        )
        for row in bindings_to_rows(payload):
            email = row["email"]
            source = row["source"].removeprefix(SOURCE_PREFIX)
            grouped.setdefault(email, [])
            if source not in grouped[email]:
                grouped[email].append(source)
    link_rows = bindings_to_rows(
        post_query(
            """
            PREFIX owl: <http://www.w3.org/2002/07/owl#>
            PREFIX schema: <https://schema.org/>
            SELECT ?email ?other WHERE {
              ?a schema:email ?email .
              ?a (owl:sameAs|^owl:sameAs) ?b .
              ?b schema:email ?other .
            }
            """
        )
    )
    for row in link_rows:
        left, right = row["email"], row["other"]
        if left in grouped and right in grouped:
            for slug in grouped[right]:
                if slug not in grouped[left]:
                    grouped[left].append(slug)
    return [
        {
            "email": email,
            "iri": str(person_iri(email)),
            "sources": sources,
            "integrated": set(sources) >= {"hr", "library", "registrar"},
        }
        for email, sources in grouped.items()
    ]


def _identity_cluster(email: str) -> list[str]:
    quoted = _sparql_string(email)
    rows = bindings_to_rows(
        post_query(
            f"""
            PREFIX owl: <http://www.w3.org/2002/07/owl#>
            PREFIX schema: <https://schema.org/>
            SELECT DISTINCT ?email WHERE {{
              ?seed schema:email {quoted} .
              {{
                BIND({quoted} AS ?email)
              }} UNION {{
                ?seed (owl:sameAs|^owl:sameAs)+ ?other .
                ?other schema:email ?email .
              }}
            }}
            """
        )
    )
    found = [row["email"] for row in rows]
    return found or [email]


def _email_values(emails: list[str]) -> str:
    return " ".join(_sparql_string(item) for item in emails)


def person_card(email: str) -> dict[str, Any]:
    cluster = _identity_cluster(email)
    values = _email_values(cluster)
    core = post_query(
        f"""
        PREFIX foaf: <http://xmlns.com/foaf/0.1/>
        PREFIX schema: <https://schema.org/>
        PREFIX dcterms: <http://purl.org/dc/terms/>
        PREFIX rel2kg: <https://rel2kg.example/vocab#>
        SELECT ?given ?family ?fullName ?hiredOn ?deptName ?deptCode ?source
        WHERE {{
          VALUES ?em {{ {values} }}
          ?person schema:email ?em .
          OPTIONAL {{ ?person foaf:givenName ?given }}
          OPTIONAL {{ ?person foaf:familyName ?family }}
          OPTIONAL {{ ?person foaf:name ?fullName }}
          OPTIONAL {{ ?person rel2kg:hiredOn ?hiredOn }}
          OPTIONAL {{
            ?person rel2kg:memberOf ?dept .
            ?dept schema:name ?deptName ;
                  rel2kg:code ?deptCode .
          }}
          OPTIONAL {{ ?person dcterms:source ?source }}
        }}
        """
    )
    rows = bindings_to_rows(core)
    if not rows:
        raise FileNotFoundError(email)

    sources: list[str] = []
    given = family = full_name = hired = dept_name = dept_code = ""
    for row in rows:
        given = given or row.get("given", "")
        family = family or row.get("family", "")
        full_name = full_name or row.get("fullName", "")
        hired = hired or row.get("hiredOn", "")
        dept_name = dept_name or row.get("deptName", "")
        dept_code = dept_code or row.get("deptCode", "")
        slug = row.get("source", "").removeprefix(SOURCE_PREFIX)
        if slug and slug not in sources:
            sources.append(slug)

    loans = bindings_to_rows(
        post_query(
            f"""
            PREFIX schema: <https://schema.org/>
            PREFIX rel2kg: <https://rel2kg.example/vocab#>
            SELECT ?title ?isbn ?loanedOn ?returnedOn WHERE {{
              VALUES ?em {{ {values} }}
              ?person schema:email ?em .
              ?loan rel2kg:borrower ?person ;
                    rel2kg:borrowed ?book ;
                    rel2kg:loanedOn ?loanedOn .
              OPTIONAL {{ ?loan rel2kg:returnedOn ?returnedOn }}
              ?book schema:name ?title .
              OPTIONAL {{ ?book schema:isbn ?isbn }}
            }}
            ORDER BY ?loanedOn
            """
        )
    )
    authored = bindings_to_rows(
        post_query(
            f"""
            PREFIX schema: <https://schema.org/>
            SELECT ?title ?isbn WHERE {{
              VALUES ?em {{ {values} }}
              ?person schema:email ?em .
              ?book schema:author ?person ;
                    schema:name ?title .
              OPTIONAL {{ ?book schema:isbn ?isbn }}
            }}
            ORDER BY ?title
            """
        )
    )
    enrollments = bindings_to_rows(
        post_query(
            f"""
            PREFIX schema: <https://schema.org/>
            PREFIX rel2kg: <https://rel2kg.example/vocab#>
            SELECT ?title ?code ?term ?grade WHERE {{
              VALUES ?em {{ {values} }}
              ?person schema:email ?em .
              ?enrollment rel2kg:student ?person ;
                          rel2kg:course ?course ;
                          rel2kg:term ?term .
              OPTIONAL {{ ?enrollment rel2kg:grade ?grade }}
              ?course schema:name ?title ;
                      schema:courseCode ?code .
            }}
            ORDER BY ?term ?code
            """
        )
    )
    display = " ".join(part for part in (given, family) if part) or full_name or email
    if (loans or authored) and "library" not in sources:
        sources.append("library")
    if enrollments and "registrar" not in sources:
        sources.append("registrar")
    aliases = [item for item in cluster if item != email]
    return {
        "ok": True,
        "email": email,
        "iri": str(person_iri(email)),
        "display": display,
        "given": given,
        "family": family,
        "full_name": full_name,
        "aliases": aliases,
        "sources": sources,
        "integrated": set(sources) >= {"hr", "library", "registrar"},
        "hr": {
            "present": "hr" in sources or bool(given or dept_name),
            "given": given,
            "family": family,
            "hired_on": hired,
            "department": dept_name,
            "code": dept_code,
        },
        "library": {
            "present": "library" in sources or bool(loans or authored),
            "name": full_name,
            "loans": loans,
            "authored": authored,
        },
        "registrar": {
            "present": "registrar" in sources or bool(enrollments),
            "enrollments": enrollments,
        },
    }


def parse_map_graphs(raw: str) -> list[str]:
    parts = [item.strip().lower() for item in raw.split(",") if item.strip()]
    if not parts:
        return list(ALLOWED_MAP_GRAPHS)
    unknown = [item for item in parts if item not in ALLOWED_MAP_GRAPHS]
    if unknown:
        raise ValueError(f"unknown graph: {', '.join(unknown)}")
    seen: list[str] = []
    for item in parts:
        if item not in seen:
            seen.append(item)
    return seen


def _kind_from_iri(iri: str) -> str:
    if "/id/person/" in iri:
        return "person"
    if "/id/department/" in iri:
        return "department"
    if "/id/book/" in iri:
        return "book"
    if "/id/course/" in iri:
        return "course"
    return "entity"


def _person_label(row: dict[str, str]) -> str:
    composed = " ".join(part for part in (row.get("gn"), row.get("fn")) if part).strip()
    return composed or row.get("nm") or row.get("email") or row["iri"].rsplit("/", 1)[-1]


def map_graph(slugs: list[str]) -> dict[str, Any]:
    values = " ".join(f"<{GRAPH_PREFIX}{slug}>" for slug in slugs)
    node_rows = bindings_to_rows(
        post_query(
            f"""
            PREFIX foaf: <http://xmlns.com/foaf/0.1/>
            PREFIX schema: <https://schema.org/>
            PREFIX rel2kg: <https://rel2kg.example/vocab#>
            SELECT ?iri ?kind ?email ?gn ?fn ?nm ?name ?code ?g WHERE {{
              VALUES ?g {{ {values} }}
              GRAPH ?g {{
                {{
                  ?iri a rel2kg:Person .
                  BIND("person" AS ?kind)
                  OPTIONAL {{ ?iri schema:email ?email }}
                  OPTIONAL {{ ?iri foaf:givenName ?gn }}
                  OPTIONAL {{ ?iri foaf:familyName ?fn }}
                  OPTIONAL {{ ?iri foaf:name ?nm }}
                }} UNION {{
                  ?iri a rel2kg:Department ; schema:name ?name .
                  BIND("department" AS ?kind)
                  OPTIONAL {{ ?iri rel2kg:code ?code }}
                }} UNION {{
                  ?iri a rel2kg:Book ; schema:name ?name .
                  BIND("book" AS ?kind)
                }} UNION {{
                  ?iri a rel2kg:Course ; schema:name ?name .
                  BIND("course" AS ?kind)
                  OPTIONAL {{ ?iri schema:courseCode ?code }}
                }}
              }}
            }}
            """
        )
    )
    edge_rows = bindings_to_rows(
        post_query(
            f"""
            PREFIX schema: <https://schema.org/>
            PREFIX rel2kg: <https://rel2kg.example/vocab#>
            SELECT ?from ?to ?kind ?g WHERE {{
              VALUES ?g {{ {values} }}
              GRAPH ?g {{
                {{ ?from rel2kg:memberOf ?to . BIND("memberOf" AS ?kind) }}
                UNION {{ ?to schema:author ?from . BIND("author" AS ?kind) }}
                UNION {{
                  ?loan rel2kg:borrower ?from ; rel2kg:borrowed ?to .
                  BIND("borrowed" AS ?kind)
                }}
                UNION {{
                  ?enrollment rel2kg:student ?from ; rel2kg:course ?to .
                  BIND("enrolled" AS ?kind)
                }}
              }}
            }}
            """
        )
    )

    nodes: dict[str, dict[str, Any]] = {}
    for row in node_rows:
        iri = row["iri"]
        slug = row["g"].removeprefix(GRAPH_PREFIX)
        node = nodes.setdefault(
            iri,
            {
                "id": iri,
                "kind": row["kind"],
                "label": "",
                "email": row.get("email") or "",
                "graphs": [],
            },
        )
        if row["kind"] == "person":
            node["label"] = node["label"] or _person_label(row)
            node["email"] = node["email"] or row.get("email") or ""
        else:
            node["label"] = (
                node["label"] or row.get("name") or row.get("code") or iri.rsplit("/", 1)[-1]
            )
        if slug and slug not in node["graphs"]:
            node["graphs"].append(slug)

    edges: list[dict[str, str]] = []
    seen_edges: set[tuple[str, str, str, str]] = set()
    for row in edge_rows:
        frm, to, kind = row["from"], row["to"], row["kind"]
        slug = row["g"].removeprefix(GRAPH_PREFIX)
        key = (frm, to, kind, slug)
        if key in seen_edges:
            continue
        seen_edges.add(key)
        for iri in (frm, to):
            if iri not in nodes:
                nodes[iri] = {
                    "id": iri,
                    "kind": _kind_from_iri(iri),
                    "label": iri.rsplit("/", 1)[-1],
                    "email": "",
                    "graphs": [slug] if slug else [],
                }
            elif slug and slug not in nodes[iri]["graphs"]:
                nodes[iri]["graphs"].append(slug)
        edges.append({"source": frm, "target": to, "kind": kind, "graph": slug})

    if "identity" in slugs:
        for row in bindings_to_rows(
            post_query(
                """
                PREFIX owl: <http://www.w3.org/2002/07/owl#>
                SELECT ?from ?to WHERE {
                  GRAPH <https://rel2kg.example/graph/identity> {
                    ?from owl:sameAs ?to .
                  }
                }
                """
            )
        ):
            frm, to = row["from"], row["to"]
            key = (frm, to, "sameAs", "identity")
            if key in seen_edges:
                continue
            seen_edges.add(key)
            for iri in (frm, to):
                if iri not in nodes:
                    nodes[iri] = {
                        "id": iri,
                        "kind": "person",
                        "label": iri.rsplit("/", 1)[-1],
                        "email": "",
                        "graphs": ["identity"],
                    }
                elif "identity" not in nodes[iri]["graphs"]:
                    nodes[iri]["graphs"].append("identity")
            edges.append({"source": frm, "target": to, "kind": "sameAs", "graph": "identity"})

    return {
        "ok": True,
        "graphs": slugs,
        "nodes": list(nodes.values()),
        "edges": edges,
    }


def health() -> dict[str, Any]:
    try:
        ping()
        payload = post_query("SELECT (COUNT(*) AS ?n) WHERE { ?s ?p ?o }")
        rows = bindings_to_rows(payload)
        triples = int(rows[0]["n"]) if rows else 0
        graph_rows = bindings_to_rows(
            post_query(
                """
                SELECT ?g (COUNT(*) AS ?n) WHERE {
                  GRAPH ?g { ?s ?p ?o }
                }
                GROUP BY ?g
                ORDER BY ?g
                """
            )
        )
        graphs = [
            {
                "iri": row["g"],
                "name": row["g"].rsplit("/", 1)[-1],
                "triples": int(row["n"]),
            }
            for row in graph_rows
        ]
        return {
            "ok": True,
            "triples": triples,
            "graphs": graphs,
            "oxigraph": OXIGRAPH_PUBLIC_URL,
            "focus_email": INTEGRATED_PERSON_EMAIL,
            "empty": triples == 0,
        }
    except (RuntimeError, URLError, TimeoutError, OSError) as exc:
        return {
            "ok": False,
            "triples": 0,
            "graphs": [],
            "oxigraph": OXIGRAPH_PUBLIC_URL,
            "focus_email": INTEGRATED_PERSON_EMAIL,
            "empty": True,
            "error": str(exc),
        }


def _json(handler: BaseHTTPRequestHandler, code: int, payload: dict[str, Any]) -> None:
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(code)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(body)


def _file(handler: BaseHTTPRequestHandler, relative: str) -> None:
    path = (WEB_DIR / relative).resolve()
    if WEB_DIR.resolve() not in path.parents and path != WEB_DIR.resolve():
        handler.send_error(403)
        return
    if not path.is_file():
        handler.send_error(404)
        return
    data = path.read_bytes()
    handler.send_response(200)
    handler.send_header("Content-Type", MIME.get(path.suffix, "application/octet-stream"))
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


class DeskHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        print(f"desk: {self.address_string()} {args[0]}")

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        if path in STATIC_FILES:
            _file(self, STATIC_FILES[path])
            return
        if path == "/api/health":
            payload = health()
            _json(self, 200 if payload["ok"] else 503, payload)
            return
        if path == "/api/queries":
            _json(self, 200, {"ok": True, "queries": query_catalog()})
            return
        if path == "/api/graph":
            raw = parse_qs(parsed.query).get("graphs", [""])[0]
            try:
                slugs = parse_map_graphs(raw)
                _json(self, 200, map_graph(slugs))
            except ValueError as exc:
                _json(self, 400, {"ok": False, "error": str(exc)})
            except Exception as exc:
                _json(self, 503, {"ok": False, "error": str(exc)})
            return
        if path == "/api/people":
            try:
                _json(self, 200, {"ok": True, "people": people_with_sources()})
            except Exception as exc:
                _json(self, 503, {"ok": False, "error": str(exc)})
            return
        if path == "/api/person":
            email = parse_qs(parsed.query).get("email", [""])[0]
            try:
                _json(self, 200, person_card(email))
            except ValueError:
                _json(self, 400, {"ok": False, "error": "invalid email"})
            except FileNotFoundError:
                _json(self, 404, {"ok": False, "error": "unknown person"})
            except Exception as exc:
                _json(self, 503, {"ok": False, "error": str(exc)})
            return
        if path.startswith("/api/query/"):
            name = path.removeprefix("/api/query/")
            if not QUERY_NAME_RE.fullmatch(name):
                _json(self, 400, {"ok": False, "error": "invalid query name"})
                return
            try:
                _json(self, 200, run_named_query(name))
            except FileNotFoundError:
                _json(self, 404, {"ok": False, "error": "unknown query"})
            except Exception as exc:
                _json(self, 503, {"ok": False, "error": str(exc)})
            return
        self.send_error(404)


def serve(host: str | None = None, port: int | None = None) -> int:
    bind_host = host or DESK_HOST
    bind_port = port or DESK_PORT
    if not WEB_DIR.is_dir():
        print(f"Web directory missing: {WEB_DIR}")
        return 1
    httpd = ThreadingHTTPServer((bind_host, bind_port), DeskHandler)
    print(f"Integration desk http://127.0.0.1:{bind_port}/")
    print(f"Raw SPARQL UI {OXIGRAPH_PUBLIC_URL}/")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("Stopping desk")
    finally:
        httpd.server_close()
    return 0


def web_files() -> dict[str, Path]:
    return {url: WEB_DIR / name for url, name in STATIC_FILES.items()}
