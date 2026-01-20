"""
描述: 业绩/合同服务
主要功能:
    - 新增业绩记录
    - 查询业绩记录
依赖: psycopg
"""

from __future__ import annotations

from datetime import datetime

from psycopg import Connection
from psycopg.errors import UniqueViolation

from schemas.performance import PerformanceCreate, PerformanceResponse
from services.validators import ensure_non_negative, normalize_commas, parse_sign_date

# ============================================
# region create_performance
# ============================================
def create_performance(conn: Connection, data: PerformanceCreate) -> PerformanceResponse:
    """
    创建业绩记录

    参数:
        conn: 数据库连接
        data: 业绩创建请求
    返回:
        业绩响应
    """

    ensure_non_negative(data.amount, "amount")
    if data.subject_amount is not None:
        ensure_non_negative(data.subject_amount, "subject_amount")

    sign_date_raw, sign_date_norm = parse_sign_date(data.sign_date_raw, data.sign_date_norm)

    payload = {
        "id": data.id,
        "file_name": data.file_name,
        "party_a": normalize_commas(data.party_a),
        "party_a_id": normalize_commas(data.party_a_id),
        "contract_number": data.contract_number,
        "amount": data.amount,
        "fee_method": data.fee_method,
        "sign_date_norm": sign_date_norm,
        "sign_date_raw": sign_date_raw,
        "project_type": data.project_type,
        "project_detail": data.project_detail,
        "subject_amount": data.subject_amount,
        "opponent": data.opponent,
        "team_member": normalize_commas(data.team_member),
        "summary": None,
        "image_data": data.image_data,
        "image_count": data.image_count,
        "raw_text": data.raw_text,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "embedding": None,
    }

    try:
        conn.execute(
            """
            INSERT INTO performances (
                id,
                file_name,
                party_a,
                party_a_id,
                contract_number,
                amount,
                fee_method,
                sign_date_norm,
                sign_date_raw,
                project_type,
                project_detail,
                subject_amount,
                opponent,
                team_member,
                summary,
                image_data,
                image_count,
                raw_text,
                created_at,
                updated_at,
                embedding
            )
            VALUES (
                %(id)s,
                %(file_name)s,
                %(party_a)s,
                %(party_a_id)s,
                %(contract_number)s,
                %(amount)s,
                %(fee_method)s,
                %(sign_date_norm)s,
                %(sign_date_raw)s,
                %(project_type)s,
                %(project_detail)s,
                %(subject_amount)s,
                %(opponent)s,
                %(team_member)s,
                %(summary)s,
                %(image_data)s,
                %(image_count)s,
                %(raw_text)s,
                %(created_at)s,
                %(updated_at)s,
                %(embedding)s
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

    return PerformanceResponse(
        id=payload["id"],
        file_name=payload["file_name"],
        party_a=payload["party_a"],
        party_a_id=payload["party_a_id"],
        contract_number=payload["contract_number"],
        amount=payload["amount"],
        fee_method=payload["fee_method"],
        sign_date_norm=payload["sign_date_norm"],
        sign_date_raw=payload["sign_date_raw"],
        project_type=payload["project_type"],
        project_detail=payload["project_detail"],
        subject_amount=payload["subject_amount"],
        opponent=payload["opponent"],
        team_member=payload["team_member"],
        summary=None,
        image_count=payload["image_count"],
        raw_text=payload["raw_text"],
        created_at=payload["created_at"],
        updated_at=payload["updated_at"],
    )
# endregion
# ============================================


# ============================================
# region delete_performance
# ============================================
def delete_performance(conn: Connection, record_id: int) -> int | None:
    """
    删除业绩记录

    参数:
        conn: 数据库连接
        record_id: 业绩ID
    返回:
        删除的 ID 或 None
    """

    try:
        row = conn.execute(
            """
            DELETE FROM performances
            WHERE id = %s
            RETURNING id
            """,
            (record_id,),
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
# region get_performance
# ============================================
def get_performance(conn: Connection, record_id: int) -> PerformanceResponse | None:
    """
    查询业绩记录

    参数:
        conn: 数据库连接
        record_id: 业绩ID
    返回:
        业绩响应或 None
    """

    row = conn.execute(
        """
        SELECT id, file_name, party_a, party_a_id, contract_number, amount, fee_method,
               sign_date_norm, sign_date_raw, project_type, project_detail, subject_amount,
               opponent, team_member, summary, image_count, raw_text, created_at, updated_at
        FROM performances
        WHERE id = %s
        """,
        (record_id,),
    ).fetchone()

    if not row:
        return None

    return PerformanceResponse(
        id=row[0],
        file_name=row[1],
        party_a=row[2],
        party_a_id=row[3],
        contract_number=row[4],
        amount=row[5],
        fee_method=row[6],
        sign_date_norm=row[7],
        sign_date_raw=row[8],
        project_type=row[9],
        project_detail=row[10],
        subject_amount=row[11],
        opponent=row[12],
        team_member=row[13],
        summary=row[14],
        image_count=row[15],
        raw_text=row[16],
        created_at=row[17],
        updated_at=row[18],
    )
# endregion
# ============================================
