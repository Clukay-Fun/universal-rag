"""
描述: 智能匹配服务
主要功能:
    - 根据约束条件筛选候选业绩
    - 调用模型评分并生成匹配理由
    - 匹配结果持久化
依赖: psycopg, model_service
"""

from __future__ import annotations

import json
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from psycopg import Connection

from schemas.matching import (
    ContractMatchCreate,
    ContractMatchResponse,
    ContractMatchWithDetail,
    MatchResultList,
)
from services.model_service import extract_json

PROMPT_PATH = Path("prompts/matching/match_score.md")


# ============================================
# region 提取JSON文本
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
# region 加载评分提示词
# ============================================
def load_match_score_prompt() -> str:
    """
    加载匹配评分提示词

    返回:
        提示词模板内容
    """
    if not PROMPT_PATH.exists():
        raise FileNotFoundError(f"提示词文件未找到: {PROMPT_PATH}")
    return PROMPT_PATH.read_text(encoding="utf-8")
# endregion
# ============================================


# ============================================
# region 构建过滤SQL
# ============================================
def _build_filter_sql(constraints: dict[str, Any]) -> tuple[str, list[Any]]:
    """
    根据约束条件构建 SQL WHERE 子句

    参数:
        constraints: 约束条件字典
    返回:
        (WHERE 子句, 参数列表)
    """
    conditions: list[str] = []
    params: list[Any] = []

    # 项目类型过滤
    project_types = constraints.get("project_types")
    if project_types and isinstance(project_types, list) and len(project_types) > 0:
        placeholders = ", ".join(["%s"] * len(project_types))
        conditions.append(f"project_type IN ({placeholders})")
        params.extend(project_types)

    # 金额区间过滤
    min_amount = constraints.get("min_amount")
    if min_amount is not None:
        conditions.append("amount >= %s")
        params.append(Decimal(str(min_amount)))

    max_amount = constraints.get("max_amount")
    if max_amount is not None:
        conditions.append("amount <= %s")
        params.append(Decimal(str(max_amount)))

    # 标的金额区间过滤
    min_subject = constraints.get("min_subject_amount")
    if min_subject is not None:
        conditions.append("subject_amount >= %s")
        params.append(Decimal(str(min_subject)))

    max_subject = constraints.get("max_subject_amount")
    if max_subject is not None:
        conditions.append("subject_amount <= %s")
        params.append(Decimal(str(max_subject)))

    # 日期范围过滤
    date_after = constraints.get("date_after")
    if date_after:
        conditions.append("sign_date_norm >= %s")
        params.append(date_after)

    date_before = constraints.get("date_before")
    if date_before:
        conditions.append("sign_date_norm <= %s")
        params.append(date_before)

    # 是否国企过滤
    require_state_owned = constraints.get("require_state_owned")
    if require_state_owned is True:
        conditions.append("is_state_owned = TRUE")

    where_clause = " AND ".join(conditions) if conditions else "1=1"
    return where_clause, params
# endregion
# ============================================


