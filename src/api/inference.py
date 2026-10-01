"""
Model inference wrapper - single place jahan se actual field-extraction
prediction hoti hai. Backend `settings.inference_backend` se choose hota hai:
  - pytorch_gpu / pytorch_cpu: models/lora_combined_v1 (LoRA adapter),
    direct PyTorch inference (Phase 4-6 ka wahi model).
  - onnx_int8: Phase 7 ka quantized model - halka, CPU-only deployment ke
    liye.
  - dummy: koi model load nahi karta, fixed fake result deta hai - isse
    tests/CI GPU ya model checkpoint ke bina bhi chal sakte hain.

KYUN ek hi jagah se: kal koi naya backend add karna ho (batched GPU serving,
ya koi aur), sirf yahan badlega - Celery task ya API routes ko pata hi nahi
chalega.

OCR NOTE (important): CORD/synthetic training-eval data me words+boxes
GROUND TRUTH hote hain (pehle se diye gaye). Ek real uploaded photo ke paas
ye nahi hota - use nikaalne ke liye OCR chahiye. Isliye yahan pytesseract
(Baseline A, Phase 2 wala hi tool) se words + bounding boxes nikaalte hain.
Honest caveat, results-log.md ke Baseline A section me already documented:
Tesseract ka raw text-extraction quality CORD ke low-res/photographed
receipts pe kamzor nikla tha (2% end-to-end via regex baseline) - saaf
machine-rendered images (jaise humari Phase 5 synthetic invoices) pe OCR
kaafi better perform karega. Ye ek real, acknowledged limitation hai jo is
demo ke saath honestly document hogi (Phase 12 README/limitations section),
"fix" karne ki koshish nahi (naya OCR engine banana over-engineering hoga -
non-negotiables dekho).
"""
import os
import sys
from functools import lru_cache
from typing import Optional

from src.api.config import settings

sys.path.insert(0, "src/data")
sys.path.insert(0, "src/models")

# Windows ka default Tesseract install path (installer PATH me add nahi
# karta agar box uncheck ho) - auto-detect fallback ke liye.
_WINDOWS_DEFAULT_TESSERACT = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
_tesseract_configured = False


def _configure_tesseract_cmd():
    """Ek baar chalta hai (process lifetime me). settings.tesseract_cmd agar
    set hai to wahi use karo (explicit override, sabse zyada priority). Nahi
    to PATH me "tesseract" already dhoondh sakte ho to kuch mat chhedo. Agar
    PATH me nahi mila aur Windows ka standard install path disk pe exist
    karta hai, wahi use kar lo - taaki installer ne PATH me add na kiya ho
    (ya terminal restart na hui ho) tab bhi kaam chale."""
    global _tesseract_configured
    if _tesseract_configured:
        return
    _tesseract_configured = True

    import shutil

    import pytesseract

    if settings.tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd
        return

    if shutil.which(pytesseract.pytesseract.tesseract_cmd):
        return  # PATH me already mil gaya, kuch karne ki zaroorat nahi

    if os.name == "nt" and os.path.isfile(_WINDOWS_DEFAULT_TESSERACT):
        pytesseract.pytesseract.tesseract_cmd = _WINDOWS_DEFAULT_TESSERACT


def _dummy_predict(image_path: str) -> dict:
    return {
        "fields": {
            "HEADER.VENDOR": {"value": "DUMMY VENDOR", "confidence": 0.99},
            "TOTAL.TOTAL_PRICE": {"value": "100.00", "confidence": 0.95},
        },
        "backend": "dummy",
    }


def _ocr_words_and_boxes(image_path: str):
    import pytesseract
    from PIL import Image

    _configure_tesseract_cmd()

    image = Image.open(image_path).convert("RGB")
    w, h = image.size
    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

    words, boxes = [], []
    for i in range(len(data["text"])):
        text = data["text"][i].strip()
        if not text:
            continue
        x, y, bw, bh = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
        # LayoutLM 0-1000 normalized scale (load_cord.py/load_synthetic.py ka
        # wahi convention - training data isi scale pe tha).
        box = [
            int(1000 * x / w), int(1000 * y / h),
            int(1000 * (x + bw) / w), int(1000 * (y + bh) / h),
        ]
        words.append(text)
        boxes.append(box)

    if not words:
        raise ValueError("OCR could not extract any text from this image")
    return words, boxes


