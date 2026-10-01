"""
GET /jobs/{id} - polling fallback (simple, always works, no special client
support needed). GET /jobs - list all (dashboard use). WS /ws/jobs -
real-time push (preferred per UX requirement) via the Redis pub/sub bridge
in status_bus.py.
"""
import asyncio
import os
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from src.api.database import get_db
from src.api.models import Job
from src.api.schemas import JobOut, ReviewIn
from src.api.status_bus import get_pubsub

router = APIRouter()


@router.get("/jobs/{job_id}", response_model=JobOut)
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/jobs", response_model=list[JobOut])
def list_jobs(db: Session = Depends(get_db)):
    return db.query(Job).order_by(Job.created_at.desc()).all()


@router.delete("/jobs/{job_id}", status_code=204)
def delete_job(job_id: str, db: Session = Depends(get_db)):
    """Removes a job (typically a failed/test upload) and best-effort
    deletes its stored file - the DB row going away is what the UI cares
    about, a leftover file on disk is not worth failing the request over."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.file_path and os.path.exists(job.file_path):
        try:
            os.remove(job.file_path)
        except OSError:
            pass
    db.delete(job)
    db.commit()


@router.patch("/jobs/{job_id}/review", response_model=JobOut)
def review_field(job_id: str, body: ReviewIn, db: Session = Depends(get_db)):
    """Human-in-the-loop step for a low-confidence field: a reviewer
    leaves a comment and either flags it onward ("sent") or signs off on
    it ("resolved"). Stored per field-key so each field's review trail is
    independent of the others on the same job."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    notes = dict(job.review_notes or {})
    notes[body.field_key] = {
        "comment": body.comment,
        "status": body.action,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    job.review_notes = notes
    db.commit()
    db.refresh(job)
    return job


@router.websocket("/ws/jobs")
async def ws_jobs(websocket: WebSocket):
    """
    Client connect karte hi status updates milte rehte hain jab bhi koi job
    ka status badalta hai (Celery worker -> Redis pub/sub -> yahan -> client).
    pubsub.get_message() blocking hai, isliye asyncio.to_thread me chalate
    hain taaki event loop block na ho. Simple/portfolio-scope implementation
    hai - production hardening (ping/pong keepalive, explicit concurrent
    receive-task for disconnect detection) jaanbujh kar skip kiya hai
    (non-negotiables: no over-engineering).
    """
    await websocket.accept()
    pubsub = get_pubsub()
    try:
        while True:
            message = await asyncio.to_thread(pubsub.get_message, timeout=1.0)
            if message is not None and message["type"] == "message":
                data = message["data"]
                if isinstance(data, bytes):
                    data = data.decode("utf-8")
                await websocket.send_text(data)
    except (WebSocketDisconnect, RuntimeError):
        pass
    finally:
        pubsub.close()
