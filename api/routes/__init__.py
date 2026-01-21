"""
描述: 路由包初始化
主要功能:
    - 聚合 API 路由
依赖: fastapi
"""

from fastapi import APIRouter

from api.routes.enterprise import router as enterprise_router
from api.routes.health import router as health_router
from api.routes.performance import router as performance_router
from api.routes.lawyers import router as lawyers_router
from api.routes.documents import router as documents_router
from api.routes.vector import router as vector_router
from api.routes.rag import router as rag_router

router = APIRouter()
router.include_router(health_router)
router.include_router(enterprise_router)
router.include_router(performance_router)
router.include_router(lawyers_router)
router.include_router(documents_router)
router.include_router(vector_router)
router.include_router(rag_router)
