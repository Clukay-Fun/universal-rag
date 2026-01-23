"""
描述: 助手管理 API 路由
主要功能:
    - 助手 CRUD 接口
    - 数据源管理接口
依赖: FastAPI, assistant_service
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from services.assistant_service import (
    AssistantService,
    AssistantCreate,
    AssistantUpdate,
    AssistantResponse,
    DatasourceService,
    DatasourceCreate,
    DatasourceResponse,
)


# ============================================
# region Router 定义
# ============================================

router = APIRouter(prefix="/assistants", tags=["助手管理"])


# endregion
# ============================================


# ============================================
# region 助手 CRUD
# ============================================

@router.post("", response_model=AssistantResponse, status_code=status.HTTP_201_CREATED)
async def create_assistant(data: AssistantCreate):
    """
    创建新助手
    """
    return await AssistantService.create(data)


@router.get("", response_model=list[AssistantResponse])
async def list_assistants(only_active: bool = True):
    """
    列出所有助手
    """
    return await AssistantService.list_all(only_active)


@router.get("/{assistant_id}", response_model=AssistantResponse)
async def get_assistant(assistant_id: UUID):
    """
    获取助手详情
    """
    assistant = await AssistantService.get_by_id(assistant_id)
    if not assistant:
        raise HTTPException(status_code=404, detail="助手不存在")
    return assistant


@router.put("/{assistant_id}", response_model=AssistantResponse)
async def update_assistant(assistant_id: UUID, data: AssistantUpdate):
    """
    更新助手
    """
    assistant = await AssistantService.update(assistant_id, data)
    if not assistant:
        raise HTTPException(status_code=404, detail="助手不存在")
    return assistant


@router.delete("/{assistant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assistant(assistant_id: UUID):
    """
    删除助手
    """
    deleted = await AssistantService.delete(assistant_id)
    if not deleted:
        raise HTTPException(status_code=400, detail="无法删除助手（默认助手不可删除）")


# endregion
# ============================================


# ============================================
# region 数据源管理
# ============================================

@router.post("/{assistant_id}/datasources", response_model=DatasourceResponse, status_code=status.HTTP_201_CREATED)
async def add_datasource(assistant_id: UUID, data: DatasourceCreate):
    """
    为助手添加数据源
    """
    # 验证助手存在
    assistant = await AssistantService.get_by_id(assistant_id)
    if not assistant:
        raise HTTPException(status_code=404, detail="助手不存在")
    
    return await DatasourceService.create(assistant_id, data)


@router.get("/{assistant_id}/datasources", response_model=list[DatasourceResponse])
async def list_datasources(assistant_id: UUID):
    """
    列出助手的所有数据源
    """
    return await DatasourceService.list_by_assistant(assistant_id)


@router.delete("/datasources/{datasource_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_datasource(datasource_id: UUID):
    """
    删除数据源
    """
    deleted = await DatasourceService.delete(datasource_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="数据源不存在")


# endregion
# ============================================
