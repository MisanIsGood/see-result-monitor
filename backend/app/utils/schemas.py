"""
Pydantic schemas for API request/response validation.
"""
import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, field_validator


# ---------------------------------------------------------------------------
# Registration schemas
# ---------------------------------------------------------------------------

class RegistrationCreate(BaseModel):
    receiver_email: EmailStr
    symbol_number: str
    date_of_birth: str  # e.g. "2065/05/15" (BS) or "2008-08-31" (AD)

    @field_validator("symbol_number")
    @classmethod
    def validate_symbol_number(cls, v: str) -> str:
        v = v.strip()
        if not re.match(r"^\d{7,10}$", v):
            raise ValueError("Symbol number must be 7–10 digits.")
        return v

    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, v: str) -> str:
        v = v.strip()
        # Accept formats like 2065/05/15, 2065-05-15, 2008/08/31
        if not re.match(r"^\d{4}[/-]\d{2}[/-]\d{2}$", v):
            raise ValueError(
                "Date of birth must be in YYYY/MM/DD or YYYY-MM-DD format. "
                "Use Nepali calendar (BS) e.g. 2065/05/15 or AD e.g. 2008/08/31."
            )
        return v


class RegistrationResponse(BaseModel):
    id: int
    receiver_email: str
    symbol_number: str
    date_of_birth: str
    is_active: bool
    result_found: bool
    email_sent: bool
    check_count: int
    last_checked_at: Optional[datetime]
    last_error: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class RegistrationStatus(BaseModel):
    id: int
    symbol_number: str
    receiver_email: str
    is_active: bool
    result_found: bool
    result_data: Optional[str]
    email_sent: bool
    check_count: int
    last_checked_at: Optional[datetime]
    last_error: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Monitor control schemas
# ---------------------------------------------------------------------------

class MonitorStatusResponse(BaseModel):
    is_monitoring: bool
    active_registrations: int
    interval_seconds: int
    message: str


class MonitorControlResponse(BaseModel):
    success: bool
    message: str
    is_monitoring: bool


# ---------------------------------------------------------------------------
# Log schemas
# ---------------------------------------------------------------------------

class ActivityLogResponse(BaseModel):
    id: int
    registration_id: Optional[int]
    event_type: str
    message: str
    symbol_number: Optional[str]
    source_url: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# General
# ---------------------------------------------------------------------------

class MessageResponse(BaseModel):
    message: str
    success: bool = True