@lru_cache(maxsize=1)
def _load_pytorch_model():
    import torch
    from cord_torch_dataset import ID2LABEL, LABEL2ID, PROCESSOR
    from load_cord import LABELS
    from peft import PeftModel
    from train_lora import MODEL_NAME
    from transformers import AutoModelForTokenClassification

    base = AutoModelForTokenClassification.from_pretrained(
        MODEL_NAME, num_labels=len(LABELS), id2label=ID2LABEL, label2id=LABEL2ID,
    )
    model = PeftModel.from_pretrained(base, settings.lora_adapter_dir)
    device = "cuda" if (settings.inference_backend == "pytorch_gpu" and torch.cuda.is_available()) else "cpu"
    model = model.to(device)
    model.eval()
    return model, PROCESSOR, ID2LABEL, device


@lru_cache(maxsize=1)
def _load_onnx_session():
    import onnxruntime as ort
    from cord_torch_dataset import ID2LABEL, PROCESSOR

    session = ort.InferenceSession(settings.onnx_int8_path, providers=["CPUExecutionProvider"])
    return session, PROCESSOR, ID2LABEL


def _decode_fields_with_confidence(words, tags, confidences):
    """calibrate.py (Phase 6) ka wahi BIO-decode logic - MIN confidence per
    field span (weakest-link, conservative choice for STP)."""
    fields = {}
    current_field, current_words, current_confs = None, [], []

    def flush():
        if current_field and current_words:
            fields[current_field] = {
                "value": " ".join(current_words),
                "confidence": min(current_confs),
            }

    for word, tag, conf in zip(words, tags, confidences):
        if tag == "O":
            flush()
            current_field, current_words, current_confs = None, [], []
        elif tag.startswith("B-"):
            flush()
            current_field, current_words, current_confs = tag[2:], [word], [conf]
        elif tag.startswith("I-"):
            if current_field == tag[2:]:
                current_words.append(word)
                current_confs.append(conf)
            else:
                flush()
                current_field, current_words, current_confs = tag[2:], [word], [conf]
    flush()
    return fields


# Phase 13 follow-up fix: the original version of this cap used a DENYLIST
# of "bad" currency symbols (EUR/GBP/JPY/$). Real-world testing (2026-10-01,
# real "Dhaba Punjabi" bill re-test, see results-log.md) found a genuine
# hole in that approach: MENU.PRICE = "20.¢" (a stray cent-sign glyph,
# OCR garbling a torn/truncated printed amount) was auto-approved at 98.9%
# confidence, because it HAS a digit (so the no-digit check didn't fire)
# and "¢" wasn't on the denylist (so the symbol check didn't fire either).
# A denylist can only ever cover symbols we already thought of - it will
# always be one OCR garble behind. Switched to an ALLOWLIST instead: a
# price/count value must look like an actual number (optionally "Rs."
# prefixed) top to bottom, nothing else. Anything that doesn't match -
# any stray symbol, any leaked label text like "CGST" or "Price", any
# trailing junk - gets capped, regardless of what new garbling shows up.
import re  # noqa: E402 (local import kept next to the regexes that use it)

_VALID_PRICE_RE = re.compile(r"^(?:Rs\.?\s?)?[\d,]+(?:\.\d{1,2})?$", re.IGNORECASE)
_VALID_CNT_RE = re.compile(r"^\d+$")


