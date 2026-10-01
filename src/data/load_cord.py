"""
Apna khud ka CORD loader - HF ke flaky loading script pe depend nahi karta.
Ab data/raw/CORD/{train,dev,test}/{image,json} me local files hain (already
download ho chuki), isliye seedha unhi ko parse karenge.

Format samajhna zaroori hai: har receipt ke json me "valid_line" hoti hai -
ek list jisme har item ek "line" hai (jaise ek receipt row), jisme:
  - "words": us line ke words, har word ka apna quad (4-corner bounding box)
  - "category": us poori line ka label (jaise "menu.nm" = item name,
    "total.total_price" = total amount, "other" = kuch important nahi)

Hum har WORD ko token banate hain, BIO tagging scheme use karke:
  - "other" category ke words -> label "O" (Outside, kuch nahi)
  - kisi field ke pehle word -> "B-<FIELD>" (Beginning)
  - usi field ke baad wale words -> "I-<FIELD>" (Inside, continuation)
Ye BIO scheme hi hai jisse model per-word predict karke fields reconstruct
karta hai - LayoutLMv3 isi format me train hota hai.
"""
import json
import os
from pathlib import Path

from PIL import Image

RAW_DIR = Path("data/raw/CORD")

LABELS = [
    "O", "B-MENU.NM", "B-MENU.NUM", "B-MENU.UNITPRICE", "B-MENU.CNT",
    "B-MENU.DISCOUNTPRICE", "B-MENU.PRICE", "B-MENU.ITEMSUBTOTAL",
    "B-MENU.VATYN", "B-MENU.ETC", "B-MENU.SUB_NM", "B-MENU.SUB_UNITPRICE",
    "B-MENU.SUB_CNT", "B-MENU.SUB_PRICE", "B-MENU.SUB_ETC",
    "B-VOID_MENU.NM", "B-VOID_MENU.PRICE", "B-SUB_TOTAL.SUBTOTAL_PRICE",
    "B-SUB_TOTAL.DISCOUNT_PRICE", "B-SUB_TOTAL.SERVICE_PRICE",
    "B-SUB_TOTAL.OTHERSVC_PRICE", "B-SUB_TOTAL.TAX_PRICE", "B-SUB_TOTAL.ETC",
    "B-TOTAL.TOTAL_PRICE", "B-TOTAL.TOTAL_ETC", "B-TOTAL.CASHPRICE",
    "B-TOTAL.CHANGEPRICE", "B-TOTAL.CREDITCARDPRICE", "B-TOTAL.EMONEYPRICE",
    "B-TOTAL.MENUTYPE_CNT", "B-TOTAL.MENUQTY_CNT",
    "I-MENU.NM", "I-MENU.NUM", "I-MENU.UNITPRICE", "I-MENU.CNT",
    "I-MENU.DISCOUNTPRICE", "I-MENU.PRICE", "I-MENU.ITEMSUBTOTAL",
    "I-MENU.VATYN", "I-MENU.ETC", "I-MENU.SUB_NM", "I-MENU.SUB_UNITPRICE",
    "I-MENU.SUB_CNT", "I-MENU.SUB_PRICE", "I-MENU.SUB_ETC",
    "I-VOID_MENU.NM", "I-VOID_MENU.PRICE", "I-SUB_TOTAL.SUBTOTAL_PRICE",
    "I-SUB_TOTAL.DISCOUNT_PRICE", "I-SUB_TOTAL.SERVICE_PRICE",
    "I-SUB_TOTAL.OTHERSVC_PRICE", "I-SUB_TOTAL.TAX_PRICE", "I-SUB_TOTAL.ETC",
    "I-TOTAL.TOTAL_PRICE", "I-TOTAL.TOTAL_ETC", "I-TOTAL.CASHPRICE",
    "I-TOTAL.CHANGEPRICE", "I-TOTAL.CREDITCARDPRICE", "I-TOTAL.EMONEYPRICE",
    "I-TOTAL.MENUTYPE_CNT", "I-TOTAL.MENUQTY_CNT",
    # --- Phase 5: synthetic Indian invoices ke naye fields (CORD me nahi the) ---
    # Purane 61 labels ke BAAD appended (beech me nahi) - taaki unki id same
    # rahe aur trained classifier head ke pehle 61 output dims ka meaning na badle.
    "B-HEADER.VENDOR", "B-HEADER.GSTIN", "B-HEADER.INVOICENO",
    "B-HEADER.INVOICEDATE", "B-MENU.HSN", "B-SUB_TOTAL.CGST_PRICE",
    "B-SUB_TOTAL.SGST_PRICE",
    "I-HEADER.VENDOR", "I-HEADER.GSTIN", "I-HEADER.INVOICENO",
    "I-HEADER.INVOICEDATE", "I-MENU.HSN", "I-SUB_TOTAL.CGST_PRICE",
    "I-SUB_TOTAL.SGST_PRICE",
]


def quad_to_box(quad):
    box = (max(0, quad["x1"]), max(0, quad["y1"]), quad["x3"], quad["y3"])
    x0, y0, x1, y1 = box
    if y1 < y0:
        y0, y1 = y1, y0
    if x1 < x0:
        x0, x1 = x1, x0
    return (x0, y0, x1, y1)


def normalize_bbox(bbox, size):
    # LayoutLM 0-1000 scale me bboxes chahta hai (image size se independent)
    w, h = size
    return [
        int(1000 * bbox[0] / w), int(1000 * bbox[1] / h),
        int(1000 * bbox[2] / w), int(1000 * bbox[3] / h),
    ]


def load_split(split):
    """split: 'train', 'dev', ya 'test'. Ek list of dict records deta hai."""
    json_dir = RAW_DIR / split / "json"
    image_dir = RAW_DIR / split / "image"
    examples = []

    for json_file in sorted(json_dir.glob("*.json")):
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        image_path = image_dir / (json_file.stem + ".png")
        image = Image.open(image_path).convert("RGB")
        size = image.size

        words, bboxes, ner_tags = [], [], []
        for line in data["valid_line"]:
            line_words = [w for w in line["words"] if w["text"].strip() != ""]
            if not line_words:
                continue
            label = line["category"]
            for idx, w in enumerate(line_words):
                words.append(w["text"])
                box = normalize_bbox(quad_to_box(w["quad"]), size)
                bboxes.append(box)
                if label == "other":
                    ner_tags.append("O")
                elif idx == 0:
                    ner_tags.append("B-" + label.upper())
                else:
                    ner_tags.append("I-" + label.upper())

        examples.append({
            "id": json_file.stem,
            "words": words,
            "bboxes": bboxes,
            "ner_tags": ner_tags,
            "image_path": str(image_path),
        })

    return examples


if __name__ == "__main__":
    train = load_split("train")
    dev = load_split("dev")
    test = load_split("test")

    print(f"train: {len(train)} examples")
    print(f"dev:   {len(dev)} examples")
    print(f"test:  {len(test)} examples")

    print("\n=== Pehla training example ===")
    ex = train[0]
    print("id:", ex["id"])
    print("words (pehle 15):", ex["words"][:15])
    print("bboxes (pehle 3):", ex["bboxes"][:3])
    print("ner_tags (pehle 15):", ex["ner_tags"][:15])
    print("total words is example me:", len(ex["words"]))

    # label distribution - dekhte hain kaunse fields zyada/kam aate hain
    from collections import Counter
    all_tags = Counter()
    for ex in train:
        all_tags.update(ex["ner_tags"])
    print("\n=== Top 10 labels (train set me, count ke hisaab se) ===")
    for label, count in all_tags.most_common(10):
        print(f"  {label}: {count}")
