"""
描述: 业绩/合同路由
主要功能:
    - 业绩新增与查询
依赖: fastapi
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from psycopg import Connection
from psycopg.errors import UniqueViolation

from api.dependencies import get_db_connection
from schemas.performance import PerformanceCreate, PerformanceDeleteResponse, PerformanceResponse
from services.performance_service import create_performance, delete_performance, get_performance

router = APIRouter(prefix="/performances", tags=["performances"])

# ============================================
# region create_performance_endpoint
# ============================================
@router.post("", response_model=PerformanceResponse, status_code=status.HTTP_201_CREATED)
def create_performance_endpoint(
    payload: PerformanceCreate,
    conn: Connection = Depends(get_db_connection),
) -> PerformanceResponse:
    """
    新增业绩

    参数:
        payload: 业绩数据
        conn: 数据库连接
    返回:
        业绩响应
    """

    try:
        return create_performance(conn, payload)
    except UniqueViolation as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="performance id already exists",
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
# endregion
# ============================================


# ============================================
# region delete_performance_endpoint
# ============================================
@router.delete("/{record_id}", response_model=PerformanceDeleteResponse)
def delete_performance_endpoint(
    record_id: int,
    conn: Connection = Depends(get_db_connection),
) -> PerformanceDeleteResponse:
    """
    删除业绩

    参数:
        record_id: 业绩ID
        conn: 数据库连接
    返回:
        删除响应
    """

    result = delete_performance(conn, record_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="performance not found")
    return PerformanceDeleteResponse(id=result, deleted=True)
# endregion
# ============================================
# ============================================
# region get_performance_endpoint
# ============================================
@router.get("/{record_id}", response_model=PerformanceResponse)
def get_performance_endpoint(
    record_id: int,
    conn: Connection = Depends(get_db_connection),
) -> PerformanceResponse:
    """
    查询业绩

    参数:
        record_id: 业绩ID
        conn: 数据库连接
    返回:
        业绩响应
    """

    result = get_performance(conn, record_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="performance not found")
    return result
# endregion
# ============================================
