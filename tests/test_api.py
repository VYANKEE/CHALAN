import io
import json
import os

os.environ["DATABASE_URL"] = "sqlite:///./test_invoice.db"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["INFERENCE_BACKEND"] = "dummy"
os.environ["UPLOAD_DIR"] = "/tmp/invoice_api/test_uploads"

if os.path.exists("test_invoice.db"):
    os.remove("test_invoice.db")

import pytest
from fastapi.testclient import TestClient

from src.api.celery_app import celery_app

celery_app.conf.task_always_eager = True
celery_app.conf.task_eager_propagates = True

from src.api.database import Base, engine  # noqa: E402
from src.api.main import app  # noqa: E402

Base.metadata.create_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


def _make_png_bytes():
    from PIL import Image

    img = Image.new("RGB", (100, 100), color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_metrics(client):
    r = client.get("/metrics")
    assert r.status_code == 200
    assert "http_requests_total" in r.text


def test_upload_single_and_bulk(client):
    files = [
        ("files", ("receipt1.png", _make_png_bytes(), "image/png")),
        ("files", ("receipt2.png", _make_png_bytes(), "image/png")),
    ]
    r = client.post("/upload", files=files)
    assert r.status_code == 200
    data = r.json()
    assert len(data["jobs"]) == 2
    for job in data["jobs"]:
        # eager Celery mode + dummy backend -> task runs synchronously within the request
        assert job["status"] == "done"
        assert job["result"]["backend"] == "dummy"
        assert "HEADER.VENDOR" in job["result"]["fields"]


def test_upload_rejects_bad_extension(client):
    buf = io.BytesIO(b"not an image")
    r = client.post("/upload", files=[("files", ("bad.txt", buf, "text/plain"))])
    assert r.status_code == 400


def test_upload_empty_rejected(client):
    r = client.post("/upload", files=[])
    assert r.status_code in (400, 422)


def test_get_job_and_list(client):
    r = client.post("/upload", files=[("files", ("r3.png", _make_png_bytes(), "image/png"))])
    job_id = r.json()["jobs"][0]["id"]

    r2 = client.get(f"/jobs/{job_id}")
    assert r2.status_code == 200
    assert r2.json()["id"] == job_id

    r3 = client.get("/jobs")
    assert r3.status_code == 200
    assert any(j["id"] == job_id for j in r3.json())


def test_get_job_not_found(client):
    r = client.get("/jobs/does-not-exist")
    assert r.status_code == 404


def test_sample_data_404_when_empty(client):
    r = client.get("/sample-data")
    assert r.status_code == 404


def test_status_bus_pubsub_roundtrip():
    """Redis pub/sub bridge (status_bus.py) ko directly test karte hain -
    ye websocket ke andar jo mechanism use hota hai, usko websocket HTTP
    layer ki timing-sensitivity ke bina verify karta hai."""
    from src.api.status_bus import get_pubsub, publish_status

    pubsub = get_pubsub()
    pubsub.get_message(timeout=1.0)  # subscribe confirmation drain karo

    publish_status("job123", "done", result={"ok": True})

    msg = None
    for _ in range(10):
        msg = pubsub.get_message(timeout=0.5)
        if msg and msg["type"] == "message":
            break
    assert msg is not None
    payload = json.loads(msg["data"])
    assert payload["job_id"] == "job123"
    assert payload["status"] == "done"
    assert payload["result"] == {"ok": True}
    pubsub.close()


def test_websocket_connects(client):
    with client.websocket_connect("/ws/jobs"):
        pass  # connect + clean disconnect, koi immediate error nahi aana chahiye
