"""
描述: 路由包初始化
主要功能:
    - 聚合 API 路由
依赖: fastapi
"""

from fastapi import APIRouter

from api.routes.health import router as health_router
from api.routes.documents import router as documents_router
from api.routes.vector import router as vector_router
from api.routes.rag import router as rag_router
from api.routes.chat import router as chat_router
from api.routes.assistants import router as assistants_router


# ============================================
# region 路由聚合
# ============================================

router = APIRouter()

# 核心路由
router.include_router(health_router)
router.include_router(assistants_router)  # 新增：助手管理
router.include_router(documents_router)
router.include_router(vector_router)
router.include_router(rag_router)
router.include_router(chat_router)

# endregion
# ============================================
