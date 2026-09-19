from __future__ import annotations

import argparse
import sys

from rel2kg import __version__
from rel2kg.init_sqlite import init_sqlite
from rel2kg.verify import verify


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rel2kg",
        description="Instantiate and verify the Rel2KG relational sources.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("bootstrap", help="create SQLite and verify all three sources")
    sub.add_parser("init-sqlite", help="create and seed the SQLite registrar")
    sub.add_parser("verify", help="check PostgreSQL, MySQL, and SQLite")
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

    build_parser().print_help(sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
