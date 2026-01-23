"""
描述: 助手管理服务
主要功能:
    - 助手 CRUD 操作
    - 数据源配置管理
依赖: db.connection, pydantic
"""

from __future__ import annotations

import logging
from typing import Optional, cast
from uuid import UUID

from pydantic import BaseModel, Field
from psycopg import Connection

from db.connection import get_connection


# ============================================
# region Pydantic 模型
# ============================================

class AssistantCreate(BaseModel):
    """创建助手请求"""
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    config: dict = Field(default_factory=dict)


class AssistantUpdate(BaseModel):
    """更新助手请求"""
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    config: Optional[dict] = None
    is_active: Optional[bool] = None


class AssistantResponse(BaseModel):
    """助手响应"""
    assistant_id: UUID
    name: str
    description: Optional[str]
    system_prompt: Optional[str]
    config: dict
    is_active: bool


class DatasourceCreate(BaseModel):
    """创建数据源请求"""
    name: str = Field(..., max_length=100)
    ds_type: str = Field(..., max_length=50)  # postgresql, mysql, api
    connection_config: dict
    table_schema: Optional[dict] = None


class DatasourceResponse(BaseModel):
    """数据源响应"""
    datasource_id: UUID
    assistant_id: UUID
    name: str
    ds_type: str
    table_schema: Optional[dict]
    is_active: bool


# endregion
# ============================================


# ============================================
# region Response Builders
# ============================================
def _build_assistant_response(row: tuple[object, ...]) -> AssistantResponse:
    assistant_uuid = UUID(str(row[0]))
    name = str(row[1])
    description = str(row[2]) if row[2] is not None else None
    system_prompt = str(row[3]) if row[3] is not None else None
    config = row[4] if isinstance(row[4], dict) else {}
    is_active = bool(row[5])
    return AssistantResponse(
        assistant_id=assistant_uuid,
        name=name,
        description=description,
        system_prompt=system_prompt,
        config=config,
        is_active=is_active,
    )


def _build_datasource_response(row: tuple[object, ...]) -> DatasourceResponse:
    datasource_id = UUID(str(row[0]))
    assistant_uuid = UUID(str(row[1]))
    name = str(row[2])
    ds_type = str(row[3])
    table_schema = row[4] if isinstance(row[4], dict) else None
    is_active = bool(row[5])
    return DatasourceResponse(
        datasource_id=datasource_id,
        assistant_id=assistant_uuid,
        name=name,
        ds_type=ds_type,
        table_schema=table_schema,
        is_active=is_active,
    )
# endregion
# ============================================


# ============================================
# region AssistantService
# ============================================

class AssistantService:
    """
    助手管理服务
    
    提供助手的创建、查询、更新、删除操作。
    """
    
    logger = logging.getLogger(__name__)
    
    # 默认助手 ID
    DEFAULT_ASSISTANT_ID = UUID("00000000-0000-0000-0000-000000000001")

    @classmethod
    async def create(cls, data: AssistantCreate) -> AssistantResponse:
        """
        创建新助手
        
        参数:
            data: 助手创建数据
        返回:
            创建的助手信息
        """
        with get_connection() as conn:
            db_conn = cast(Connection, conn)
            try:
                with db_conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO assistants (name, description, system_prompt, config)
                        VALUES (%s, %s, %s, %s)
                        RETURNING assistant_id, name, description, system_prompt, config, is_active
                        """,
                        (data.name, data.description, data.system_prompt, data.config),
                    )
                    row = cur.fetchone()
                if row is None:
                    raise RuntimeError("Failed to create assistant")
                row_value = cast(tuple[object, ...], row)
                db_conn.commit()

                return _build_assistant_response(row_value)
            except Exception as exc:
                db_conn.rollback()
                cls.logger.error("创建助手失败", exc_info=exc)
                raise

    @classmethod
    async def get_by_id(cls, assistant_id: UUID) -> Optional[AssistantResponse]:
        """
        根据 ID 获取助手
        
        参数:
            assistant_id: 助手 UUID
        返回:
            助手信息或 None
        """
        with get_connection() as conn:
            db_conn = cast(Connection, conn)
            with db_conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT assistant_id, name, description, system_prompt, config, is_active
                    FROM assistants
                    WHERE assistant_id = %s
                    """,
                    (str(assistant_id),),
                )
                row = cur.fetchone()

        if not row:
            return None

        return _build_assistant_response(cast(tuple[object, ...], row))

    @classmethod
    async def list_all(cls, only_active: bool = True) -> list[AssistantResponse]:
        """
        列出所有助手
        
        参数:
            only_active: 是否只返回激活的助手
        返回:
            助手列表
        """
        with get_connection() as conn:
            db_conn = cast(Connection, conn)
            with db_conn.cursor() as cur:
                query = """
                    SELECT assistant_id, name, description, system_prompt, config, is_active
                    FROM assistants
                """
                if only_active:
                    query += " WHERE is_active = TRUE"
                query += " ORDER BY created_at DESC"

                cur.execute(query)
                rows = cur.fetchall()

        return [_build_assistant_response(cast(tuple[object, ...], row)) for row in rows]

    @classmethod
    async def update(cls, assistant_id: UUID, data: AssistantUpdate) -> Optional[AssistantResponse]:
        """
        更新助手
        
        参数:
            assistant_id: 助手 UUID
            data: 更新数据
        返回:
            更新后的助手信息或 None
        """
        # 构建动态 UPDATE 语句
        updates = []
        values = []
        
        if data.name is not None:
            updates.append("name = %s")
            values.append(data.name)
        if data.description is not None:
            updates.append("description = %s")
            values.append(data.description)
        if data.system_prompt is not None:
            updates.append("system_prompt = %s")
            values.append(data.system_prompt)
        if data.config is not None:
            updates.append("config = %s")
            values.append(data.config)
        if data.is_active is not None:
            updates.append("is_active = %s")
            values.append(data.is_active)
        
        if not updates:
            return await cls.get_by_id(assistant_id)
        
        updates.append("updated_at = NOW()")
        values.append(str(assistant_id))
        
        with get_connection() as conn:
            db_conn = cast(Connection, conn)
            try:
                with db_conn.cursor() as cur:
                    cur.execute(
                        f"""
                        UPDATE assistants
                        SET {", ".join(updates)}
                        WHERE assistant_id = %s
                        RETURNING assistant_id, name, description, system_prompt, config, is_active
                        """,
                        values,
                    )
                    row = cur.fetchone()
                db_conn.commit()

                if not row:
                    return None

                return _build_assistant_response(cast(tuple[object, ...], row))
            except Exception as exc:
                db_conn.rollback()
                cls.logger.error("更新助手失败", exc_info=exc)
                raise

    @classmethod
    async def delete(cls, assistant_id: UUID) -> bool:
        """
        删除助手
        
        参数:
            assistant_id: 助手 UUID
        返回:
            是否删除成功
        """
        # 禁止删除默认助手
        if assistant_id == cls.DEFAULT_ASSISTANT_ID:
            cls.logger.warning("尝试删除默认助手，已拒绝")
            return False
        
        with get_connection() as conn:
            db_conn = cast(Connection, conn)
            try:
                with db_conn.cursor() as cur:
                    cur.execute(
                        "DELETE FROM assistants WHERE assistant_id = %s",
                        (str(assistant_id),),
                    )
                    deleted = cur.rowcount > 0
                db_conn.commit()
                return deleted
            except Exception as exc:
                db_conn.rollback()
                cls.logger.error("删除助手失败", exc_info=exc)
                raise

    @classmethod
    async def get_system_prompt(cls, assistant_id: UUID) -> str:
        """
        获取助手的 system prompt
        
        参数:
            assistant_id: 助手 UUID
        返回:
            system prompt 内容
        """
        assistant = await cls.get_by_id(assistant_id)
        if assistant and assistant.system_prompt:
            return assistant.system_prompt
        
        # 返回默认 prompt
        return "你是一个专业的知识库问答助手。请根据用户问题，结合检索到的知识库内容，给出准确、有帮助的回答。"


