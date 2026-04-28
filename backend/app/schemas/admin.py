"""
Pydantic schemas for Admin panel request/response validation.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AdminUserResponse(BaseModel):
    """Full user record as seen by an admin, augmented with usage counters."""

    id: int
    email: str
    full_name: Optional[str] = None
    is_active: bool
    is_admin: bool
    is_verified: bool
    oauth_provider: Optional[str] = None
    created_at: datetime
    invoice_count: int = 0
    client_count: int = 0

    model_config = {"from_attributes": True}


class AdminUserStatusUpdate(BaseModel):
    """Payload for activating or deactivating a user account."""

    is_active: bool


class AdminStats(BaseModel):
    """Platform-wide aggregate statistics visible only to admins."""

    total_users: int
    active_users: int
    total_invoices: int
    total_revenue: float


class AdminLogResponse(BaseModel):
    """A single audit log entry from the admin_logs table."""

    id: int
    admin_user_id: int
    action: str
    target_type: Optional[str] = None
    target_id: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}
