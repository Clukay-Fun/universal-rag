"""
描述: 文档解析 Schema
主要功能:
    - 文档节点与解析响应结构
依赖: pydantic
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class DocumentNode(BaseModel):
    """
    文档节点
    """

    node_id: int = Field(..., description="节点ID")
    parent_id: int | None = Field(None, description="父节点ID")
    level: int = Field(..., description="层级")
    title: str = Field(..., description="标题")
    content: str = Field(..., description="内容")
    path: list[str] = Field(default_factory=list, description="血缘路径")

    model_config = ConfigDict(extra="forbid")


class DocumentParseStats(BaseModel):
    """
    解析统计
    """

    node_count: int = Field(..., description="节点数量")
    line_count: int = Field(..., description="行数")
    content_length: int = Field(..., description="文本长度")

    model_config = ConfigDict(extra="forbid")


class DocumentParseResponse(BaseModel):
    """
    文档解析响应
    """

    doc_id: int | None = Field(None, description="文档ID")
    title: str | None = Field(None, description="文档标题")
    file_name: str | None = Field(None, description="文件名")
    markdown: str | None = Field(None, description="Markdown 内容")
    structure_result: str | None = Field(None, description="结构化结果")
    structure_error: str | None = Field(None, description="结构化错误")
    nodes: list[DocumentNode] = Field(default_factory=list, description="节点列表")
    stats: DocumentParseStats

    model_config = ConfigDict(extra="forbid")


class DocumentStructureResponse(BaseModel):
    """
    文档结构化结果响应
    """

    doc_id: int
    model_name: str | None
    payload: dict[str, object] | None
    raw_text: str | None
    error: str | None
    created_at: str | None

    model_config = ConfigDict(extra="forbid")


class DocumentTreeNode(BaseModel):
    """
    文档树节点
    """

    title: str
    level: int
    content: str
    children: list["DocumentTreeNode"] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


DocumentTreeNode.model_rebuild()
