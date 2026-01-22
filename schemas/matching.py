"""
描述: 智能匹配 Schema
主要功能:
    - 招标需求创建与响应结构
    - 匹配结果创建与响应结构
依赖: pydantic
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ============================================
# region TenderRequirement Schema
# ============================================
class TenderRequirementCreate(BaseModel):
    """
    招标需求创建请求

    参数:
        title: 招标标题
        raw_text: 招标原文
        constraints: 解析后的约束条件（JSON）
    """

    title: str | None = Field(None, description="招标标题")
    raw_text: str = Field(..., description="招标原文")
    constraints: dict[str, Any] | None = Field(
        default_factory=dict, description="约束条件（金额区间、项目类型、行业等）"
    )

    model_config = ConfigDict(extra="forbid")


class TenderRequirementResponse(BaseModel):
    """
    招标需求响应
    """

    tender_id: int = Field(..., description="招标需求ID")
    title: str | None = Field(None, description="招标标题")
    raw_text: str = Field(..., description="招标原文")
    constraints: dict[str, Any] = Field(default_factory=dict, description="约束条件")
    created_at: datetime = Field(..., description="创建时间")

    model_config = ConfigDict(extra="forbid")


class TenderRequirementDeleteResponse(BaseModel):
    """
    招标需求删除响应
    """

    tender_id: int
    deleted: bool

    model_config = ConfigDict(extra="forbid")


# endregion
# ============================================


# ============================================
# region ContractMatch Schema
# ============================================
class ContractMatchCreate(BaseModel):
    """
    匹配结果创建请求

    参数:
        tender_id: 招标需求ID
        contract_id: 业绩/合同ID
        score: 匹配得分（0-1）
        reasons: 匹配理由列表
    """

    tender_id: int = Field(..., description="招标需求ID")
    contract_id: int = Field(..., description="业绩/合同ID")
    score: Decimal = Field(..., description="匹配得分（0-1）")
    reasons: list[str] = Field(default_factory=list, description="匹配理由列表")

    model_config = ConfigDict(extra="forbid")

    # ============================================
    # region validate_score
    # ============================================
    @field_validator("score")
    @classmethod
    def validate_score(cls, value: Decimal) -> Decimal:
        if value < 0 or value > 1:
            raise ValueError("score must be between 0 and 1")
        return value
    # endregion
    # ============================================


class ContractMatchResponse(BaseModel):
    """
    匹配结果响应
    """

    match_id: int = Field(..., description="匹配记录ID")
    tender_id: int = Field(..., description="招标需求ID")
    contract_id: int = Field(..., description="业绩/合同ID")
    score: Decimal = Field(..., description="匹配得分（0-1）")
    reasons: list[str] = Field(default_factory=list, description="匹配理由列表")
    created_at: datetime = Field(..., description="创建时间")

    model_config = ConfigDict(extra="forbid")


class ContractMatchWithDetail(BaseModel):
    """
    带业绩详情的匹配结果（用于展示）

    参数:
        match_id: 匹配记录ID
        score: 匹配得分
        reasons: 匹配理由
        contract: 业绩详情
    """

    match_id: int = Field(..., description="匹配记录ID")
    score: Decimal = Field(..., description="匹配得分")
    reasons: list[str] = Field(default_factory=list, description="匹配理由")
    contract_id: int = Field(..., description="业绩/合同ID")
    party_a: str | None = Field(None, description="甲方名称")
    project_type: str | None = Field(None, description="项目类型")
    project_detail: str | None = Field(None, description="项目详情")
    amount: Decimal | None = Field(None, description="金额")
    sign_date_raw: str | None = Field(None, description="签署日期原文")

    model_config = ConfigDict(extra="forbid")


class MatchResultList(BaseModel):
    """
    匹配结果列表响应
    """

    tender_id: int = Field(..., description="招标需求ID")
    total: int = Field(..., description="匹配结果总数")
    items: list[ContractMatchWithDetail] = Field(
        default_factory=list, description="匹配结果列表"
    )

    model_config = ConfigDict(extra="forbid")


# endregion
# ============================================
