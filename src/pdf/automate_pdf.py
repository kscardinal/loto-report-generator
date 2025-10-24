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
BASE_DIR = Path(__file__).parent.parent.parent  # Adjust if generate_pdf.py is inside src/pdf/
INCLUDES_DIR = BASE_DIR / "includes"
JSON_DIR = BASE_DIR / "src" / "tests"
TEMP_DIR = BASE_DIR / "temp"

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
        file_path = INCLUDES_DIR / name
        if not file_path.exists():
            print(f"[Warning] Included file not found: {name}")
            continue
        # Tell the server the "filename" should just be the base name
        files.append(('files', (name, open(file_path, 'rb'))))
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
        # Write directly into JSON_DIR
        output_path = BASE_DIR / pdf_filename
        with open(output_path, "wb") as f:
            f.write(res.content)
        print(f"Downloaded: {output_path}")
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
    if len(sys.argv) > 1:
        json_filename = sys.argv[1]
    else:
        json_filename = input("Enter the JSON filename (without .json extension): ").strip()
        if not json_filename.endswith('.json'):
            json_filename += '.json'
    
    json_path = TEMP_DIR / json_filename

    if not json_path.exists():
        print(f"JSON file not found: {json_path}")
        sys.exit(1)
    
    included_files = extract_included_files(json_path)
    print("Included files:", included_files)  # Optional debug output

    output_pdf = json_path.with_suffix(".pdf").name  # Just the filename, not full path

    upload_files(str(json_path), included_files)
    generate_pdf(json_path.name)
    download_pdf(output_pdf)
    clear_temp()
