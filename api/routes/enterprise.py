"""
描述: 企业信息路由
主要功能:
    - 企业新增与查询
依赖: fastapi
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from psycopg import Connection
from psycopg.errors import UniqueViolation

from api.dependencies import get_db_connection
from schemas.enterprise import (
    EnterpriseCreate,
    EnterpriseDeleteResponse,
    EnterpriseImportResponse,
    EnterpriseResponse,
)
from services.enterprise_service import (
    bulk_create_enterprises,
    create_enterprise,
    delete_enterprise,
    get_enterprise,
)

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
# region import_enterprises_endpoint
# ============================================
@router.post("/import", response_model=EnterpriseImportResponse)
def import_enterprises_endpoint(
    file: UploadFile = File(...),
    conn: Connection = Depends(get_db_connection),
) -> EnterpriseImportResponse:
    """
    批量导入企业

    参数:
        file: JSON 文件
        conn: 数据库连接
    返回:
        导入响应
    """

    try:
        payload = json.loads(file.file.read())
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid JSON") from exc

    if not isinstance(payload, list):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="JSON must be a list"
        )

    return bulk_create_enterprises(conn, payload)
# endregion
# ============================================


# ============================================
# region delete_enterprise_endpoint
# ============================================
@router.delete("/{credit_code}", response_model=EnterpriseDeleteResponse)
def delete_enterprise_endpoint(
    credit_code: str,
    conn: Connection = Depends(get_db_connection),
) -> EnterpriseDeleteResponse:
    """
    删除企业

    参数:
        credit_code: 统一社会信用代码
        conn: 数据库连接
    返回:
        删除响应
    """

    result = delete_enterprise(conn, credit_code)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="enterprise not found")
    return EnterpriseDeleteResponse(credit_code=result, deleted=True)
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
