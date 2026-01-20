"""
描述: 文档解析路由
主要功能:
    - 文档解析与结构化
依赖: fastapi, markitdown
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from db.connection import get_connection, get_database_url
from schemas.document import DocumentParseResponse
from services.document_service import parse_document

router = APIRouter(prefix="/documents", tags=["documents"])


# ============================================
# region parse_document_endpoint
# ============================================
@router.post("/parse", response_model=DocumentParseResponse, status_code=status.HTTP_200_OK)
def parse_document_endpoint(
    file: UploadFile = File(...),
    include_markdown: bool = False,
    persist: bool = False,
    use_model_structure: bool = True,
) -> DocumentParseResponse:
    """
    解析文档

    参数:
        file: 上传文件
        include_markdown: 是否返回 Markdown
        persist: 是否持久化
        use_model_structure: 是否调用模型结构化
    返回:
        解析响应
    """

    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="file name is required")

    suffix = Path(file.filename).suffix or ".docx"
    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(file.file.read())
            temp_path = temp_file.name

        if persist:
            db_url = get_database_url()
            with get_connection(db_url) as conn:
                return parse_document(
                    temp_path,
                    file.filename,
                    include_markdown,
                    True,
                    use_model_structure,
                    conn,
                )

        return parse_document(
            temp_path,
            file.filename,
            include_markdown,
            False,
            use_model_structure,
            None,
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
# endregion
# ============================================
