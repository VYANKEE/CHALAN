"""
One-off demo-image generator - NOT part of the app, NOT part of the
train/dev/test split (writes to data/demo_samples/, never touches
data/synthetic/). Produces a handful of fresh synthetic Indian invoices
you can drag-and-drop into the live app to try out the new staged-upload /
parallel-progress UI (Phase 14) without needing a real photographed bill.

Two are forced to business_type="restaurant" specifically so you can see
the Phase 13 Fix 4 POS-noise lines (Cashier:/Token No.:/Dine In: etc.) in
a clean, legible image - useful to visually show "this is what the model
was trained to ignore" in an interview, next to the real Dhaba Punjabi
photo where the same lines are printed.

Usage (run from the project root, same venv as the API - needs only PIL,
no GPU/CUDA, no model loading):
    python scripts/generate_demo_samples.py [n_random]

Writes data/demo_samples/demo_01_restaurant.png, demo_02_restaurant.png,
then demo_03.png.. demo_0N.png (random business type each, N = n_random,
default 4). Prints each file's business type and vendor name as it goes
so you know what landed in which file before uploading.
"""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, "src/data")

import src.data.generate_synthetic as gs  # noqa: E402

OUT_DIR = Path("data/demo_samples")


def _vendor_text(words, tags):
    """Pulls the HEADER.VENDOR span back out of the tagged words, just for
    the printed summary below - doesn't affect the saved image at all."""
    out = []
    for w, t in zip(words, tags):
        if t.endswith("HEADER.VENDOR"):
            out.append(w)
    return " ".join(out) if out else "(not tagged)"


def _render_forced(business_type: str, seed: int):
    """render_invoice() picks its business type internally via
    _pick_business_type(rng) - temporarily pin that so we can force
    "restaurant" for the two demo images that should show the Fix 4
    noise lines, instead of hoping a random seed lands on it (13% odds
    per call, not worth the retry loop for a one-off demo script)."""
    original = gs._pick_business_type
    gs._pick_business_type = lambda rng: business_type
    try:
        rng = random.Random(seed)
        return gs.render_invoice(rng)
    finally:
        gs._pick_business_type = original


def main():
    n_random = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    plan = [("restaurant", 101), ("restaurant", 202)]
    plan += [(None, 1000 + i) for i in range(n_random)]

    for i, (forced_type, seed) in enumerate(plan, start=1):
        if forced_type:
            img, words, bboxes, tags = _render_forced(forced_type, seed)
            label = forced_type
        else:
            rng = random.Random(seed)
            img, words, bboxes, tags = gs.render_invoice(rng)
            label = "random"

        name = f"demo_{i:02d}_{label}.png" if forced_type else f"demo_{i:02d}.png"
        out_path = OUT_DIR / name
        img.save(out_path)
        print(f"{out_path}  (business_type={label}, vendor={_vendor_text(words, tags)!r}, "
              f"{len(words)} words, {img.size[0]}x{img.size[1]})")

    print(f"\n{len(plan)} demo images written to {OUT_DIR}/ - drag any of these into the app.")


if __name__ == "__main__":
    main()
