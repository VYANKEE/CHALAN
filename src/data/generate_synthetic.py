"""
Phase 5 - Synthetic Indian invoice generator.

KYA: PIL se seedhe invoice images banate hain (randomized layout/data),
aur usi waqt EXACT ground truth (words + pixel bboxes + BIO labels) bhi
nikal lete hain - kyunki hum khud text draw kar rahe hain, humein pata
hai har word kahan hai (CORD jaisa manual annotation ki zaroorat nahi).

KYUN naye labels: original CORD dataset me "vendor name", "GSTIN",
"invoice number", "date" - ye fields hain hi nahi (sirf MENU/SUB_TOTAL/
TOTAL cover hote hain). Lekin project ka Problem statement explicitly
"vendor, GSTIN, invoice number, date" maangta hai - ye asli gap hai jo
sirf synthetic data se fill ho sakta hai. Naye labels EXISTING 61 ke
BAAD append kiye hain (beech me insert nahi) - taaki purane 61 labels
ki id same rahe, aur trained classifier ke pehle 61 output dimensions
ka meaning na badle jab hum classifier ko 61->75 classes tak extend
karke continue-train karein.

7 naye field types (14 labels with B-/I-):
  HEADER.VENDOR, HEADER.GSTIN, HEADER.INVOICENO, HEADER.INVOICEDATE,
  MENU.HSN, SUB_TOTAL.CGST_PRICE, SUB_TOTAL.SGST_PRICE

Phase 5.1 (business_type): 30% of invoices are now "restaurant" (dhaba/
hotel/cafe) rather than always "retail" (kirana/electronics/stationery) -
added after a real photographed dhaba bill fed through the deployed model
got confidently wrong results, traced to this exact domain gap in
training data (see synthetic_catalog.py's RESTAURANT_* additions and
results-log.md). Nothing about the label scheme changed - a restaurant
invoice uses the exact same 75 BIO labels, just different vendor names,
items, and occasional bulk quantities (e.g. 29 rotis).

Phase 5.2 (more business types + currency): user explicitly asked for
more real-world Indian shop categories, not just restaurant - "medical
agriculture electronic shoes grocery jo bhi hote hai". business_type is
now a weighted choice across 7 types (general_retail, grocery, restaurant,
medical, electronics, agriculture, footwear), each with its own item
catalog + vendor-naming convention from synthetic_catalog.py.

Also added a "Rs." currency prefix on money values (70% of invoices,
randomly glued "Rs.180.00" or spaced "Rs. 180.00") - PREVIOUSLY NO
invoice (synthetic or otherwise in training) ever showed ANY currency
symbol at all, which is itself unrealistic since real Indian bills
almost always show one. We deliberately use "Rs." and NOT the actual
Rupee sign "₹": empirically tested with the project's own Tesseract
(5.3.4, default eng data) - it OCRs "Rs.1265.60" perfectly every time,
but reliably GARBLES "₹1265.60" into junk like "%1265.60" or "€1265.60"
(this is almost certainly what actually happened on the real dhaba bill's
"Brand Total EUR1265.6" misread - not a training gap we can fix by
retraining, an OCR-level limitation of tesseract's default charset for
the Rupee glyph). Training the model to expect "Rs." teaches it the
correct, OCR-reliable convention instead.
"""
import json
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, "src/data")
from synthetic_catalog import (
    GST_SLABS, INDIAN_CITIES, random_date, random_gstin, random_invoice_no,
    random_items, random_restaurant_items, random_restaurant_vendor_name,
    random_vendor_name,
    random_medical_items, random_medical_vendor_name,
    random_agriculture_items, random_agriculture_vendor_name,
    random_electronics_items, random_electronics_vendor_name,
    random_footwear_items, random_footwear_vendor_name,
    random_grocery_items, random_grocery_vendor_name,
    random_apparel_items, random_apparel_vendor_name,
    random_cosmetics_items, random_cosmetics_vendor_name,
)

