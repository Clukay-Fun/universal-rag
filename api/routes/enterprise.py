"""
描述: 企业信息路由
主要功能:
    - 企业新增与查询
依赖: fastapi
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from psycopg import Connection
from psycopg.errors import UniqueViolation

from api.dependencies import get_db_connection
from schemas.enterprise import EnterpriseCreate, EnterpriseResponse
from services.enterprise_service import create_enterprise, get_enterprise

router = APIRouter(prefix="/enterprises", tags=["enterprises"])

# ============================================
# region create_enterprise_endpoint
# ============================================
@router.post("", response_model=EnterpriseResponse, status_code=status.HTTP_201_CREATED)
def create_enterprise_endpoint(
    payload: EnterpriseCreate,
    conn: Connection = Depends(get_db_connection),
) -> EnterpriseResponse:
    """
    新增企业

    参数:
        payload: 企业数据
        conn: 数据库连接
    返回:
        企业响应
    """

    try:
        return create_enterprise(conn, payload)
    except UniqueViolation as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="credit_code already exists",
        ) from exc
# endregion
# ============================================

# ============================================
# region get_enterprise_endpoint
# ============================================
@router.get("/{credit_code}", response_model=EnterpriseResponse)
def get_enterprise_endpoint(
    credit_code: str,
    conn: Connection = Depends(get_db_connection),
) -> EnterpriseResponse:
    """
    查询企业

    参数:
        credit_code: 统一社会信用代码
        conn: 数据库连接
    返回:
        企业响应
    """

    result = get_enterprise(conn, credit_code)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="enterprise not found")
    return result
# endregion
# ============================================
