"""
描述: API 依赖项
主要功能:
    - 提供数据库连接依赖
依赖: psycopg
"""

from __future__ import annotations

from typing import Generator

from psycopg import Connection

from db.connection import get_connection, get_database_url

# ============================================
# region get_db_connection
# ============================================
def get_db_connection() -> Generator[Connection, None, None]:
    """
    FastAPI 数据库依赖

    返回:
        数据库连接
    """

    db_url = get_database_url()
    with get_connection(db_url) as conn:
        yield conn
# endregion
# ============================================
