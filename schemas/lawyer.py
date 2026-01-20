"""
描述: 律师信息 Schema
主要功能:
    - 律师新增与查询结构
依赖: pydantic
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LawyerCreate(BaseModel):
    """
    律师创建请求
    """

    id: int = Field(..., description="主键ID")
    name: str = Field(..., description="姓名")
    id_card: str | None = Field(None, description="身份证号")
    license_no: str | None = Field(None, description="执业证号")
    resume: str | None = Field(None, description="个人简介/简历")
    resume_embedding: list[float] | None = Field(None, description="简历向量特征")
    id_card_image: str | None = Field(None, description="身份证照片路径")
    degree_image: str | None = Field(None, description="学位证照片路径")
    diploma_image: str | None = Field(None, description="毕业证照片路径")
    license_image: str | None = Field(None, description="执业证照片路径")

    model_config = ConfigDict(extra="forbid")


class LawyerResponse(BaseModel):
    """
    律师响应
    """

    id: int
    name: str
    id_card: str | None
    license_no: str | None
    resume: str | None
    resume_embedding: list[float] | None
    id_card_image: str | None
    degree_image: str | None
    diploma_image: str | None
    license_image: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(extra="forbid")


class LawyerDeleteResponse(BaseModel):
    """
    律师删除响应
    """

    id: int
    deleted: bool

    model_config = ConfigDict(extra="forbid")
