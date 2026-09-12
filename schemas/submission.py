from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class PublicSubmissionRequest(BaseModel):
    """Schema for public submission endpoint."""
    widget_id: str = Field(..., min_length=1, max_length=100)
    data: Dict[str, Any] = Field(..., min_length=1, max_length=50)
    hp_field: str = Field(default="", max_length=1000)  # Honeypot field


class SubmissionCreate(BaseModel):
    """Internal schema for creating submissions."""
    widget_id: str
    tenant_id: int
    submitted_data: Dict[str, Any]
    ip_address: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    user_agent: Optional[str] = None
    idempotency_key: Optional[str] = None


class SubmissionResponse(BaseModel):
    id: int
    widget_id: str
    tenant_id: int
    submitted_data: Dict[str, Any]
    ip_address: Optional[str]
    country: Optional[str]
    city: Optional[str]
    user_agent: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class SubmissionSuccess(BaseModel):
    """Response for successful submission."""
    success: bool = True
    message: str = "Submission received successfully"