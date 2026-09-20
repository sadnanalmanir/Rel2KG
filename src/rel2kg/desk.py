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

STATIC_FILES = {
    "/": "index.html",
    "/index.html": "index.html",
    "/static/style.css": "style.css",
    "/static/app.js": "app.js",
}

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
    grouped: dict[str, list[str]] = {}
    for row in bindings_to_rows(payload):
        email = row["email"]
        source = row["source"].removeprefix(SOURCE_PREFIX)
        grouped.setdefault(email, [])
        if source not in grouped[email]:
            grouped[email].append(source)
    return [
        {
            "email": email,
            "iri": str(person_iri(email)),
            "sources": sources,
            "integrated": set(sources) >= {"hr", "library", "registrar"},
        }
        for email, sources in grouped.items()
    ]


def person_card(email: str) -> dict[str, Any]:
    quoted = _sparql_string(email)
    core = post_query(
        f"""
        PREFIX foaf: <http://xmlns.com/foaf/0.1/>
        PREFIX schema: <https://schema.org/>
        PREFIX dcterms: <http://purl.org/dc/terms/>
        PREFIX rel2kg: <https://rel2kg.example/vocab#>
        SELECT ?given ?family ?fullName ?hiredOn ?deptName ?deptCode ?source
        WHERE {{
          ?person schema:email {quoted} .
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
              ?person schema:email {quoted} .
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
    enrollments = bindings_to_rows(
        post_query(
            f"""
            PREFIX schema: <https://schema.org/>
            PREFIX rel2kg: <https://rel2kg.example/vocab#>
            SELECT ?title ?code ?term ?grade WHERE {{
              ?person schema:email {quoted} .
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
    if loans and "library" not in sources:
        sources.append("library")
    if enrollments and "registrar" not in sources:
        sources.append("registrar")
    return {
        "ok": True,
        "email": email,
        "iri": str(person_iri(email)),
        "display": display,
        "given": given,
        "family": family,
        "full_name": full_name,
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
            "present": "library" in sources or bool(loans),
            "name": full_name,
            "loans": loans,
        },
        "registrar": {
            "present": "registrar" in sources or bool(enrollments),
            "enrollments": enrollments,
        },
    }


def health() -> dict[str, Any]:
    try:
        ping()
        payload = post_query("SELECT (COUNT(*) AS ?n) WHERE { ?s ?p ?o }")
        rows = bindings_to_rows(payload)
        triples = int(rows[0]["n"]) if rows else 0
        return {
            "ok": True,
            "triples": triples,
            "oxigraph": OXIGRAPH_PUBLIC_URL,
            "focus_email": INTEGRATED_PERSON_EMAIL,
            "empty": triples == 0,
        }
    except (RuntimeError, URLError, TimeoutError, OSError) as exc:
        return {
            "ok": False,
            "triples": 0,
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