# endregion
# ============================================


# ============================================
# region DatasourceService
# ============================================

class DatasourceService:
    """
    数据源管理服务
    
    管理助手的外接数据源配置。
    """
    
    logger = logging.getLogger(__name__)

    @classmethod
    async def create(cls, assistant_id: UUID, data: DatasourceCreate) -> DatasourceResponse:
        """
        为助手添加数据源
        
        参数:
            assistant_id: 助手 UUID
            data: 数据源配置
        返回:
            创建的数据源信息
        """
        with get_connection() as conn:
            db_conn = cast(Connection, conn)
            try:
                with db_conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO assistant_datasources 
                            (assistant_id, name, ds_type, connection_config, table_schema)
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING datasource_id, assistant_id, name, ds_type, table_schema, is_active
                        """,
                        (
                            str(assistant_id),
                            data.name,
                            data.ds_type,
                            data.connection_config,
                            data.table_schema,
                        ),
                    )
                    row = cur.fetchone()
                if row is None:
                    raise RuntimeError("Failed to create datasource")
                row_value = cast(tuple[object, ...], row)
                db_conn.commit()

                return _build_datasource_response(row_value)
            except Exception as exc:
                db_conn.rollback()
                cls.logger.error("创建数据源失败", exc_info=exc)
                raise

    @classmethod
    async def list_by_assistant(cls, assistant_id: UUID) -> list[DatasourceResponse]:
        """
        列出助手的所有数据源
        
        参数:
            assistant_id: 助手 UUID
        返回:
            数据源列表
        """
        with get_connection() as conn:
            db_conn = cast(Connection, conn)
            with db_conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT datasource_id, assistant_id, name, ds_type, table_schema, is_active
                    FROM assistant_datasources
                    WHERE assistant_id = %s AND is_active = TRUE
                    ORDER BY created_at
                    """,
                    (str(assistant_id),),
                )
                rows = cur.fetchall()

        return [_build_datasource_response(cast(tuple[object, ...], row)) for row in rows]

    @classmethod
    async def delete(cls, datasource_id: UUID) -> bool:
        """
        删除数据源
        
        参数:
            datasource_id: 数据源 UUID
        返回:
            是否删除成功
        """
        with get_connection() as conn:
            db_conn = cast(Connection, conn)
            try:
                with db_conn.cursor() as cur:
                    cur.execute(
                        "DELETE FROM assistant_datasources WHERE datasource_id = %s",
                        (str(datasource_id),),
                    )
                    deleted = cur.rowcount > 0
                db_conn.commit()
                return deleted
            except Exception as exc:
                db_conn.rollback()
                cls.logger.error("删除数据源失败", exc_info=exc)
                raise


# endregion
# ============================================
