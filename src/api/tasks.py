"""
Celery task - actual model inference yahan chalta hai, upload endpoint se
alag process me (background). Job status DB me update hota hai + Redis
pub/sub pe broadcast hota hai (websocket clients ke liye).
"""
from src.api.celery_app import celery_app
from src.api.database import SessionLocal
from src.api.models import Job, JobStatus
from src.api.status_bus import publish_status


@celery_app.task(name="process_invoice")
def process_invoice(job_id: str):
    from src.api.inference import predict  # lazy import - model load sirf worker process me ho, API process me nahi

    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if job is None:
            return

        job.status = JobStatus.PROCESSING.value
        db.commit()
        publish_status(job_id, JobStatus.PROCESSING.value, stage="queued")

        def _on_stage(stage: str):
            # Phase 14: live sub-stage push for the frontend's per-file
            # progress cards - see status_bus.py's publish_status docstring.
            # Never touches the DB row (job.status stays "processing" the
            # whole time) - this is UI-only, ephemeral progress.
            publish_status(job_id, JobStatus.PROCESSING.value, stage=stage)

        try:
            result = predict(job.file_path, on_stage=_on_stage)
            job.status = JobStatus.DONE.value
            job.result = result
            db.commit()
            publish_status(job_id, JobStatus.DONE.value, result=result, stage="done")
        except Exception as e:
            job.status = JobStatus.FAILED.value
            job.error = str(e)
            db.commit()
            publish_status(job_id, JobStatus.FAILED.value, error=str(e), stage="failed")
    finally:
        db.close()