# Weighted business-type mix - grocery/kirana aur general retail sabse
# common hain real India mein, isliye unko zyada weight diya hai; footwear
# sabse kam common single-item-type shop hai isliye sabse kam weight.
# Phase 5.3: apparel (jeans/shirt/t-shirt/trouser/shorts/innerwear) aur
# cosmetics/perfume add kiye - user ne explicitly maanga ki koi bhi real
# Indian bill type aaye, model "hang" (confused/garbage output) nahi hona
# chahiye. 9 types ab cover karte hain almost every common Indian retail
# bill category.
BUSINESS_TYPES = [
    ("general_retail", 0.18),
    ("grocery", 0.16),
    ("restaurant", 0.13),
    ("medical", 0.12),
    ("apparel", 0.12),
    ("electronics", 0.09),
    ("agriculture", 0.08),
    ("cosmetics", 0.07),
    ("footwear", 0.05),
]

# Har business type ka: (items_fn, vendor_fn, title choices)
BUSINESS_TYPE_CONFIG = {
    "general_retail": (random_items, random_vendor_name,
                        ["TAX INVOICE", "CASH MEMO", "BILL", "RETAIL INVOICE"]),
    "grocery": (random_grocery_items, random_grocery_vendor_name,
                ["CASH MEMO", "BILL", "TAX INVOICE"]),
    "restaurant": (random_restaurant_items, random_restaurant_vendor_name,
                   ["BILL", "DINE IN BILL", "CASH MEMO", "TAX INVOICE"]),
    "medical": (random_medical_items, random_medical_vendor_name,
                ["CASH MEMO", "TAX INVOICE", "BILL"]),
    "apparel": (random_apparel_items, random_apparel_vendor_name,
                ["TAX INVOICE", "CASH MEMO", "BILL", "RETAIL INVOICE"]),
    "electronics": (random_electronics_items, random_electronics_vendor_name,
                    ["TAX INVOICE", "RETAIL INVOICE", "BILL"]),
    "agriculture": (random_agriculture_items, random_agriculture_vendor_name,
                     ["CASH MEMO", "BILL", "TAX INVOICE"]),
    "cosmetics": (random_cosmetics_items, random_cosmetics_vendor_name,
                  ["TAX INVOICE", "CASH MEMO", "BILL", "RETAIL INVOICE"]),
    "footwear": (random_footwear_items, random_footwear_vendor_name,
                 ["TAX INVOICE", "CASH MEMO", "BILL"]),
}

# Phase 13 fix: common Indian POS-receipt staff/cashier first names - used
# only for the restaurant-header noise lines below (see render_invoice),
# so the model sees "Cashier: <name>" as a realistic O-tagged line and
# stops confusing a cashier's name with the vendor name (this is exactly
# what happened on the real "Dhaba Punjabi" bill: "Cashier: biller" got
# mistagged as HEADER.VENDOR because training never showed this pattern).
RESTAURANT_STAFF_NAMES = [
    "Ramesh", "Suresh", "Anita", "Priya", "Vikram", "Sunil", "Rahul",
    "Manoj", "Deepak", "Pooja", "Amit", "Sanjay", "Kavita", "Rajesh",
    # Phase 13 follow-up: user shared 3 more real restaurant bills (Donne
    # Biryani Palace, Mandi King Arabian Restaurant, Theory Cafe) - all on
    # the same common Indian POS template as the original Dhaba Punjabi
    # bill. Real "Cashier:" values there are often generic POS login names,
    # not human names - "biller" (confirmed twice now), "user", "NUEL".
    "biller", "user", "NUEL", "Admin", "Staff1",
]


def _pick_business_type(rng):
    types = [t for t, _ in BUSINESS_TYPES]
    weights = [w for _, w in BUSINESS_TYPES]
    return rng.choices(types, weights=weights, k=1)[0]

