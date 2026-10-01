"""
Quick sanity check - 10 sample images pe OCR chala ke dekhte hain average
kitna kharab/achha hai, poori baseline banane se pehle.
"""
import glob
import numpy as np
import pytesseract
from PIL import Image, ImageOps, ImageFilter
from scipy import ndimage

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
KERNEL = 31


def otsu_threshold(arr):
    hist, _ = np.histogram(arr, bins=256, range=(0, 256))
    total = arr.size
    sum_total = np.dot(np.arange(256), hist)
    sum_b, w_b, max_var, threshold = 0, 0, 0, 0
    for t in range(256):
        w_b += hist[t]
        if w_b == 0:
            continue
        w_f = total - w_b
        if w_f == 0:
            break
        sum_b += t * hist[t]
        m_b, m_f = sum_b / w_b, (sum_total - sum_b) / w_f
        var_between = w_b * w_f * (m_b - m_f) ** 2
        if var_between > max_var:
            max_var, threshold = var_between, t
    return threshold


def crop_to_receipt(image):
    gray = ImageOps.grayscale(image)
    arr = np.array(gray)
    bright_mask = (arr > 150).astype(np.uint8) * 255
    mask_img = Image.fromarray(bright_mask, mode="L")
    opened = mask_img.filter(ImageFilter.MinFilter(KERNEL)).filter(ImageFilter.MaxFilter(KERNEL))
    opened_arr = np.array(opened) > 0
    labeled, num_features = ndimage.label(opened_arr)
    if num_features == 0:
        return gray
    sizes = ndimage.sum(opened_arr, labeled, range(1, num_features + 1))
    largest_label = int(np.argmax(sizes)) + 1
    component_mask = labeled == largest_label
    rows = np.any(component_mask, axis=1)
    cols = np.any(component_mask, axis=0)
    y0, y1 = np.where(rows)[0][[0, -1]]
    x0, x1 = np.where(cols)[0][[0, -1]]
    padding = 10
    x0, y0 = max(0, x0 - padding), max(0, y0 - padding)
    x1, y1 = min(arr.shape[1], x1 + padding), min(arr.shape[0], y1 + padding)
    return gray.crop((x0, y0, x1, y1))


def ocr_word_count(path):
    image = Image.open(path)
    cropped = crop_to_receipt(image)
    w, h = cropped.size
    upscaled = cropped.resize((w * 3, h * 3), Image.LANCZOS)
    up_arr = np.array(upscaled)
    t = otsu_threshold(up_arr)
    binary = np.where(up_arr < t, 0, 255).astype(np.uint8)
    final = Image.fromarray(binary, mode="L")
    data = pytesseract.image_to_data(final, config="--psm 4", output_type=pytesseract.Output.DICT)
    words = [w2.strip() for w2 in data["text"] if w2.strip()]
    return words


import sys
sys.path.insert(0, "src/data")
from load_cord import load_split
train = load_split("train")
gt_by_id = {ex["id"]: len(ex["words"]) for ex in train}

paths = sorted(glob.glob("data/raw/cord_samples/receipt_*.png"))
paths = [p for p in paths if "cropped" not in p and "enhanced" not in p and "final" not in p]

print(f"{'receipt':<20} {'ocr_words':>10} {'gt_words':>10} {'ratio':>8}")
for p in paths:
    receipt_id = p.split("\\")[-1].split("/")[-1].replace(".png", "")
    words = ocr_word_count(p)
    gt_count = gt_by_id.get(receipt_id, 0)
    ratio = len(words) / gt_count if gt_count else 0
    print(f"{receipt_id:<20} {len(words):>10} {gt_count:>10} {ratio:>8.2f}")
