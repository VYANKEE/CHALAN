"""
GET /sample-data - "Download sample data" button ke liye (Core UX requirement
#2, project-plan.md). Ek zip banake serve karta hai jisme data/samples/ ke
saare files hon - chhota curated set (CORD test images + synthetic Phase 5
images). Bundle khud Phase 9 me build hoga; abhi endpoint kaam karta hai aur
clean 404 deta hai agar bundle abhi nahi bana.
"""
import io
import os
import zipfile

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from src.api.config import settings

router = APIRouter()


@router.get("/sample-data")
def download_sample_data():
    if not os.path.isdir(settings.sample_data_dir) or not os.listdir(settings.sample_data_dir):
        raise HTTPException(
            status_code=404,
            detail="Sample data bundle not built yet (Phase 9 task - a handful of CORD test "
                   "images + synthetic Phase 5 images will be added to data/samples/).",
        )

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for fname in os.listdir(settings.sample_data_dir):
            zf.write(os.path.join(settings.sample_data_dir, fname), arcname=fname)
    buf.seek(0)

    return StreamingResponse(
        buf, media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=sample_invoices.zip"},
    )
