"""
描述: 企业信息服务
主要功能:
    - 新增企业
    - 查询企业
依赖: psycopg
"""

from __future__ import annotations

from datetime import datetime

from psycopg import Connection
from psycopg.errors import UniqueViolation

from schemas.enterprise import (
    EnterpriseCreate,
    EnterpriseImportError,
    EnterpriseImportResponse,
    EnterpriseResponse,
)
from services.validators import normalize_commas

# ============================================
# region create_enterprise
# ============================================
def create_enterprise(conn: Connection, data: EnterpriseCreate) -> EnterpriseResponse:
    """
    创建企业信息

    参数:
        conn: 数据库连接
        data: 企业创建请求
    返回:
        企业响应
    """

    payload = {
        "credit_code": normalize_commas(data.credit_code),
        "company_name": data.company_name,
        "business_scope": data.business_scope,
        "industry": data.industry,
        "enterprise_type": data.enterprise_type,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }

    try:
        conn.execute(
            """
            INSERT INTO enterprises (
                credit_code,
                company_name,
                business_scope,
                industry,
                enterprise_type,
                created_at,
                updated_at
            )
            VALUES (
                %(credit_code)s,
                %(company_name)s,
                %(business_scope)s,
                %(industry)s,
                %(enterprise_type)s,
                %(created_at)s,
                %(updated_at)s
            )
            """,
            payload,
        )
        conn.commit()
    except UniqueViolation as exc:
        conn.rollback()
        raise exc
    except Exception:
        conn.rollback()
        raise

    return EnterpriseResponse(**payload)
# endregion
# ============================================


# ============================================
# region bulk_create_enterprises
# ============================================
def bulk_create_enterprises(
    conn: Connection,
    items: list[dict[str, object]],
) -> EnterpriseImportResponse:
    """
    批量导入企业

    参数:
        conn: 数据库连接
        items: 企业数据列表
    返回:
        导入响应
    """

    now = datetime.utcnow()
    payloads: list[dict[str, object]] = []
    errors: list[EnterpriseImportError] = []

    for index, item in enumerate(items):
        if not isinstance(item, dict):
            errors.append(EnterpriseImportError(index=index, error="Each item must be an object"))
            continue
        credit_code = item.get("credit_code")
        company_name = item.get("company_name")
        if not credit_code or not company_name:
            errors.append(
                EnterpriseImportError(index=index, error="credit_code and company_name are required")
            )
            continue
        payloads.append(
            {
                "credit_code": normalize_commas(str(credit_code)),
                "company_name": company_name,
                "business_scope": item.get("business_scope"),
                "industry": item.get("industry"),
                "enterprise_type": item.get("enterprise_type"),
                "created_at": now,
                "updated_at": now,
            }
        )

    if payloads:
        with conn.cursor() as cursor:
            cursor.executemany(
                """
                INSERT INTO enterprises (
                    credit_code,
                    company_name,
                    business_scope,
                    industry,
                    enterprise_type,
                    created_at,
                    updated_at
                )
                VALUES (
                    %(credit_code)s,
                    %(company_name)s,
                    %(business_scope)s,
                    %(industry)s,
                    %(enterprise_type)s,
                    %(created_at)s,
                    %(updated_at)s
                )
                """,
                payloads,
            )
        conn.commit()

    return EnterpriseImportResponse(
        inserted=len(payloads),
        failed=len(errors),
        errors=errors,
    )
# endregion
# ============================================


# ============================================
# region delete_enterprise
# ============================================
def delete_enterprise(conn: Connection, credit_code: str) -> str | None:
    """
    删除企业信息

    参数:
        conn: 数据库连接
        credit_code: 统一社会信用代码
    返回:
        删除的信用代码或 None
    """

    try:
        row = conn.execute(
            """
            DELETE FROM enterprises
            WHERE credit_code = %s
            RETURNING credit_code
            """,
            (credit_code,),
        ).fetchone()
        conn.commit()
    except Exception:
        conn.rollback()
        raise

    if not row:
        return None
    return row[0]
# endregion
# ============================================
# ============================================
# region get_enterprise
# ============================================
def get_enterprise(conn: Connection, credit_code: str) -> EnterpriseResponse | None:
    """
    查询企业信息

    参数:
        conn: 数据库连接
        credit_code: 统一社会信用代码
    返回:
        企业响应或 None
    """

    row = conn.execute(
        """
        SELECT credit_code, company_name, business_scope, industry, enterprise_type,
               created_at, updated_at
        FROM enterprises
        WHERE credit_code = %s
        """,
        (credit_code,),
    ).fetchone()

    if not row:
        return None

    return EnterpriseResponse(
        credit_code=row[0],
        company_name=row[1],
        business_scope=row[2],
        industry=row[3],
        enterprise_type=row[4],
        created_at=row[5],
        updated_at=row[6],
    )
# endregion
# ============================================
