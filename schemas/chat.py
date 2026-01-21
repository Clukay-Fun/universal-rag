"""
描述: 对话会话 Schema
主要功能:
    - 会话与消息结构
依赖: pydantic
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ChatSessionCreateRequest(BaseModel):
    """
    创建会话请求
    """

    user_id: str | None = Field(None, description="用户ID")

    model_config = ConfigDict(extra="forbid")


class ChatSessionCreateResponse(BaseModel):
    """
    创建会话响应
    """

    session_id: str
    title: str | None

    model_config = ConfigDict(extra="forbid")


class ChatMessageRequest(BaseModel):
    """
    发送消息请求
    """

    content: str = Field(..., description="消息内容")
    top_k: int = Field(5, description="召回数量")
    doc_id: int | None = Field(None, description="文档ID")

    model_config = ConfigDict(extra="forbid")


class ChatCitation(BaseModel):
    """
    引用来源
    """

    source_id: str
    node_id: int
    score: float
    path: list[str]

    model_config = ConfigDict(extra="forbid")


class ChatMessageItem(BaseModel):
    """
    会话消息
    """

    message_id: int
    role: str
    content: str
    citations: list[ChatCitation] = Field(default_factory=list)
    created_at: str

    model_config = ConfigDict(extra="forbid")


class ChatHistoryResponse(BaseModel):
    """
    会话历史响应
    """

    session_id: str
    messages: list[ChatMessageItem]

    model_config = ConfigDict(extra="forbid")
