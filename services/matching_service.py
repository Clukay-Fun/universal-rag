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

    # 项目类型过滤（暂时禁用）
    # project_types = constraints.get("project_types")
    # if project_types and isinstance(project_types, list) and len(project_types) > 0:
    #     placeholders = ", ".join(["%s"] * len(project_types))
    #     conditions.append(f"project_type IN ({placeholders})")
    #     params.extend(project_types)

    # 金额区间过滤
    min_amount = constraints.get("min_amount")
    if min_amount is not None:
        try:
            conditions.append("amount >= %s")
            params.append(Decimal(str(min_amount)))
        except Exception:
             pass # 防止金额列也不存在

    # max_amount = constraints.get("max_amount")
    # if max_amount is not None:
    #     conditions.append("amount <= %s")
    #     params.append(Decimal(str(max_amount)))

    # 标的金额区间过滤（暂时禁用）
    # min_subject = constraints.get("min_subject_amount")
    # if min_subject is not None:
    #     conditions.append("subject_amount >= %s")
    #     params.append(Decimal(str(min_subject)))

    # max_subject = constraints.get("max_subject_amount")
    # if max_subject is not None:
    #     conditions.append("subject_amount <= %s")
    #     params.append(Decimal(str(max_subject)))

    # 日期范围过滤（暂时禁用）
    # date_after = constraints.get("date_after")
    # if date_after:
    #     conditions.append("sign_date_norm >= %s")
    #     params.append(date_after)

    # date_before = constraints.get("date_before")
    # if date_before:
    #     conditions.append("sign_date_norm <= %s")
    #     params.append(date_before)

    # 是否国企过滤（暂时禁用，防止列不存在报错）
    # require_state_owned = constraints.get("require_state_owned")
    # if require_state_owned is True:
    #     conditions.append("is_state_owned = TRUE")

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
        # 使用 SELECT * 动态获取所有列
        cur.execute(
            f"""
            SELECT *
            FROM contract_data
            WHERE {where_clause}
            ORDER BY contract_id DESC
            LIMIT %s
            """,
            params,
        )
        rows = cur.fetchall()
        
        # 获取列名
        col_names = [desc[0] for desc in cur.description] if cur.description else []

    candidates = []
    for row in rows:
        # 构建字典
        row_dict = dict(zip(col_names, row))
        # 只保留核心字段
        candidates.append({
            "contract_id": row_dict.get("contract_id") or row_dict.get("id"),
            "party_a": row_dict.get("party_a"),
            "amount": float(row_dict.get("amount", 0)) if row_dict.get("amount") else None,
            "sign_date_norm": str(row_dict.get("sign_date_norm")) if row_dict.get("sign_date_norm") else None,
            "project_type": row_dict.get("project_type"),
            "project_detail": row_dict.get("project_detail"),
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
        # 获取 contract_matches 的列，使用动态列获取防止列不存在报错
        cur.execute(
            """
            SELECT m.match_id, m.score, m.reasons, c.*
            FROM contract_matches m
            JOIN contract_data c ON m.contract_id = c.contract_id
            WHERE m.tender_id = %s
            ORDER BY m.score DESC
            """,
            (tender_id,),
        )
        rows = cur.fetchall()
        
        # 获取列名
        col_names = [desc[0] for desc in cur.description] if cur.description else []

    items = []
    for row in rows:
        row_dict = dict(zip(col_names, row))
        
        reasons = row_dict.get("reasons")
        if isinstance(reasons, str):
            reasons = json.loads(reasons or "[]")

        items.append(ContractMatchWithDetail(
            match_id=row_dict.get("match_id"),
            score=row_dict.get("score"),
            reasons=reasons,
            contract_id=row_dict.get("contract_id"),
            party_a=row_dict.get("party_a"),
            project_type=row_dict.get("project_type"),
            project_detail=row_dict.get("project_detail"),
            amount=row_dict.get("amount"),
            sign_date_raw=row_dict.get("sign_date_raw"),
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


# ============================================
# region SSE匹配生成器
# ============================================
from typing import Generator

from services.sse_utils import (
    MatchingState,
    sse_status,
    sse_progress,
    sse_done,
    sse_error,
)


def execute_matching_stream(
    conn: Connection,
    tender_id: int,
    constraints: dict[str, Any],
    top_k: int = 10,
) -> Generator[str, None, list[ContractMatchResponse]]:
    """
    执行匹配（SSE 流式版本）：逐步推送状态

    参数:
        conn: 数据库连接
        tender_id: 招标需求ID
        constraints: 约束条件
        top_k: 返回前 K 条结果
    返回:
        生成器，yield SSE 事件字符串，最终返回匹配结果列表
    """
    # 1. 筛选候选业绩
    yield sse_status(MatchingState.FILTERING.value, 1, 3, "正在筛选候选业绩...")
    candidates = filter_candidates(conn, constraints, limit=top_k * 3)

    if not candidates:
        yield sse_status(MatchingState.DONE.value, 3, 3, "无符合条件的业绩")
        yield sse_done({"total": 0, "results": []})
        return []

    yield sse_progress(1, 3, f"筛选出 {len(candidates)} 条候选业绩")

    # 2. 对每条候选评分
    yield sse_status(MatchingState.SCORING.value, 2, 3, "正在评分...")
    scored_candidates = []
    total = len(candidates)

    for idx, contract in enumerate(candidates):
        try:
            score_result = score_contract(constraints, contract)
            scored_candidates.append({
                "contract_id": contract["contract_id"],
                "score": score_result["score"],
                "reasons": score_result["reasons"],
            })
            # 每评分一条推送进度
            yield sse_progress(idx + 1, total, f"已评分 {idx + 1}/{total}")
        except Exception:
            # 评分失败则跳过
            continue

    # 3. 排序取 top_k
    scored_candidates.sort(key=lambda x: x["score"], reverse=True)
    top_results = scored_candidates[:top_k]

    # 4. 持久化
    yield sse_status(MatchingState.SAVING.value, 3, 3, "正在保存结果...")
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

    # 5. 完成
    yield sse_status(MatchingState.DONE.value, 3, 3, f"匹配完成，共 {len(results)} 条结果")
    yield sse_done({
        "total": len(results),
        "results": [
            {"match_id": r.match_id, "contract_id": r.contract_id, "score": float(r.score)}
            for r in results
        ],
    })

    return results
# endregion
# ============================================