# ============================================
# region 筛选候选业绩
# ============================================
def filter_candidates(
    conn: Connection,
    constraints: dict[str, Any],
    limit: int = 50,
) -> list[dict[str, Any]]:
    """
    根据约束条件筛选候选业绩

    参数:
        conn: 数据库连接
        constraints: 约束条件
        limit: 最大返回数量
    返回:
        候选业绩列表
    """
    where_clause, params = _build_filter_sql(constraints)
    params.append(limit)

    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT 
                contract_id, contract_name, party_a, party_a_industry,
                is_state_owned, amount, sign_date_raw, sign_date_norm,
                project_type, project_detail, subject_amount, summary
            FROM contract_data
            WHERE {where_clause}
            ORDER BY amount DESC
            LIMIT %s
            """,
            params,
        )
        rows = cur.fetchall()

    candidates = []
    for row in rows:
        candidates.append({
            "contract_id": row[0],
            "contract_name": row[1],
            "party_a": row[2],
            "party_a_industry": row[3],
            "is_state_owned": row[4],
            "amount": float(row[5]) if row[5] else None,
            "sign_date_raw": row[6],
            "sign_date_norm": str(row[7]) if row[7] else None,
            "project_type": row[8],
            "project_detail": row[9],
            "subject_amount": float(row[10]) if row[10] else None,
            "summary": row[11],
        })

    return candidates
# endregion
# ============================================


# ============================================
# region 业绩评分
# ============================================
def score_contract(
    constraints: dict[str, Any],
    contract: dict[str, Any],
) -> dict[str, Any]:
    """
    调用模型对单条业绩评分

    参数:
        constraints: 约束条件
        contract: 业绩信息
    返回:
        评分结果 {"score": float, "reasons": list, "warnings": list}
    """
    prompt_template = load_match_score_prompt()

    # 替换占位符
    prompt = prompt_template.replace(
        "{constraints}", json.dumps(constraints, ensure_ascii=False, indent=2)
    ).replace(
        "{contract}", json.dumps(contract, ensure_ascii=False, indent=2)
    )

    response = extract_json(prompt)
    if not response.content:
        raise ValueError("模型响应为空")

    json_text = _extract_json_text(response.content)
    result = json.loads(json_text)

    return {
        "score": float(result.get("score", 0)),
        "reasons": result.get("reasons", []),
        "warnings": result.get("warnings", []),
    }
# endregion
# ============================================


# ============================================
# region 执行匹配
# ============================================
def execute_matching(
    conn: Connection,
    tender_id: int,
    constraints: dict[str, Any],
    top_k: int = 10,
) -> list[ContractMatchResponse]:
    """
    执行匹配：筛选 + 评分 + 排序 + 持久化

    参数:
        conn: 数据库连接
        tender_id: 招标需求ID
        constraints: 约束条件
        top_k: 返回前 K 条结果
    返回:
        匹配结果列表
    """
    # 1. 筛选候选业绩
    candidates = filter_candidates(conn, constraints, limit=top_k * 3)

    if not candidates:
        return []

    # 2. 对每条候选评分
    scored_candidates = []
    for contract in candidates:
        try:
            score_result = score_contract(constraints, contract)
            scored_candidates.append({
                "contract_id": contract["contract_id"],
                "score": score_result["score"],
                "reasons": score_result["reasons"],
            })
        except Exception:
            # 评分失败则跳过
            continue

    # 3. 按得分排序取 top_k
    scored_candidates.sort(key=lambda x: x["score"], reverse=True)
    top_results = scored_candidates[:top_k]

    # 4. 持久化到 contract_matches 表
    results: list[ContractMatchResponse] = []
    with conn.cursor() as cur:
        for item in top_results:
            cur.execute(
                """
                INSERT INTO contract_matches (tender_id, contract_id, score, reasons)
                VALUES (%s, %s, %s, %s)
                RETURNING match_id, tender_id, contract_id, score, reasons, created_at
                """,
                (
                    tender_id,
                    item["contract_id"],
                    Decimal(str(item["score"])),
                    json.dumps(item["reasons"], ensure_ascii=False),
                ),
            )
            row = cur.fetchone()
            if row:
                results.append(ContractMatchResponse(
                    match_id=row[0],
                    tender_id=row[1],
                    contract_id=row[2],
                    score=row[3],
                    reasons=row[4] if isinstance(row[4], list) else json.loads(row[4] or "[]"),
                    created_at=row[5],
                ))

    return results
# endregion
# ============================================


# ============================================
# region 查询匹配结果
# ============================================
def get_match_results(
    conn: Connection,
    tender_id: int,
) -> MatchResultList:
    """
    查询匹配结果（带业绩详情）

    参数:
        conn: 数据库连接
        tender_id: 招标需求ID
    返回:
        匹配结果列表（含业绩详情）
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT 
                m.match_id, m.score, m.reasons,
                c.contract_id, c.party_a, c.project_type, 
                c.project_detail, c.amount, c.sign_date_raw
            FROM contract_matches m
            JOIN contract_data c ON m.contract_id = c.contract_id
            WHERE m.tender_id = %s
            ORDER BY m.score DESC
            """,
            (tender_id,),
        )
        rows = cur.fetchall()

    items = []
    for row in rows:
        reasons = row[2]
        if isinstance(reasons, str):
            reasons = json.loads(reasons or "[]")

        items.append(ContractMatchWithDetail(
            match_id=row[0],
            score=row[1],
            reasons=reasons,
            contract_id=row[3],
            party_a=row[4],
            project_type=row[5],
            project_detail=row[6],
            amount=row[7],
            sign_date_raw=row[8],
        ))

    return MatchResultList(
        tender_id=tender_id,
        total=len(items),
        items=items,
    )
# endregion
# ============================================


# ============================================
# region 删除匹配结果
# ============================================
def delete_match_results(
    conn: Connection,
    tender_id: int,
) -> int:
    """
    删除指定招标需求的所有匹配结果

    参数:
        conn: 数据库连接
        tender_id: 招标需求ID
    返回:
        删除的记录数
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            DELETE FROM contract_matches
            WHERE tender_id = %s
            """,
            (tender_id,),
        )
        return cur.rowcount
# endregion
# ============================================
