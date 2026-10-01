"""
POST /upload - single AUR bulk dono isi ek endpoint se (List[UploadFile]) -
alag single/bulk mode nahi (explicit user requirement, project-plan.md Core
UX requirement #1). Har file ke liye: disk pe save karo, Job row create karo
(status=queued), Celery task enqueue karo, turant job_id return karo -
processing background me hoga, upload request block nahi hoti. Ek file
1 route → per-file independent status (frontend har row apne aap update
karega, ek dusre ka wait nahi karta).
"""
import os
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from src.api.config import settings
from src.api.database import get_db
from src.api.models import Job, JobStatus
from src.api.schemas import JobOut, UploadResponse
from src.api.tasks import process_invoice

router = APIRouter()


def _validate_file(file: UploadFile):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in settings.allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"{file.filename}: unsupported file type '{ext}' (allowed: {settings.allowed_extensions})",
        )


@router.post("/upload", response_model=UploadResponse)
async def upload_invoices(files: list[UploadFile] = File(...), db: Session = Depends(get_db)):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    os.makedirs(settings.upload_dir, exist_ok=True)
    jobs = []

    for file in files:
        _validate_file(file)
        contents = await file.read()
        if len(contents) > settings.max_upload_mb * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail=f"{file.filename}: exceeds {settings.max_upload_mb}MB limit",
            )

        ext = os.path.splitext(file.filename)[1].lower()
        stored_name = f"{uuid.uuid4()}{ext}"
        stored_path = os.path.join(settings.upload_dir, stored_name)
        with open(stored_path, "wb") as f:
            f.write(contents)

        job = Job(filename=file.filename, file_path=stored_path, status=JobStatus.QUEUED.value)
        db.add(job)
        db.commit()
        db.refresh(job)

        process_invoice.delay(job.id)  # background me enqueue - yahan block nahi hota
        db.refresh(job)  # task ne (Celery eager mode ya already-fast worker) status badla ho
        # to response me sabse current state dikhe - real async deployment me ye harmless
        # hai (abhi tak kuch nahi badla, "queued" hi dikhega, jo sahi bhi hai).
        jobs.append(job)

    return UploadResponse(jobs=[JobOut.model_validate(j) for j in jobs])