NEW_LABELS = [
    "B-HEADER.VENDOR", "B-HEADER.GSTIN", "B-HEADER.INVOICENO",
    "B-HEADER.INVOICEDATE", "B-MENU.HSN", "B-SUB_TOTAL.CGST_PRICE",
    "B-SUB_TOTAL.SGST_PRICE",
    "I-HEADER.VENDOR", "I-HEADER.GSTIN", "I-HEADER.INVOICENO",
    "I-HEADER.INVOICEDATE", "I-MENU.HSN", "I-SUB_TOTAL.CGST_PRICE",
    "I-SUB_TOTAL.SGST_PRICE",
]

# Windows system fonts (isi machine pe chalega) - fallback chain agar
# koi missing ho. Regular + Bold dono chahiye (header bold hota hai).
FONT_CANDIDATES_REGULAR = [
    r"C:\Windows\Fonts\arial.ttf",
    r"C:\Windows\Fonts\calibri.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # dev/testing fallback
]
FONT_CANDIDATES_BOLD = [
    r"C:\Windows\Fonts\arialbd.ttf",
    r"C:\Windows\Fonts\calibrib.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]


def _load_font(candidates, size):
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    raise FileNotFoundError(
        f"Koi font nahi mila in me se: {candidates}. "
        "Ek .ttf font ka path FONT_CANDIDATES me add karo."
    )


def draw_words(draw, x, y, text, font, fill=(20, 20, 20)):
    """
    `text` ko word-by-word draw karta hai (taaki har word ka apna EXACT
    bbox mile) aur [(word, (x0,y0,x1,y1)), ...] return karta hai.
    """
    out = []
    cur_x = x
    space_w = draw.textlength(" ", font=font)
    for word in text.split(" "):
        if word == "":
            continue
        bbox = draw.textbbox((cur_x, y), word, font=font)
        draw.text((cur_x, y), word, font=font, fill=fill)
        out.append((word, bbox))
        cur_x += draw.textlength(word, font=font) + space_w
    return out


def draw_words_right_aligned(draw, right_x, y, text, font, fill=(20, 20, 20)):
    """
    Numeric columns (Qty/Rate/Amt) real invoices me RIGHT-aligned hote
    hain - aur ye fixed-width overlap bug bhi fix karta hai (agar amount
    "25000.00" jaisa lamba ho toh left-aligned fixed-x se agle column me
    ghus jaata, right-align me hamesha right_x pe hi end hoga).
    """
    total_w = draw.textlength(text, font=font)
    return draw_words(draw, right_x - total_w, y, text, font, fill=fill)


def tag_words(words_with_boxes, field_label):
    """[(word,bbox),...] -> words, bboxes, tags (B-/I- BIO scheme)."""
    words, bboxes, tags = [], [], []
    for idx, (word, box) in enumerate(words_with_boxes):
        words.append(word)
        bboxes.append(box)
        tags.append(("B-" if idx == 0 else "I-") + field_label)
    return words, bboxes, tags


def render_invoice(rng):
    """
    Ek randomized synthetic invoice banata hai. Har baar layout ke
    parameters (width, table borders, HSN column, title text) random
    choose hote hain - taaki 4-5 hardcoded templates ke bajaye zyada
    visual diversity mile, kam code me.
    """
    width = rng.choice([650, 750, 850])
    show_hsn = rng.random() < 0.8   # 80% invoices me HSN column, 20% me nahi (real-world variation)
    has_border = rng.random() < 0.5

    # 7-way weighted business type - see module docstring / BUSINESS_TYPES.
    business_type = _pick_business_type(rng)
    items_fn, vendor_fn, title_choices = BUSINESS_TYPE_CONFIG[business_type]
    items = items_fn(rng)
    vendor = vendor_fn(rng)
    title = rng.choice(title_choices)

    # Currency prefix on money values - see module docstring for why "Rs."
    # (not "₹") was chosen. 70% of invoices show it; when shown, 50/50
    # glued "Rs.180.00" vs spaced "Rs. 180.00" (both are common in the
    # real world, e.g. printed POS bills vs handwritten/typed ones).
    show_currency = rng.random() < 0.7
    currency_glue = rng.random() < 0.5

    def money(v):
        s = f"{v:.2f}"
        if not show_currency:
            return s
        return f"Rs.{s}" if currency_glue else f"Rs. {s}"

    font_title = _load_font(FONT_CANDIDATES_BOLD, 26)
    font_header = _load_font(FONT_CANDIDATES_BOLD, 18)
    font_regular = _load_font(FONT_CANDIDATES_REGULAR, 15)
    font_small = _load_font(FONT_CANDIDATES_REGULAR, 13)

    city = rng.choice(INDIAN_CITIES)
    gstin = random_gstin(rng)
    invoice_no = random_invoice_no(rng)
    date = random_date(rng)
    cgst_rate = rng.choice(GST_SLABS)
    sgst_rate = cgst_rate

    row_h = 26
    n_items = len(items)
    # Phase 13 fix: restaurant invoices may draw 1-3 extra POS header noise
    # lines (Mob/Cashier/Token/Bill No./Dine In) below - reserve worst-case
    # height (3 lines * 20px) upfront so nothing overflows the canvas.
    extra_header_h = 80 if business_type == "restaurant" else 0  # 4 lines * 20px max
    height = 260 + n_items * row_h + 220 + extra_header_h

    img = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    all_words, all_bboxes, all_tags = [], [], []

    def emit(words_with_boxes, label):
        w, b, t = tag_words(words_with_boxes, label)
        all_words.extend(w)
        all_bboxes.extend(b)
        all_tags.extend(t)

    y = 20
    # --- Header: vendor name (bold, centered-ish) ---
    vendor_words = draw_words(draw, 30, y, vendor, font_header)
    emit(vendor_words, "HEADER.VENDOR")
    y += 26

    addr_words = draw_words(draw, 30, y, f"{city}, India", font_small)
    for w in addr_words:
        all_words.append(w[0]); all_bboxes.append(w[1]); all_tags.append("O")
    y += 20

    gstin_label = draw_words(draw, 30, y, "GSTIN:", font_small)
    for w in gstin_label:
        all_words.append(w[0]); all_bboxes.append(w[1]); all_tags.append("O")
    gstin_x = gstin_label[-1][1][2] + 8
    gstin_words = draw_words(draw, gstin_x, y, gstin, font_small)
    emit(gstin_words, "HEADER.GSTIN")
    y += 30

    # Phase 13 fix: real restaurant POS bills commonly print extra header
    # lines (Mob:, Cashier:, Token No.:, Bill No.:, Dine In:) that are NOT
    # part of the vendor name - added here as "O"-tagged lines (1-3 of them,
    # randomly picked, restaurant only) so the model learns to treat them as
    # noise instead of vendor text. See RESTAURANT_STAFF_NAMES above for why.
    if business_type == "restaurant":
        # Phase 13 follow-up: "Assign to: <name>" added after seeing it on
        # a real bill (Theory Cafe & Dessert Bar) - a waiter/staff
        # assignment line, same "O"-tagged-noise idea as the others.
        noise_pool = [
            lambda: f"Mob: {rng.randint(6000000000, 9999999999)}",
            lambda: f"Cashier: {rng.choice(RESTAURANT_STAFF_NAMES)}",
            lambda: f"Token No.: {rng.randint(1, 150)}",
            lambda: f"Bill No.: {rng.randint(10000, 99999)}",
            lambda: f"Dine In: T{rng.randint(1, 60)}",
            lambda: f"Assign to: {rng.choice(RESTAURANT_STAFF_NAMES)}",
        ]
        n_noise = rng.randint(1, 4)
        for line_fn in rng.sample(noise_pool, k=n_noise):
            noise_words = draw_words(draw, 30, y, line_fn(), font_small)
            for w in noise_words:
                all_words.append(w[0]); all_bboxes.append(w[1]); all_tags.append("O")
            y += 20

    draw.line([(20, y), (width - 20, y)], fill=(0, 0, 0), width=1)
    y += 10

    # --- Title ---
    draw.text((width // 2 - draw.textlength(title, font=font_title) // 2, y),
               title, font=font_title, fill=(0, 0, 0))
    y += 40

    # --- Invoice no / date row ---
    inv_label = draw_words(draw, 30, y, "Invoice No:", font_small)
    for w in inv_label:
        all_words.append(w[0]); all_bboxes.append(w[1]); all_tags.append("O")
    inv_x = inv_label[-1][1][2] + 8
    inv_words = draw_words(draw, inv_x, y, invoice_no, font_small)
    emit(inv_words, "HEADER.INVOICENO")

    date_label_x = width - 200
    date_label = draw_words(draw, date_label_x, y, "Date:", font_small)
    for w in date_label:
        all_words.append(w[0]); all_bboxes.append(w[1]); all_tags.append("O")
    date_x = date_label[-1][1][2] + 8
    date_words = draw_words(draw, date_x, y, date, font_small)
    emit(date_words, "HEADER.INVOICEDATE")
    y += 30

    draw.line([(20, y), (width - 20, y)], fill=(0, 0, 0), width=1)
    y += 8

    # --- Item table header ---
    # Numeric columns RIGHT edge se define hote hain (right-aligned).
    # Gaps actual max text width (measured via draw.textlength, guess nahi)
    # + padding se calculate kiye - taaki "25000.00" jaisa lamba rate ya
    # "100000.00" jaisa amount kabhi agle column me na ghuse.
    amt_right = width - 20
    rate_right = amt_right - 135  # Amt max ~90px ("Rs.100000.00") + padding
    qty_right = rate_right - 125  # Rate max ~85px ("Rs.25000.00") + padding
    hsn_right = qty_right - 40    # Qty max ~15px ("4") + padding
    col_x = {"sno": 25, "name": 60, "hsn_right": hsn_right,
             "qty_right": qty_right, "rate_right": rate_right,
             "amt_right": amt_right}
    headers = [("S.No", col_x["sno"]), ("Item", col_x["name"])]
    for text, right_x in headers:
        draw.text((right_x, y), text, font=font_small, fill=(0, 0, 0))
    if show_hsn:
        draw_words_right_aligned(draw, col_x["hsn_right"], y, "HSN", font_small)
    draw_words_right_aligned(draw, col_x["qty_right"], y, "Qty", font_small)
    draw_words_right_aligned(draw, col_x["rate_right"], y, "Rate", font_small)
    draw_words_right_aligned(draw, col_x["amt_right"], y, "Amt", font_small)
    y += 20
    draw.line([(20, y), (width - 20, y)], fill=(0, 0, 0), width=1)
    y += 6

    subtotal = 0.0
    for i, (name, hsn, price_range) in enumerate(items):
        # Real dhaba bills sometimes order in bulk (29 rotis) - that unusual
        # 2-digit quantity was part of what threw the model on the real
        # receipt this fix responds to, so restaurant invoices occasionally
        # (15%) generate a bulk quantity instead of the usual 1-4.
        if business_type == "restaurant" and rng.random() < 0.15:
            qty = rng.randint(5, 30)
        else:
            qty = rng.randint(1, 4)
        rate = round(rng.uniform(*price_range), 2)
        amount = round(qty * rate, 2)
        subtotal += amount

        draw.text((col_x["sno"], y), str(i + 1), font=font_regular, fill=(20, 20, 20))
        name_words = draw_words(draw, col_x["name"], y, name, font_regular)
        emit(name_words, "MENU.NM")
        if show_hsn:
            hsn_words = draw_words_right_aligned(draw, col_x["hsn_right"], y, hsn, font_regular)
            emit(hsn_words, "MENU.HSN")
        qty_words = draw_words_right_aligned(draw, col_x["qty_right"], y, str(qty), font_regular)
        emit(qty_words, "MENU.CNT")
        rate_words = draw_words_right_aligned(draw, col_x["rate_right"], y, money(rate), font_regular)
        emit(rate_words, "MENU.UNITPRICE")
        amt_words = draw_words_right_aligned(draw, col_x["amt_right"], y, money(amount), font_regular)
        emit(amt_words, "MENU.PRICE")

        y += row_h
        if has_border:
            draw.line([(20, y - 4), (width - 20, y - 4)], fill=(220, 220, 220), width=1)

    draw.line([(20, y), (width - 20, y)], fill=(0, 0, 0), width=1)
    y += 12

    cgst_amt = round(subtotal * cgst_rate / 100, 2)
    sgst_amt = round(subtotal * sgst_rate / 100, 2)
    total = round(subtotal + cgst_amt + sgst_amt, 2)

    def totals_row(label_text, value_text, field_label, bold=False):
        nonlocal y
        f = font_header if bold else font_regular
        lbl = draw_words(draw, width - 260, y, label_text, f)
        for w in lbl:
            all_words.append(w[0]); all_bboxes.append(w[1]); all_tags.append("O")
        val_words = draw_words_right_aligned(draw, width - 20, y, value_text, f)
        emit(val_words, field_label)
        y += 24 if bold else 20

    totals_row("Subtotal:", money(subtotal), "SUB_TOTAL.SUBTOTAL_PRICE")
    totals_row(f"CGST ({cgst_rate}%):", money(cgst_amt), "SUB_TOTAL.CGST_PRICE")
    totals_row(f"SGST ({sgst_rate}%):", money(sgst_amt), "SUB_TOTAL.SGST_PRICE")
    y += 4
    draw.line([(width - 260, y), (width - 20, y)], fill=(0, 0, 0), width=1)
    y += 8
    totals_row("TOTAL:", money(total), "TOTAL.TOTAL_PRICE", bold=True)

    y += 20
    footer = "Thank you, visit again!"
    fw = draw_words(draw, width // 2 - 90, y, footer, font_small)
    for w in fw:
        all_words.append(w[0]); all_bboxes.append(w[1]); all_tags.append("O")

    # canvas thoda crop/pad taaki actual content ke hisaab se ho (height overestimate tha)
    final_h = min(height, y + 40)
    img = img.crop((0, 0, width, final_h))

    return img, all_words, all_bboxes, all_tags


def generate_dataset(n, seed, out_dir):
    rng = random.Random(seed)
    out_dir = Path(out_dir)
    (out_dir / "image").mkdir(parents=True, exist_ok=True)
    (out_dir / "json").mkdir(parents=True, exist_ok=True)

    for i in range(n):
        img, words, bboxes, tags = render_invoice(rng)
        stem = f"synth_{i:04d}"
        img.save(out_dir / "image" / f"{stem}.png")
        record = {"id": stem, "words": words, "bboxes": bboxes, "ner_tags": tags,
                  "image_size": list(img.size)}
        with open(out_dir / "json" / f"{stem}.json", "w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False)

    print(f"{n} synthetic invoices generated -> {out_dir}")


if __name__ == "__main__":
    print("Test: 1 sample invoice generate kar rahe hain...")
    rng = random.Random(42)
    img, words, bboxes, tags = render_invoice(rng)
    print(f"Image size: {img.size}")
    print(f"Total words: {len(words)}")
    print("\nPehle 15 words + tags:")
    for w, t in zip(words[:15], tags[:15]):
        print(f"  {w!r:25s} {t}")
    print("\nField-tagged words (non-O):")
    for w, t in zip(words, tags):
        if t != "O":
            print(f"  {w!r:25s} {t}")

    out_path = Path("data/synthetic/_test_sample.png")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)
    print(f"\nSample image saved: {out_path}")
