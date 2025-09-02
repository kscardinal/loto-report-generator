import sys
import json
import requests
from pathlib import Path
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# -------------------------
# CONFIGURATION
# -------------------------
SERVER = os.getenv("SERVER_IP")


# -------------------------
# Load JSON and gather image filenames
# -------------------------
def extract_included_files(json_file_path: Path):
    with open(json_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    included = set()

    # Top-level image
    machine_image = data.get("machine_image")
    if machine_image:
        included.add(machine_image)

    # From each source
    sources = data.get("sources", [])
    for src in sources:
        for key in ("isolation_point", "verification_device"):
            img = src.get(key)
            if img:
                included.add(img)

    return list(included)


# -------------------------
# Step 1: Upload
# -------------------------
def upload_files(json_file: str, include_files: list):
    files = [('files', open(json_file, 'rb'))]
    for name in include_files:
        try:
            files.append(('files', open(name, 'rb')))
        except FileNotFoundError:
            print(f"[Warning] Included file not found: {name}")
    res = requests.post(f"{SERVER}/upload/", files=files)
    print("Upload response:", res.json())


# -------------------------
# Step 2: Generate PDF
# -------------------------
def generate_pdf(json_file: str):
    payload = {"json_filename": json_file}
    res = requests.post(f"{SERVER}/generate/", json=payload)
    print("Generate response:", res.json())


# -------------------------
# Step 3: Download PDF
# -------------------------
def download_pdf(pdf_filename: str):
    res = requests.get(f"{SERVER}/transfer/{pdf_filename}")
    if res.status_code == 200:
        with open(pdf_filename, "wb") as f:
            f.write(res.content)
        print(f"Downloaded: {pdf_filename}")
    else:
        print("Download failed:", res.text)


# -------------------------
# Step 4: Clear temp
# -------------------------
def clear_temp():
    res = requests.post(f"{SERVER}/clear/")
    print("Clear response:", res.json())


# -------------------------
# Run with argument or prompt
# -------------------------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        json_file = input("Enter the JSON filename: ").strip()
    else:
        json_file = sys.argv[1]

    json_path = Path(json_file)
    if not json_path.exists():
        print(f"JSON file not found: {json_file}")
        sys.exit(1)

    included_files = extract_included_files(json_path)
    print("Included files:", included_files)  # Optional debug output

    output_pdf = json_path.with_suffix(".pdf").name

    upload_files(json_file, included_files)
    generate_pdf(json_path.name)
    download_pdf(output_pdf)
    clear_temp()
