"""
Phase 5 - Synthetic Indian invoices ko load_cord.load_split() jaisa hi
dict format ({id, words, bboxes, ner_tags, image_path}) me dena, taaki
training code CORD aur synthetic dono examples ko seedha mix kar sake.

KYUN alag file (load_cord.py me hi nahi daala): synthetic data ka source
format already normalize-ready hai (generate_synthetic.py ne khud hi
JSON me words/bboxes/ner_tags/image_size save kiya - CORD ke quad-based
raw format jaisa parsing yahan nahi chahiye). Alag rakhna dono loaders ko
simple rakhta hai - CORD ka XML/quad parsing logic synthetic ke saath
mix nahi hota.
"""
import json
from pathlib import Path

SYNTH_DIR = Path("data/synthetic")


def normalize_bbox(bbox, size):
    # load_cord.py jaisa hi: LayoutLM 0-1000 scale chahta hai.
    w, h = size
    x0, y0, x1, y1 = bbox
    return [
        int(1000 * x0 / w), int(1000 * y0 / h),
        int(1000 * x1 / w), int(1000 * y1 / h),
    ]


def load_split(split):
    """split: 'train', 'dev', ya 'test'. load_cord.load_split() jaisa hi format."""
    json_dir = SYNTH_DIR / split / "json"
    image_dir = SYNTH_DIR / split / "image"
    examples = []

    if not json_dir.exists():
        return examples

    for json_file in sorted(json_dir.glob("*.json")):
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        size = tuple(data["image_size"])
        bboxes = [normalize_bbox(b, size) for b in data["bboxes"]]

        examples.append({
            "id": data["id"],
            "words": data["words"],
            "bboxes": bboxes,
            "ner_tags": data["ner_tags"],
            "image_path": str(image_dir / (data["id"] + ".png")),
        })

    return examples


if __name__ == "__main__":
    for split in ["train", "dev", "test"]:
        examples = load_split(split)
        print(f"{split}: {len(examples)} examples")
        if examples:
            ex = examples[0]
            print("  id:", ex["id"])
            print("  words (pehle 10):", ex["words"][:10])
            print("  bboxes (pehle 2, normalized 0-1000):", ex["bboxes"][:2])
            print("  ner_tags (pehle 10):", ex["ner_tags"][:10])

    from collections import Counter
    train = load_split("train")
    all_tags = Counter()
    for ex in train:
        all_tags.update(ex["ner_tags"])
    print("\n=== Label distribution (synthetic train) ===")
    for label, count in all_tags.most_common(20):
        print(f"  {label}: {count}")
