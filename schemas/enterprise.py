"""
描述: 企业信息 Schema
主要功能:
    - 企业新增与查询结构
依赖: pydantic
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class EnterpriseCreate(BaseModel):
    """
    企业创建请求
    """

    credit_code: str = Field(..., description="统一社会信用代码")
    company_name: str = Field(..., description="企业名称")
    business_scope: str | None = Field(None, description="经营范围")
    industry: str | None = Field(None, description="所属行业")
    enterprise_type: str | None = Field(None, description="企业类型")

    model_config = ConfigDict(extra="forbid")


class EnterpriseResponse(BaseModel):
    """
    企业响应
    """

    credit_code: str
    company_name: str
    business_scope: str | None
    industry: str | None
    enterprise_type: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(extra="forbid")


class EnterpriseDeleteResponse(BaseModel):
    """
    企业删除响应
    """

    credit_code: str
    deleted: bool

    model_config = ConfigDict(extra="forbid")
