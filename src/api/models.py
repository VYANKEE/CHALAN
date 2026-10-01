"""
Job table - ek row per uploaded file. status: queued -> processing ->
done/failed. `result` JSON me extracted fields + per-field confidence store
hota hai (DONE hone ke baad), `error` text FAILED hone par.
"""
import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, String, Text

from src.api.database import Base


class JobStatus(str, enum.Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


def _uuid():
    return str(uuid.uuid4())


def _now():
    return datetime.now(timezone.utc)


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True, default=_uuid)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    status = Column(String, nullable=False, default=JobStatus.QUEUED.value)
    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    # Human-in-the-loop review notes: {field_key: {comment, status, updated_at}}.
    # status is "sent" (flagged to the review team) or "resolved" (a person
    # signed off on it). Keyed by field so each low-confidence field can be
    # commented on independently.
    review_notes = Column(JSON, nullable=True, default=dict)
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)
