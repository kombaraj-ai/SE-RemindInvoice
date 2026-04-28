"""
Pydantic schemas for ReminderRule and ReminderLog request/response validation.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator

from app.models.reminder import ReminderStatus, TriggerType


# ---------------------------------------------------------------------------
# ReminderRule schemas
# ---------------------------------------------------------------------------


class ReminderRuleCreate(BaseModel):
    name: str
    trigger_type: TriggerType
    days_offset: int = 0

    @field_validator("days_offset")
    @classmethod
    def must_be_non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("days_offset must be >= 0")
        return v


class ReminderRuleUpdate(BaseModel):
    name: Optional[str] = None
    trigger_type: Optional[TriggerType] = None
    days_offset: Optional[int] = None
    is_active: Optional[bool] = None

    @field_validator("days_offset")
    @classmethod
    def must_be_non_negative(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 0:
            raise ValueError("days_offset must be >= 0")
        return v


class ReminderRuleResponse(BaseModel):
    id: int
    user_id: int
    name: str
    trigger_type: TriggerType
    days_offset: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# ReminderLog schemas
# ---------------------------------------------------------------------------


class ReminderLogResponse(BaseModel):
    id: int
    invoice_id: int
    rule_id: Optional[int] = None
    sent_at: datetime
    status: ReminderStatus
    email_to: str
    subject: str
    error_message: Optional[str] = None

    model_config = {"from_attributes": True}
