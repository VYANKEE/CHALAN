"""
CORD dataset download - Attempt 2.

KYA BADLA: Azure blob link (jo script ke comments me tha) ab band ho chuka hai
("Public access is not permitted on this storage account" - Microsoft ne shayad
public access hata diya). To ab hum seedha Google Drive se download karenge,
lekin sahi tareeke se - session cookies handle karke, taaki Drive ka
"virus scan warning" page bypass ho jaye (jo pehli baar humein todla tha).

Ye standard tareeka hai bade Google Drive files scripted download karne ka.
"""
import os
import zipfile
import requests

FILE_IDS = [
    "1MqhTbcj-AHXOqYoeoh12aRUwIprzTJYI",
    "1wYdp5nC9LnHQZ2FcmOoC0eClyWvcuARU",
]

RAW_DIR = "data/raw"
os.makedirs(RAW_DIR, exist_ok=True)


def get_confirm_token(response):
    for key, value in response.cookies.items():
        if key.startswith("download_warning"):
            return value
    # naye Drive versions kabhi kabhi HTML body me token dete hain, cookie me nahi
    if "download_warning" in response.text[:5000]:
        import re
        match = re.search(r"confirm=([0-9A-Za-z_]+)", response.text)
        if match:
            return match.group(1)
    return None


def download_from_drive(file_id, dest_path):
    if os.path.exists(dest_path):
        print(f"Already downloaded: {dest_path}")
        return
    url = "https://drive.google.com/uc?export=download"
    session = requests.Session()
    response = session.get(url, params={"id": file_id}, stream=True)
    token = get_confirm_token(response)
    if token:
        response = session.get(url, params={"id": file_id, "confirm": token}, stream=True)

    total = int(response.headers.get("content-length", 0))
    downloaded = 0
    with open(dest_path, "wb") as f:
        for chunk in response.iter_content(32768):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if total:
                    print(f"\r{os.path.basename(dest_path)}: {downloaded * 100 // total}%", end="", flush=True)
                else:
                    print(f"\r{os.path.basename(dest_path)}: {downloaded / 1e6:.1f} MB", end="", flush=True)
    print()

    # sanity check: agar file bahut chhoti hai (few KB), wo zip nahi, warning page hi hoga
    size_kb = os.path.getsize(dest_path) / 1024
    if size_kb < 50:
        print(f"WARNING: {dest_path} sirf {size_kb:.1f} KB ka hai - ye asli zip nahi lagta, warning page ho sakta hai")


def print_tree(path, prefix="", max_depth=3, depth=0):
    if depth > max_depth:
        return
    try:
        entries = sorted(os.listdir(path))
    except NotADirectoryError:
        return
    for entry in entries[:10]:
        full = os.path.join(path, entry)
        print(f"{prefix}{entry}{'/' if os.path.isdir(full) else ''}")
        if os.path.isdir(full):
            print_tree(full, prefix + "  ", max_depth, depth + 1)
    if len(entries) > 10:
        print(f"{prefix}... ({len(entries) - 10} more)")


for i, file_id in enumerate(FILE_IDS, start=1):
    zip_path = os.path.join(RAW_DIR, f"CORD-1k-{i:03d}.zip")
    extract_dir = os.path.join(RAW_DIR, f"cord_extracted_{i}")

    print(f"\n=== Zip {i}: downloading ===")
    download_from_drive(file_id, zip_path)

    print(f"=== Zip {i}: extracting ===")
    try:
        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(extract_dir)
        print(f"=== Zip {i}: folder structure (top levels) ===")
        print_tree(extract_dir)
    except zipfile.BadZipFile:
        print(f"XXX Zip {i} sahi se download nahi hui (BadZipFile) - ye warning page tha, asli zip nahi.")

print("\nDone.")
