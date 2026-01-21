"""
描述: RAG 问答 Schema
主要功能:
    - 问答请求与响应
依赖: pydantic
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class QARequest(BaseModel):
    """
    问答请求
    """

    question: str = Field(..., description="问题")
    top_k: int = Field(5, description="召回数量")
    doc_id: int | None = Field(None, description="限定文档ID")

    model_config = ConfigDict(extra="forbid")


class QACitation(BaseModel):
    """
    引用来源
    """

    source_id: str
    chunk_id: int
    score: float
    source_title: str | None = None
    file_name: str | None = None
    path: list[str] = Field(default_factory=list)
    party_a_name: str | None = None

    model_config = ConfigDict(extra="forbid")


class QAResponse(BaseModel):
    """
    问答响应
    """

    answer: str
    citations: list[QACitation]

    model_config = ConfigDict(extra="forbid")
