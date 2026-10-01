"""Pydantic request/response schemas - API contract, DB model se jaanbujh kar
alag rakha hai taaki internal DB shape aur external API shape independently
badal sakein."""
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class JobOut(BaseModel):
    id: str
    filename: str
    status: str
    result: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    review_notes: Optional[dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReviewIn(BaseModel):
    """Body for PATCH /jobs/{id}/review - one comment on one low-confidence
    field. action is "sent" (flagged to the review team) or "resolved"
    (a person has signed off on it)."""

    field_key: str
    comment: str = ""
    action: str


class UploadResponse(BaseModel):
    jobs: list[JobOut]
