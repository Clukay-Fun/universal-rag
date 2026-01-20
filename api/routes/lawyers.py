"""
描述: 律师信息路由
主要功能:
    - 律师新增与查询
依赖: fastapi
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from psycopg import Connection
from psycopg.errors import UniqueViolation

from api.dependencies import get_db_connection
from schemas.lawyer import LawyerCreate, LawyerDeleteResponse, LawyerResponse
from services.lawyer_service import create_lawyer, delete_lawyer, get_lawyer

router = APIRouter(prefix="/lawyers", tags=["lawyers"])


# ============================================
# region create_lawyer_endpoint
# ============================================
@router.post("", response_model=LawyerResponse, status_code=status.HTTP_201_CREATED)
def create_lawyer_endpoint(
    payload: LawyerCreate,
    conn: Connection = Depends(get_db_connection),
) -> LawyerResponse:
    """
    新增律师

    参数:
        payload: 律师数据
        conn: 数据库连接
    返回:
        律师响应
    """

    try:
        return create_lawyer(conn, payload)
    except UniqueViolation as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="lawyer id already exists",
        ) from exc
# endregion
# ============================================


# ============================================
# region delete_lawyer_endpoint
# ============================================
@router.delete("/{record_id}", response_model=LawyerDeleteResponse)
def delete_lawyer_endpoint(
    record_id: int,
    conn: Connection = Depends(get_db_connection),
) -> LawyerDeleteResponse:
    """
    删除律师

    参数:
        record_id: 律师ID
        conn: 数据库连接
    返回:
        删除响应
    """

    result = delete_lawyer(conn, record_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="lawyer not found")
    return LawyerDeleteResponse(id=result, deleted=True)
# endregion
# ============================================

# ============================================
# region get_lawyer_endpoint
# ============================================
@router.get("/{record_id}", response_model=LawyerResponse)
def get_lawyer_endpoint(
    record_id: int,
    conn: Connection = Depends(get_db_connection),
) -> LawyerResponse:
    """
    查询律师

    参数:
        record_id: 律师ID
        conn: 数据库连接
    返回:
        律师响应
    """

    result = get_lawyer(conn, record_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="lawyer not found")
    return result
# endregion
# ============================================
