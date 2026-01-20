"""
描述: 校验工具单元测试
主要功能:
    - 日期解析与数值校验测试
依赖: unittest
"""

from __future__ import annotations

import unittest
from datetime import date
from decimal import Decimal

from cli.validation import ensure_non_negative as cli_ensure_non_negative
from cli.validation import normalize_commas as cli_normalize_commas
from cli.validation import parse_decimal
from cli.validation import parse_sign_date as cli_parse_sign_date
from services.validators import ensure_non_negative
from services.validators import normalize_commas
from services.validators import parse_sign_date


class ValidatorTests(unittest.TestCase):
    """
    校验函数测试
    """

    def test_normalize_commas(self) -> None:
        self.assertEqual(normalize_commas("a，b、c"), "a,b,c")
        self.assertEqual(cli_normalize_commas("a，b"), "a,b")

    def test_parse_sign_date_norm(self) -> None:
        raw, norm = parse_sign_date(None, date(2024, 1, 15))
        self.assertEqual(raw, "2024-01-15")
        self.assertEqual(norm, date(2024, 1, 15))

    def test_parse_sign_date_raw(self) -> None:
        raw, norm = parse_sign_date("2024年02月15日", None)
        self.assertEqual(raw, "2024年02月15日")
        self.assertEqual(norm, date(2024, 2, 15))

        raw_cli, norm_cli = cli_parse_sign_date("2024-03-01", None)
        self.assertEqual(raw_cli, "2024-03-01")
        self.assertEqual(norm_cli, date(2024, 3, 1))

    def test_ensure_non_negative(self) -> None:
        ensure_non_negative(Decimal("0"), "amount")
        cli_ensure_non_negative(Decimal("1"), "amount")
        with self.assertRaises(ValueError):
            ensure_non_negative(Decimal("-1"), "amount")

    def test_parse_decimal(self) -> None:
        self.assertEqual(parse_decimal("5.5", "amount"), Decimal("5.5"))
        with self.assertRaises(ValueError):
            parse_decimal("bad", "amount")


if __name__ == "__main__":
    unittest.main()
