"""
描述: 律师信息服务
主要功能:
    - 新增律师
    - 查询律师
依赖: psycopg
"""

from __future__ import annotations

from datetime import datetime

from psycopg import Connection
from psycopg.errors import UniqueViolation

from schemas.lawyer import LawyerCreate, LawyerResponse


# ============================================
# region _format_vector
# ============================================
def _format_vector(values: list[float] | None) -> str | None:
    """
    转换向量为 pgvector 字面量

    参数:
        values: 向量列表
    返回:
        pgvector 字面量字符串
    """

    if values is None:
        return None
    return f"[{','.join(str(float(v)) for v in values)}]"
# endregion
# ============================================


# ============================================
# region delete_lawyer
# ============================================
def delete_lawyer(conn: Connection, record_id: int) -> int | None:
    """
    删除律师信息

    参数:
        conn: 数据库连接
        record_id: 律师ID
    返回:
        删除的 ID 或 None
    """

    try:
        row = conn.execute(
            """
            DELETE FROM lawyers
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
# region _normalize_vector
# ============================================
def _normalize_vector(value: object | None) -> list[float] | None:
    """
    规范化向量数据

    参数:
        value: 数据库存储的向量
    返回:
        向量列表
    """

    if value is None:
        return None
    if isinstance(value, (list, tuple)):
        return [float(v) for v in value]
    if isinstance(value, str):
        text = value.strip().strip("[]")
        if not text:
            return []
        return [float(item) for item in text.split(",")]
    return None
# endregion
# ============================================


# ============================================
# region create_lawyer
# ============================================
def create_lawyer(conn: Connection, data: LawyerCreate) -> LawyerResponse:
    """
    创建律师信息

    参数:
        conn: 数据库连接
        data: 律师创建请求
    返回:
        律师响应
    """

    payload = {
        "id": data.id,
        "name": data.name,
        "id_card": data.id_card,
        "license_no": data.license_no,
        "resume": data.resume,
        "resume_embedding": _format_vector(data.resume_embedding),
        "id_card_image": data.id_card_image,
        "degree_image": data.degree_image,
        "diploma_image": data.diploma_image,
        "license_image": data.license_image,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }

    try:
        conn.execute(
            """
            INSERT INTO lawyers (
                id,
                name,
                id_card,
                license_no,
                resume,
                resume_embedding,
                id_card_image,
                degree_image,
                diploma_image,
                license_image,
                created_at,
                updated_at
            )
            VALUES (
                %(id)s,
                %(name)s,
                %(id_card)s,
                %(license_no)s,
                %(resume)s,
                %(resume_embedding)s,
                %(id_card_image)s,
                %(degree_image)s,
                %(diploma_image)s,
                %(license_image)s,
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

    return LawyerResponse(
        id=payload["id"],
        name=payload["name"],
        id_card=payload["id_card"],
        license_no=payload["license_no"],
        resume=payload["resume"],
        resume_embedding=data.resume_embedding,
        id_card_image=payload["id_card_image"],
        degree_image=payload["degree_image"],
        diploma_image=payload["diploma_image"],
        license_image=payload["license_image"],
        created_at=payload["created_at"],
        updated_at=payload["updated_at"],
    )
# endregion
# ============================================


# ============================================
# region get_lawyer
# ============================================
def get_lawyer(conn: Connection, record_id: int) -> LawyerResponse | None:
    """
    查询律师信息

    参数:
        conn: 数据库连接
        record_id: 律师ID
    返回:
        律师响应或 None
    """

    row = conn.execute(
        """
        SELECT id, name, id_card, license_no, resume, resume_embedding, id_card_image,
               degree_image, diploma_image, license_image, created_at, updated_at
        FROM lawyers
        WHERE id = %s
        """,
        (record_id,),
    ).fetchone()

    if not row:
        return None

    return LawyerResponse(
        id=row[0],
        name=row[1],
        id_card=row[2],
        license_no=row[3],
        resume=row[4],
        resume_embedding=_normalize_vector(row[5]),
        id_card_image=row[6],
        degree_image=row[7],
        diploma_image=row[8],
        license_image=row[9],
        created_at=row[10],
        updated_at=row[11],
    )
# endregion
# ============================================