def _apply_plausibility_caps(fields: dict) -> dict:
    """Honest safety net, not an accuracy fix: the model's softmax confidence
    was calibrated (Phase 6) on CORD + synthetic dev/test data, which is
    IN-distribution - it says nothing about how trustworthy that confidence
    is on a genuinely out-of-distribution real photo (e.g. a restaurant bill,
    when training only ever saw retail/kirana-style invoices - see
    synthetic_catalog.py). A model can be confidently wrong on OOD input;
    that's a well-known limitation of post-hoc calibration, not something
    this cap "fixes".

    What this DOES do: for fields whose name says they should be a price or
    a count (...PRICE / ...CNT), the DECODED TEXT must match a strict
    allowlist pattern (plain digits, optional thousands commas, optional
    "Rs." prefix, optional 1-2 decimal digits) to be trusted at all -
    anything else (no digits, a stray symbol, leaked label text, trailing
    junk) gets capped into the review tier, regardless of what the model's
    raw confidence said. This never changes a value, only how much the
    system trusts it.
    """
    CAP = 0.3  # below both the 0.7 "review" and 0.9 "auto" thresholds

    for key, field in fields.items():
        value = field["value"].strip()

        if key.endswith("PRICE"):
            if not _VALID_PRICE_RE.match(value):
                field["confidence"] = min(field["confidence"], CAP)
        elif key.endswith("CNT"):
            if not _VALID_CNT_RE.match(value):
                field["confidence"] = min(field["confidence"], CAP)

    return fields


def predict(image_path: str, on_stage=None) -> dict:
    """`on_stage` is a Phase 14 addition (richer live UI): an optional
    callback invoked with a short stage name ("ocr" / "model" / "decoding")
    right before that step starts, purely so a caller (tasks.py) can push a
    live progress update. It changes nothing about the actual prediction -
    every existing caller that doesn't pass it (eval scripts, calibrate.py,
    export_quantize.py) behaves exactly as before, since the default is a
    no-op."""
    def _stage(name):
        if on_stage is not None:
            on_stage(name)

    if settings.inference_backend == "dummy":
        return _dummy_predict(image_path)

    _stage("ocr")
    words, boxes = _ocr_words_and_boxes(image_path)

    import numpy as np
    from PIL import Image

    _stage("model")
    if settings.inference_backend in ("pytorch_gpu", "pytorch_cpu"):
        import torch

        model, processor, id2label, device = _load_pytorch_model()
        image = Image.open(image_path).convert("RGB")
        encoding = processor(image, words, boxes=boxes, truncation=True,
                              padding="max_length", max_length=320, return_tensors="pt")
        word_ids = encoding.word_ids(batch_index=0)
        enc = {k: v.to(device) for k, v in encoding.items()}
        with torch.no_grad():
            logits = model(**enc).logits.squeeze(0).cpu().numpy()
    elif settings.inference_backend == "onnx_int8":
        session, processor, id2label = _load_onnx_session()
        image = Image.open(image_path).convert("RGB")
        encoding = processor(image, words, boxes=boxes, truncation=True,
                              padding="max_length", max_length=320, return_tensors="pt")
        word_ids = encoding.word_ids(batch_index=0)
        feed = {name: encoding[name].numpy() for name in ["input_ids", "attention_mask", "bbox", "pixel_values"]}
        logits = session.run(None, feed)[0][0]
    else:
        raise ValueError(f"Unknown inference_backend: {settings.inference_backend}")

    def softmax(x):
        x = x - np.max(x, axis=-1, keepdims=True)
        e = np.exp(x)
        return e / np.sum(e, axis=-1, keepdims=True)

    probs = softmax(logits)
    preds = probs.argmax(-1)

    _stage("decoding")
    pred_tags, pred_confs, prev_word_id = [], [], None
    for idx, word_id in enumerate(word_ids):
        if word_id is None:
            continue
        if word_id != prev_word_id:
            pred_tags.append(id2label[int(preds[idx])])
            pred_confs.append(float(probs[idx][preds[idx]]))
            prev_word_id = word_id

    words_truncated = words[:len(pred_tags)]
    fields = _decode_fields_with_confidence(words_truncated, pred_tags, pred_confs)
    fields = _apply_plausibility_caps(fields)
    return {"fields": fields, "backend": settings.inference_backend}
