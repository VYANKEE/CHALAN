"""
One-off diagnostic script - NOT part of the app, doesn't touch the API/DB.
Runs the exact same OCR + LoRA model steps as src/api/inference.predict(),
but instead of only returning the final merged fields, it prints the FULL
per-word trail: what OCR read, what confidence OCR had, what BIO tag the
model assigned to that word, and what confidence the model had in that tag.

Why: the app was showing clearly wrong extracted values on a real Indian
dhaba receipt (wrong vendor name, wrong total, garbled GST lines). Before
"fixing" anything, we need to see WHERE in the pipeline it goes wrong - bad
OCR text, or the model mis-tagging words that OCR read correctly. Guessing
would violate the project's own "no fake fixes" rule.

Usage (run from the project root, same venv as the API):
    python scripts/debug_predict.py data/uploads/<file>.jpeg

Writes a full JSON report next to the script's output path (default:
debug_report.json in the project root) and also prints a compact table to
stdout so you can just paste the terminal output back.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, "src/data")
sys.path.insert(0, "src/models")


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/debug_predict.py <image_path> [output_json_path]")
        sys.exit(1)

    image_path = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) > 2 else "debug_report.json"

    from src.api.inference import _ocr_words_and_boxes, _load_pytorch_model, _decode_fields_with_confidence

    print(f"=== OCR: {image_path} ===")
    words, boxes = _ocr_words_and_boxes(image_path)
    print(f"OCR produced {len(words)} words.\n")

    import numpy as np
    import torch
    from PIL import Image

    model, processor, id2label, device = _load_pytorch_model()
    print(f"Model loaded on device: {device}\n")

    image = Image.open(image_path).convert("RGB")
    encoding = processor(image, words, boxes=boxes, truncation=True,
                          padding="max_length", max_length=320, return_tensors="pt")
    word_ids = encoding.word_ids(batch_index=0)
    enc = {k: v.to(device) for k, v in encoding.items()}
    with torch.no_grad():
        logits = model(**enc).logits.squeeze(0).cpu().numpy()

    def softmax(x):
        x = x - np.max(x, axis=-1, keepdims=True)
        e = np.exp(x)
        return e / np.sum(e, axis=-1, keepdims=True)

    probs = softmax(logits)
    preds = probs.argmax(-1)

    pred_tags, pred_confs, prev_word_id = [], [], None
    for idx, word_id in enumerate(word_ids):
        if word_id is None:
            continue
        if word_id != prev_word_id:
            pred_tags.append(id2label[int(preds[idx])])
            pred_confs.append(float(probs[idx][preds[idx]]))
            prev_word_id = word_id

    words_truncated = words[:len(pred_tags)]
    if len(words) > len(words_truncated):
        print(f"!! WARNING: {len(words)} words but max_length=320 truncated to "
              f"{len(words_truncated)} tokens - {len(words) - len(words_truncated)} words "
              f"never reached the model.\n")

    print(f"{'#':>3} | {'word':<22} | {'predicted tag':<30} | conf")
    print("-" * 75)
    per_word = []
    for i, (w, t, c) in enumerate(zip(words_truncated, pred_tags, pred_confs)):
        flag = "  <-- non-O" if t != "O" else ""
        print(f"{i:3d} | {w:<22} | {t:<30} | {c:.3f}{flag}")
        per_word.append({"word": w, "tag": t, "confidence": round(c, 4)})

    fields = _decode_fields_with_confidence(words_truncated, pred_tags, pred_confs)
    print("\n=== DECODED FIELDS (same logic as the API) ===")
    for k, v in fields.items():
        print(f"  {k:<30} = {v['value']!r}  (conf {v['confidence']:.3f})")

    report = {
        "image_path": image_path,
        "ocr_word_count": len(words),
        "model_token_count": len(words_truncated),
        "truncated": len(words) > len(words_truncated),
        "per_word": per_word,
        "decoded_fields": fields,
    }
    Path(out_path).write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"\nFull report written to {out_path}")


if __name__ == "__main__":
    main()
