"""
描述: 数据库连接工具
主要功能:
    - 创建 PostgreSQL 连接
    - 提供上下文管理
依赖: psycopg
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

import psycopg
from psycopg import Connection

# ============================================
# region get_connection
# ============================================
@contextmanager
def get_connection(db_url: str) -> Iterator[Connection]:
    """
    获取数据库连接

    参数:
        db_url: PostgreSQL 连接串
    返回:
        数据库连接上下文
    """

    conn = psycopg.connect(db_url)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
# endregion
# ============================================
