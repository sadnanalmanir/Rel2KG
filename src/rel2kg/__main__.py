from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rel2kg import __version__
from rel2kg.init_sqlite import init_sqlite
from rel2kg.verify import verify


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rel2kg",
        description="Relational sources, R2RML mappings, and SPARQL over the graph.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("bootstrap", help="create SQLite and verify all three sources")
    sub.add_parser("init-sqlite", help="create and seed the SQLite registrar")
    sub.add_parser("verify", help="check PostgreSQL, MySQL, and SQLite")
    materialize = sub.add_parser(
        "materialize",
        help="apply R2RML mappings and write a Turtle graph",
    )
    materialize.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Turtle output path (default: $KG_OUTPUT or data/kg.ttl)",
    )
    materialize.add_argument(
        "--load",
        action="store_true",
        help="also PUT the graph into Oxigraph",
    )
    load = sub.add_parser("load", help="PUT the Turtle graph into Oxigraph")
    load.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Turtle file to load (default: $KG_OUTPUT)",
    )
    query = sub.add_parser("query", help="run SPARQL against Oxigraph")
    query.add_argument(
        "names",
        nargs="*",
        help="query file names or paths (default: all files in queries/)",
    )
    query.add_argument(
        "--check",
        action="store_true",
        help="fail if result sizes do not match expected.py",
    )
    serve = sub.add_parser("serve", help="run the integration desk HTTP UI")
    serve.add_argument("--host", default=None, help="bind address (default 0.0.0.0)")
    serve.add_argument("--port", type=int, default=None, help="bind port (default 8765)")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    command = args.command or "bootstrap"

    if command == "init-sqlite":
        init_sqlite()
        return 0
    if command == "verify":
        return verify()
    if command == "bootstrap":
        init_sqlite()
        return verify()
    if command == "materialize":
        from rel2kg.materialize import materialize

        code = materialize(args.output)
        if code != 0 or not args.load:
            return code
        from rel2kg.sparql import load_graph

        return load_graph(args.output)
    if command == "load":
        from rel2kg.sparql import load_graph

        return load_graph(args.output)
    if command == "query":
        from rel2kg.sparql import query

        return query(args.names, check=args.check)
    if command == "serve":
        from rel2kg.desk import serve

        return serve(args.host, args.port)

    build_parser().print_help(sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
