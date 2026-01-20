"""
描述: 数据校验与标准化
主要功能:
    - 金额非负校验
    - 日期解析与标准化
    - 分隔符统一
依赖: 标准库
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation

DATE_FORMATS = ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%Y年%m月%d日")


def normalize_commas(value: str | None) -> str | None:
    """
    统一中文分隔符为英文逗号

    参数:
        value: 原始字符串
    返回:
        规范化后的字符串
    """

    if value is None:
        return None
    return value.replace("，", ",").replace("、", ",")


def ensure_non_negative(value: Decimal, field_name: str) -> None:
    """
    校验非负数值

    参数:
        value: 数值
        field_name: 字段名
    返回:
        None
    """

    if value < 0:
        raise ValueError(f"{field_name} must be >= 0")


def parse_decimal(value: str, field_name: str) -> Decimal:
    """
    解析数值字符串为 Decimal

    参数:
        value: 数值字符串
        field_name: 字段名
    返回:
        Decimal 数值
    """

    try:
        return Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name} is not a valid number") from exc


def parse_sign_date(raw: str | None, norm: str | None) -> tuple[str | None, date | None]:
    """
    解析签署日期

    参数:
        raw: 原始日期字符串
        norm: 标准化日期字符串
    返回:
        原文与标准化日期
    """

    if norm:
        try:
            parsed = date.fromisoformat(norm)
        except ValueError as exc:
            raise ValueError("sign_date_norm format must be YYYY-MM-DD") from exc
        return raw or norm, parsed

    if raw:
        for fmt in DATE_FORMATS:
            try:
                return raw, datetime.strptime(raw, fmt).date()
            except ValueError:
                continue
        raise ValueError("sign_date_raw format is not supported")

    return None, None
