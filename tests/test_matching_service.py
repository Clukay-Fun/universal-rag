"""
描述: 智能匹配服务单元测试
主要功能:
    - 约束条件解析测试
    - SQL 过滤构建测试
    - Schema 验证测试
依赖: unittest
"""

from __future__ import annotations

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

import unittest
from decimal import Decimal
from typing import Any

from schemas.matching import (
    ContractMatchCreate,
    TenderRequirementCreate,
)
from services.matching_service import _build_filter_sql


# ============================================
# region SQL过滤构建测试
# ============================================
class BuildFilterSqlTests(unittest.TestCase):
    """
    SQL WHERE 子句构建测试
    """

    def test_empty_constraints(self) -> None:
        """空约束条件应返回 1=1"""
        where, params = _build_filter_sql({})
        self.assertEqual(where, "1=1")
        self.assertEqual(params, [])

    def test_project_types_filter(self) -> None:
        """项目类型过滤"""
        constraints = {"project_types": ["诉讼", "常法"]}
        where, params = _build_filter_sql(constraints)
        self.assertIn("project_type IN", where)
        self.assertEqual(params, ["诉讼", "常法"])

    def test_amount_range_filter(self) -> None:
        """金额区间过滤"""
        constraints = {"min_amount": 10, "max_amount": 100}
        where, params = _build_filter_sql(constraints)
        self.assertIn("amount >=", where)
        self.assertIn("amount <=", where)
        self.assertEqual(len(params), 2)

    def test_date_range_filter(self) -> None:
        """日期范围过滤"""
        constraints = {"date_after": "2023-01-01", "date_before": "2024-12-31"}
        where, params = _build_filter_sql(constraints)
        self.assertIn("sign_date_norm >=", where)
        self.assertIn("sign_date_norm <=", where)

    def test_state_owned_filter(self) -> None:
        """国企过滤"""
        constraints = {"require_state_owned": True}
        where, params = _build_filter_sql(constraints)
        self.assertIn("is_state_owned = TRUE", where)

    def test_combined_filters(self) -> None:
        """组合过滤条件"""
        constraints = {
            "project_types": ["诉讼"],
            "min_amount": 50,
            "date_after": "2022-01-01",
        }
        where, params = _build_filter_sql(constraints)
        self.assertIn(" AND ", where)
        self.assertEqual(len(params), 3)
# endregion
# ============================================


# ============================================
# region Schema验证测试
# ============================================
class SchemaValidationTests(unittest.TestCase):
    """
    Pydantic Schema 验证测试
    """

    def test_tender_requirement_create(self) -> None:
        """招标需求创建 Schema"""
        data = TenderRequirementCreate(
            title="测试招标",
            raw_text="这是一段招标原文",
        )
        self.assertEqual(data.title, "测试招标")
        self.assertEqual(data.raw_text, "这是一段招标原文")
        self.assertEqual(data.constraints, {})

    def test_tender_requirement_with_constraints(self) -> None:
        """招标需求带约束条件"""
        data = TenderRequirementCreate(
            title="测试招标",
            raw_text="这是一段招标原文",
            constraints={"min_amount": 10, "project_types": ["诉讼"]},
        )
        self.assertEqual(data.constraints["min_amount"], 10)

    def test_contract_match_create_valid(self) -> None:
        """匹配结果创建 Schema - 有效得分"""
        data = ContractMatchCreate(
            tender_id=1,
            contract_id=100,
            score=Decimal("0.85"),
            reasons=["项目类型匹配", "金额符合"],
        )
        self.assertEqual(data.score, Decimal("0.85"))
        self.assertEqual(len(data.reasons), 2)

    def test_contract_match_create_score_validation(self) -> None:
        """匹配结果创建 Schema - 得分范围校验"""
        # 得分超过 1 应该报错
        with self.assertRaises(ValueError):
            ContractMatchCreate(
                tender_id=1,
                contract_id=100,
                score=Decimal("1.5"),
                reasons=[],
            )

        # 负分应该报错
        with self.assertRaises(ValueError):
            ContractMatchCreate(
                tender_id=1,
                contract_id=100,
                score=Decimal("-0.1"),
                reasons=[],
            )
# endregion
# ============================================


# ============================================
# region 约束条件解析测试
# ============================================
class ConstraintsParsingTests(unittest.TestCase):
    """
    约束条件解析相关测试
    """

    def test_empty_project_types_ignored(self) -> None:
        """空项目类型列表应被忽略"""
        constraints: dict[str, Any] = {"project_types": []}
        where, params = _build_filter_sql(constraints)
        self.assertEqual(where, "1=1")
        self.assertEqual(params, [])

    def test_null_values_ignored(self) -> None:
        """None 值应被忽略"""
        constraints: dict[str, Any] = {
            "min_amount": None,
            "max_amount": None,
            "date_after": None,
        }
        where, params = _build_filter_sql(constraints)
        self.assertEqual(where, "1=1")
        self.assertEqual(params, [])

    def test_only_min_amount(self) -> None:
        """仅设置最小金额"""
        constraints = {"min_amount": 20}
        where, params = _build_filter_sql(constraints)
        self.assertIn("amount >=", where)
        self.assertNotIn("amount <=", where)
        self.assertEqual(len(params), 1)

    def test_subject_amount_filter(self) -> None:
        """标的金额过滤"""
        constraints = {
            "min_subject_amount": 100,
            "max_subject_amount": 1000,
        }
        where, params = _build_filter_sql(constraints)
        self.assertIn("subject_amount >=", where)
        self.assertIn("subject_amount <=", where)
# endregion
# ============================================


if __name__ == "__main__":
    unittest.main()
