"""
Redis pub/sub bridge - Celery worker (alag process) jab kisi job ka status
badalta hai, ek Redis channel pe publish karta hai. FastAPI process me
websocket handler usi channel ko subscribe karke connected clients ko forward
karta hai. Ye standard pattern hai background-worker -> websocket bridge ke
liye jab worker aur web server alag processes (kabhi kabhi alag machines) pe
ho sakte hain - dono sirf Redis ke through baat karte hain, ek dusre ko
directly import/call nahi karte.
"""
import json
from typing import Optional

import redis

from src.api.config import settings

_redis_client = redis.from_url(settings.redis_url)
JOB_STATUS_CHANNEL = "job_status_updates"


def publish_status(
    job_id: str,
    status: str,
    result: Optional[dict] = None,
    error: Optional[str] = None,
    stage: Optional[str] = None,
):
    """`stage` is a Phase 14 addition (richer live UI): a fine-grained,
    EPHEMERAL sub-step within the "processing" status - "ocr" / "model" /
    "decoding" - published right before tasks.py actually does that step,
    so the frontend can show real pipeline progress instead of a fake
    timed animation. It is never written to the DB (the Job.status column
    is unchanged: queued/processing/done/failed) - it only ever travels
    over this pub/sub message, so a client that reconnects mid-job simply
    doesn't see the in-between stages, which is fine for a live progress
    indicator (not a source of truth)."""
    payload = {"job_id": job_id, "status": status, "result": result, "error": error, "stage": stage}
    _redis_client.publish(JOB_STATUS_CHANNEL, json.dumps(payload))


def get_pubsub():
    pubsub = _redis_client.pubsub()
    pubsub.subscribe(JOB_STATUS_CHANNEL)
    return pubsub
