"""
描述: 业绩/合同 Schema
主要功能:
    - 业绩新增与查询结构
依赖: pydantic
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PerformanceCreate(BaseModel):
    """
    业绩创建请求
    """

    id: int = Field(..., description="主键ID")
    file_name: str | None = Field(None, description="文件名")
    party_a: str | None = Field(None, description="甲方名称（逗号分隔）")
    party_a_id: str | None = Field(None, description="甲方证件号（逗号分隔）")
    contract_number: int | None = Field(None, description="合同编号")
    amount: Decimal = Field(..., description="金额（万元）")
    fee_method: str | None = Field(None, description="计费方式原文")
    sign_date_norm: date | None = Field(None, description="签署日期（标准化）")
    sign_date_raw: str | None = Field(None, description="签署日期原文")
    project_type: str | None = Field(None, description="合同类型")
    project_detail: str | None = Field(None, description="项目详情")
    subject_amount: Decimal | None = Field(None, description="标的金额（万元）")
    opponent: str | None = Field(None, description="相对方/对手方")
    team_member: str | None = Field(None, description="团队成员")
    summary: None | str = Field(None, description="摘要/总结")
    image_data: bytes | None = Field(None, description="图片二进制")
    image_count: int | None = Field(None, description="图片数量")
    raw_text: str | None = Field(None, description="原始文本")

    model_config = ConfigDict(extra="forbid")

    # ============================================
    # region validate_amount
    # ============================================
    @field_validator("amount")
    @classmethod
    def validate_amount(cls, value: Decimal) -> Decimal:
        if value < 0:
            raise ValueError("amount must be >= 0")
        return value
    # endregion
    # ============================================

    # ============================================
    # region validate_subject_amount
    # ============================================
    @field_validator("subject_amount")
    @classmethod
    def validate_subject_amount(cls, value: Decimal | None) -> Decimal | None:
        if value is not None and value < 0:
            raise ValueError("subject_amount must be >= 0")
        return value
    # endregion
    # ============================================


class PerformanceResponse(BaseModel):
    """
    业绩响应
    """

    id: int
    file_name: str | None
    party_a: str | None
    party_a_id: str | None
    contract_number: int | None
    amount: Decimal
    fee_method: str | None
    sign_date_norm: date | None
    sign_date_raw: str | None
    project_type: str | None
    project_detail: str | None
    subject_amount: Decimal | None
    opponent: str | None
    team_member: str | None
    summary: None | str
    image_count: int | None
    raw_text: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(extra="forbid")


class PerformanceDeleteResponse(BaseModel):
    """
    业绩删除响应
    """

    id: int
    deleted: bool

    model_config = ConfigDict(extra="forbid")
