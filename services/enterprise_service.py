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

from schemas.enterprise import EnterpriseCreate, EnterpriseResponse
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
