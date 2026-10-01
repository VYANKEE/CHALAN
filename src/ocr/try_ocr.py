"""
Phase 0 - OCR trial, take 6.
Fix: hardcoded threshold (190) galat tha kyunki har receipt ki lighting alag
hoti hai. Ab Otsu's method use karenge - image ke apne pixel histogram se
khud best threshold nikalta hai (paper vs text ka natural split).
"""
import numpy as np
import pytesseract
from PIL import Image, ImageOps, ImageFilter
from scipy import ndimage

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
IMAGE_PATH = "data/raw/cord_samples/receipt_00000.png"
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
        m_b = sum_b / w_b
        m_f = (sum_total - sum_b) / w_f
        var_between = w_b * w_f * (m_b - m_f) ** 2
        if var_between > max_var:
            max_var = var_between
            threshold = t
    return threshold


def crop_to_receipt(image):
    gray = ImageOps.grayscale(image)
    arr = np.array(gray)
    bright_mask = (arr > 150).astype(np.uint8) * 255
    mask_img = Image.fromarray(bright_mask, mode="L")
    opened = mask_img.filter(ImageFilter.MinFilter(KERNEL)).filter(ImageFilter.MaxFilter(KERNEL))
    opened_arr = np.array(opened) > 0
    labeled, num_features = ndimage.label(opened_arr)
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


image = Image.open(IMAGE_PATH)
cropped = crop_to_receipt(image)
crop_arr = np.array(cropped)
print(f"Cropped size: {cropped.size}, pixel range: min={crop_arr.min()} max={crop_arr.max()} mean={crop_arr.mean():.1f}")

w, h = cropped.size
upscaled = cropped.resize((w * 3, h * 3), Image.LANCZOS)
up_arr = np.array(upscaled)

t = otsu_threshold(up_arr)
print(f"Otsu ne ye threshold nikala: {t}")
binary = np.where(up_arr < t, 0, 255).astype(np.uint8)
final = Image.fromarray(binary, mode="L")
final.save("data/raw/cord_samples/receipt_00000_final.png")

print("=" * 60)
for psm in [6, 4]:
    text = pytesseract.image_to_string(final, config=f"--psm {psm}")
    data = pytesseract.image_to_data(final, config=f"--psm {psm}", output_type=pytesseract.Output.DICT)
    words = [t2.strip() for t2 in data["text"] if t2.strip()]
    print(f"\n--psm {psm}: {len(words)} words")
    print("Pehle 30:", words[:30])

import sys
sys.path.insert(0, "src/data")
from load_cord import load_split
train = load_split("train")
print(f"\nGround truth total words: {len(train[0]['words'])}")
