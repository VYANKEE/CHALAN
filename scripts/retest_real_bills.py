"""
Phase 13 Fix 4 verification - one-off script, NOT part of the app, doesn't
touch the DB/Celery/websocket at all. Calls the EXACT production predict()
pipeline from src/api/inference.py (same function tasks.py calls, including
OCR -> model -> decode -> _apply_plausibility_caps) directly on the real
photographed bills on disk, so the result is byte-for-byte what the live
app would have returned, without needing uvicorn/Celery running.

Why this instead of re-uploading through the browser: predict() already IS
the whole pipeline the API calls - going through FastAPI/Celery/Redis/
websocket on top of it would only add infra round-trips, not change the
model's answer. This gets the same ground truth faster.

Usage (run from the project root, same venv as the API - needs CUDA if
INFERENCE_BACKEND=pytorch_gpu, which is this project's default):
    python scripts/retest_real_bills.py

Prints a per-bill, per-field table (value, confidence, tier - same
Auto-approve >=90% / Needs review <90% split the frontend uses) and writes
the full structured result to retest_report.json in the project root so it
can be pasted/attached straight into results-log.md.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, "src/data")
sys.path.insert(0, "src/models")

REAL_BILLS = [
    "data/real_test_samples/dhaba_punjabi.jpg",
    "data/real_test_samples/donne_biryani_palace.jpg",
    "data/real_test_samples/mandi_king_arabian.jpg",
    "data/real_test_samples/theory_cafe.jpg",
]


def tier(conf: float) -> str:
    return "Auto-approve" if conf >= 0.9 else "Needs review"


def main():
    from src.api.inference import predict
    from src.api.config import settings

    print(f"Backend: {settings.inference_backend}\n")

    report = {}
    for path in REAL_BILLS:
        if not Path(path).exists():
            print(f"!! SKIP (not found): {path}\n")
            continue

        print(f"=== {path} ===")
        result = predict(path)
        fields = result["fields"]
        report[path] = fields

        print(f"{'field':<28} | {'value':<30} | {'tier':<14} | conf")
        print("-" * 90)
        for name, f in fields.items():
            val = str(f["value"])
            val_display = (val[:27] + "...") if len(val) > 30 else val
            print(f"{name:<28} | {val_display:<30} | {tier(f['confidence']):<14} | {f['confidence']:.3f}")
        print()

    out_path = "retest_report.json"
    Path(out_path).write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"Full report written to {out_path}")


if __name__ == "__main__":
    main()
