"""
FastAPI app entrypoint. /health aur /metrics (Prometheus text format, basic
request counter) + upload/jobs/sample-data routers mount karta hai. CORS
open rakha hai (portfolio demo - frontend alag origin/port se chalega, Vite
dev server 5173 waghera).

Run: uvicorn src.api.main:app --reload   (project root se)
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text

from src.api.database import Base, engine
from src.api.routers import jobs, sample_data, upload

Base.metadata.create_all(bind=engine)

# Lightweight in-place migration (no Alembic in this project - portfolio
# scope). create_all() above only creates tables that don't exist yet, so
# an already-created `jobs` table from before the review feature needs
# this column added explicitly. Idempotent / safe to run on every start.
_inspector = inspect(engine)
if "jobs" in _inspector.get_table_names():
    _existing_cols = {c["name"] for c in _inspector.get_columns("jobs")}
    if "review_notes" not in _existing_cols:
        with engine.begin() as _conn:
            _conn.execute(text("ALTER TABLE jobs ADD COLUMN review_notes JSON"))

app = FastAPI(title="Invoice Document Intelligence API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router, tags=["upload"])
app.include_router(jobs.router, tags=["jobs"])
app.include_router(sample_data.router, tags=["sample-data"])

_request_count = {"total": 0}


@app.middleware("http")
async def count_requests(request: Request, call_next):
    _request_count["total"] += 1
    return await call_next(request)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/metrics")
def metrics():
    # Prometheus text format, ek basic counter - Phase 11 me chahiye to
    # prometheus-client library se replace/expand kiya ja sakta hai.
    return (
        "# HELP http_requests_total Total HTTP requests\n"
        "# TYPE http_requests_total counter\n"
        f"http_requests_total {_request_count['total']}\n"
    )
