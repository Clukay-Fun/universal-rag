"""
描述: 智能匹配路由
主要功能:
    - 招标需求创建与查询
    - 执行匹配与结果查询
依赖: fastapi
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from psycopg import Connection

from api.dependencies import get_db_connection
from schemas.matching import (
    ContractMatchResponse,
    MatchResultList,
    TenderRequirementCreate,
    TenderRequirementDeleteResponse,
    TenderRequirementResponse,
)
from services.matching_service import (
    delete_match_results,
    execute_matching,
    get_match_results,
)
from services.tender_service import (
    create_tender_requirement,
    delete_tender_requirement,
    get_tender_requirement,
    list_tender_requirements,
)

router = APIRouter(prefix="/matching", tags=["matching"])


# ============================================
# region 创建招标需求
# ============================================
@router.post("/tenders", response_model=TenderRequirementResponse, status_code=status.HTTP_201_CREATED)
def create_tender_endpoint(
    payload: TenderRequirementCreate,
    auto_parse: bool = Query(True, description="是否自动解析约束条件"),
    conn: Connection = Depends(get_db_connection),
) -> TenderRequirementResponse:
    """
    创建招标需求

    参数:
        payload: 招标需求数据
        auto_parse: 是否自动解析约束条件
        conn: 数据库连接
    返回:
        招标需求响应
    """
    try:
        return create_tender_requirement(conn, payload, auto_parse=auto_parse)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
# endregion
# ============================================


# ============================================
# region 查询招标需求
# ============================================
@router.get("/tenders/{tender_id}", response_model=TenderRequirementResponse)
def get_tender_endpoint(
    tender_id: int,
    conn: Connection = Depends(get_db_connection),
) -> TenderRequirementResponse:
    """
    查询招标需求详情

    参数:
        tender_id: 招标需求ID
        conn: 数据库连接
    返回:
        招标需求响应
    """
    result = get_tender_requirement(conn, tender_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="招标需求不存在")
    return result
# endregion
# ============================================


# ============================================
# region 招标需求列表
# ============================================
@router.get("/tenders", response_model=list[TenderRequirementResponse])
def list_tenders_endpoint(
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    conn: Connection = Depends(get_db_connection),
) -> list[TenderRequirementResponse]:
    """
    查询招标需求列表

    参数:
        limit: 返回数量
        offset: 偏移量
        conn: 数据库连接
    返回:
        招标需求列表
    """
    return list_tender_requirements(conn, limit=limit, offset=offset)
# endregion
# ============================================


# ============================================
# region 删除招标需求
# ============================================
@router.delete("/tenders/{tender_id}", response_model=TenderRequirementDeleteResponse)
def delete_tender_endpoint(
    tender_id: int,
    conn: Connection = Depends(get_db_connection),
) -> TenderRequirementDeleteResponse:
    """
    删除招标需求

    参数:
        tender_id: 招标需求ID
        conn: 数据库连接
    返回:
        删除响应
    """
    result = delete_tender_requirement(conn, tender_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="招标需求不存在")
    return TenderRequirementDeleteResponse(tender_id=result, deleted=True)
# endregion
# ============================================


# ============================================
# region 执行匹配
# ============================================
@router.post("/tenders/{tender_id}/match", response_model=list[ContractMatchResponse])
def match_tender_endpoint(
    tender_id: int,
    top_k: int = Query(10, ge=1, le=50, description="返回前K条结果"),
    conn: Connection = Depends(get_db_connection),
) -> list[ContractMatchResponse]:
    """
    执行匹配：筛选业绩 + 评分 + 排序

    参数:
        tender_id: 招标需求ID
        top_k: 返回前K条结果
        conn: 数据库连接
    返回:
        匹配结果列表
    """
    # 1. 获取招标需求
    tender = get_tender_requirement(conn, tender_id)
    if not tender:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="招标需求不存在")

    # 2. 清除旧匹配结果
    delete_match_results(conn, tender_id)

    # 3. 执行匹配
    try:
        results = execute_matching(conn, tender_id, tender.constraints, top_k=top_k)
        return results
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
# endregion
# ============================================


# ============================================
# region 查询匹配结果
# ============================================
@router.get("/tenders/{tender_id}/results", response_model=MatchResultList)
def get_match_results_endpoint(
    tender_id: int,
    conn: Connection = Depends(get_db_connection),
) -> MatchResultList:
    """
    查询匹配结果（带业绩详情）

    参数:
        tender_id: 招标需求ID
        conn: 数据库连接
    返回:
        匹配结果列表
    """
    # 检查招标需求是否存在
    tender = get_tender_requirement(conn, tender_id)
    if not tender:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="招标需求不存在")

    return get_match_results(conn, tender_id)
# endregion
# ============================================


# ============================================
# region SSE执行匹配
# ============================================
from typing import Generator
from fastapi.responses import StreamingResponse
from db.connection import get_connection, get_database_url
from services.matching_service import execute_matching_stream
from services.sse_utils import sse_error


@router.post("/tenders/{tender_id}/match/stream")
async def match_tender_stream_endpoint(
    tender_id: int,
    top_k: int = Query(10, ge=1, le=50, description="返回前K条结果"),
) -> StreamingResponse:
    """
    执行匹配（SSE 流式）：实时推送匹配进度

    参数:
        tender_id: 招标需求ID
        top_k: 返回前K条结果
    返回:
        SSE 事件流
    """
    def event_stream() -> Generator[str, None, None]:
        db_url = get_database_url()
        with get_connection(db_url) as conn:
            # 1. 获取招标需求
            tender = get_tender_requirement(conn, tender_id)
            if not tender:
                yield sse_error("招标需求不存在", "NOT_FOUND")
                return

            # 2. 清除旧匹配结果
            delete_match_results(conn, tender_id)

            # 3. 执行匹配（流式）
            try:
                gen = execute_matching_stream(conn, tender_id, tender.constraints, top_k=top_k)
                for event in gen:
                    yield event
            except Exception as exc:
                yield sse_error(str(exc), "MATCH_ERROR")

    return StreamingResponse(event_stream(), media_type="text/event-stream")
# endregion
# ============================================

