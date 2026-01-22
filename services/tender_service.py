"""
描述: 招标需求服务
主要功能:
    - 招标需求创建与查询
    - 调用模型解析约束条件
依赖: psycopg, model_service
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from psycopg import Connection

from schemas.matching import (
    TenderRequirementCreate,
    TenderRequirementResponse,
)
from services.model_service import extract_json

PROMPT_PATH = Path("prompts/matching/tender_parse.md")


# ============================================
# region _extract_json_text
# ============================================
def _extract_json_text(text: str) -> str:
    """
    从模型响应中提取 JSON 文本

    参数:
        text: 模型原始响应
    返回:
        清理后的 JSON 字符串
    """
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        lines = stripped.splitlines()
        if lines and lines[0].lower().startswith("json"):
            stripped = "\n".join(lines[1:])
    return stripped.strip()
# endregion
# ============================================


# ============================================
# region load_tender_parse_prompt
# ============================================
def load_tender_parse_prompt() -> str:
    """
    加载招标需求解析提示词

    返回:
        提示词模板内容
    """
    if not PROMPT_PATH.exists():
        raise FileNotFoundError(f"Prompt not found: {PROMPT_PATH}")
    return PROMPT_PATH.read_text(encoding="utf-8")
# endregion
# ============================================


# ============================================
# region parse_tender_constraints
# ============================================
def parse_tender_constraints(raw_text: str) -> dict[str, Any]:
    """
    调用模型解析招标原文，提取约束条件

    参数:
        raw_text: 招标原文
    返回:
        约束条件字典
    """
    prompt = load_tender_parse_prompt()
    full_prompt = f"{prompt}\n\n{raw_text}"
    response = extract_json(full_prompt)
    if not response.content:
        raise ValueError("Empty model response")
    json_text = _extract_json_text(response.content)
    payload = json.loads(json_text)
    if not isinstance(payload, dict):
        raise ValueError("Tender parse response must be a JSON object")
    return payload
# endregion
# ============================================


# ============================================
# region create_tender_requirement
# ============================================
def create_tender_requirement(
    conn: Connection,
    data: TenderRequirementCreate,
    auto_parse: bool = True,
) -> TenderRequirementResponse:
    """
    创建招标需求

    参数:
        conn: 数据库连接
        data: 招标需求创建请求
        auto_parse: 是否自动解析约束条件
    返回:
        招标需求响应
    """
    constraints = data.constraints or {}

    # 如果启用自动解析且未提供约束条件，调用模型解析
    if auto_parse and not constraints:
        try:
            constraints = parse_tender_constraints(data.raw_text)
        except Exception:
            # 解析失败时使用空约束
            constraints = {}

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO tender_requirements (title, raw_text, constraints)
            VALUES (%s, %s, %s)
            RETURNING tender_id, title, raw_text, constraints, created_at
            """,
            (data.title, data.raw_text, json.dumps(constraints, ensure_ascii=False)),
        )
        row = cur.fetchone()
        if not row:
            raise ValueError("Failed to create tender requirement")

    return TenderRequirementResponse(
        tender_id=row[0],
        title=row[1],
        raw_text=row[2],
        constraints=row[3] if isinstance(row[3], dict) else json.loads(row[3] or "{}"),
        created_at=row[4],
    )
# endregion
# ============================================


# ============================================
# region get_tender_requirement
# ============================================
def get_tender_requirement(
    conn: Connection,
    tender_id: int,
) -> TenderRequirementResponse | None:
    """
    查询招标需求

    参数:
        conn: 数据库连接
        tender_id: 招标需求ID
    返回:
        招标需求响应或 None
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT tender_id, title, raw_text, constraints, created_at
            FROM tender_requirements
            WHERE tender_id = %s
            """,
            (tender_id,),
        )
        row = cur.fetchone()
        if not row:
            return None

    return TenderRequirementResponse(
        tender_id=row[0],
        title=row[1],
        raw_text=row[2],
        constraints=row[3] if isinstance(row[3], dict) else json.loads(row[3] or "{}"),
        created_at=row[4],
    )
# endregion
# ============================================


# ============================================
# region list_tender_requirements
# ============================================
def list_tender_requirements(
    conn: Connection,
    limit: int = 20,
    offset: int = 0,
) -> list[TenderRequirementResponse]:
    """
    查询招标需求列表

    参数:
        conn: 数据库连接
        limit: 返回数量
        offset: 偏移量
    返回:
        招标需求列表
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT tender_id, title, raw_text, constraints, created_at
            FROM tender_requirements
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
            """,
            (limit, offset),
        )
        rows = cur.fetchall()

    return [
        TenderRequirementResponse(
            tender_id=row[0],
            title=row[1],
            raw_text=row[2],
            constraints=row[3] if isinstance(row[3], dict) else json.loads(row[3] or "{}"),
            created_at=row[4],
        )
        for row in rows
    ]
# endregion
# ============================================


# ============================================
# region delete_tender_requirement
# ============================================
def delete_tender_requirement(
    conn: Connection,
    tender_id: int,
) -> int | None:
    """
    删除招标需求

    参数:
        conn: 数据库连接
        tender_id: 招标需求ID
    返回:
        删除的 ID 或 None
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            DELETE FROM tender_requirements
            WHERE tender_id = %s
            RETURNING tender_id
            """,
            (tender_id,),
        )
        row = cur.fetchone()

    return row[0] if row else None
# endregion
# ============================================
