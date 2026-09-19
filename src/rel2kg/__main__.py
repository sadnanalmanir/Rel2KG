from __future__ import annotations

import sys

from rel2kg.init_sqlite import init_sqlite
from rel2kg.verify import verify

USAGE = "usage: python -m rel2kg [bootstrap|init-sqlite|verify]"


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    cmd = args[0] if args else "bootstrap"

    if cmd == "init-sqlite":
        init_sqlite()
        return 0
    if cmd == "verify":
        return verify()
    if cmd == "bootstrap":
        init_sqlite()
        return verify()

    print(USAGE, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
