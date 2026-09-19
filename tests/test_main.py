from __future__ import annotations

import unittest
from contextlib import redirect_stderr
from io import StringIO
from unittest.mock import patch

from rel2kg.__main__ import build_parser, main


class TestMain(unittest.TestCase):
    def test_parser_defaults_to_bootstrap(self) -> None:
        args = build_parser().parse_args([])
        self.assertIsNone(args.command)

    def test_parser_accepts_verify(self) -> None:
        args = build_parser().parse_args(["verify"])
        self.assertEqual(args.command, "verify")

    def test_unknown_command_exits(self) -> None:
        with redirect_stderr(StringIO()), self.assertRaises(SystemExit) as cm:
            main(["nope"])
        self.assertEqual(cm.exception.code, 2)

    def test_init_sqlite_dispatches(self) -> None:
        with patch("rel2kg.__main__.init_sqlite") as init:
            code = main(["init-sqlite"])
        self.assertEqual(code, 0)
        init.assert_called_once()


class TestExpected(unittest.TestCase):
    def test_table_groups_cover_counts(self) -> None:
        from rel2kg.expected import (
            EXPECTED_ROW_COUNTS,
            MYSQL_TABLES,
            POSTGRES_TABLES,
            SQLITE_TABLES,
        )

        grouped = POSTGRES_TABLES + MYSQL_TABLES + SQLITE_TABLES
        self.assertEqual(set(grouped), set(EXPECTED_ROW_COUNTS))
        self.assertEqual(len(grouped), len(EXPECTED_ROW_COUNTS))
