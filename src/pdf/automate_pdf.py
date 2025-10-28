import sys
import json
import requests
from pathlib import Path
import os
from dotenv import load_dotenv
from icecream import ic

# Load .env file
load_dotenv()

# -------------------------
# CONFIGURATION
# -------------------------
SERVER = os.getenv("SERVER_IP")
BASE_DIR = Path(__file__).parent.parent.parent
TEMP_DIR = BASE_DIR / "temp"

# -------------------------
# Extract images referenced in JSON
# -------------------------
def extract_included_files(json_file_path: Path):
    with open(json_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    included = set()

    machine_image = data.get("machine_image")
    if machine_image:
        included.add(machine_image)

    for src in data.get("sources", []):
        for key in ("isolation_point", "verification_device"):
            img = src.get(key)
            if img:
                included.add(img)

    return list(included)

# -------------------------
# Upload JSON + images
# -------------------------
def upload_files(json_file: str, include_files: list):
    files = [('files', open(json_file, 'rb'))]
    for name in include_files:
        file_path = TEMP_DIR / name
        if not file_path.exists():
            print(f"[Warning] Included file not found: {name}")
            continue
        files.append(('files', (name, open(file_path, 'rb'))))

    data = {"uploaded_by": "automation", "tags": [], "notes": ""}
    res = requests.post(f"{SERVER}/upload/", files=files, data=data)
    print("Upload response:", res.json())

# -------------------------
# Trigger PDF generation
# -------------------------
def generate_pdf(report_name: str):
    payload = {"report_name": report_name}
    res = requests.post(f"{SERVER}/generate/", json=payload)
    print("Generate response:", res.json())

# -------------------------
# Download PDF via /download_pdf
# -------------------------
def download_pdf(report_name: str, output_dir: Path):
    output_pdf_path = output_dir / f"{report_name}.pdf"
    res = requests.get(f"{SERVER}/download_pdf/{report_name}", stream=True)
    if res.status_code == 200:
        with open(output_pdf_path, "wb") as f:
            for chunk in res.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Downloaded PDF: {output_pdf_path}")
    else:
        print("Download failed:", res.text)
    return output_pdf_path

# -------------------------
# Clear temp folder
# -------------------------
def clear_temp():
    res = requests.post(f"{SERVER}/clear/")
    print("Clear response:", res.json())

# -------------------------
# Main automation
# -------------------------
def main(json_path: Path | str = None):
    if json_path is None:
        if len(sys.argv) > 1:
            json_filename = sys.argv[1]
        else:
            json_filename = input("Enter the JSON filename (without .json extension): ").strip()
            if not json_filename.endswith(".json"):
                json_filename += ".json"
        json_path = TEMP_DIR / json_filename
    else:
        json_path = Path(json_path)

    if not json_path.exists():
        ic(f"JSON file not found: {json_path}")
        sys.exit(1)

    included_files = extract_included_files(json_path)
    ic(f"Included files: {included_files}")

    report_name = json_path.stem

    upload_files(str(json_path), included_files)
    generate_pdf(report_name)
    output_pdf_path = download_pdf(report_name, BASE_DIR)
    clear_temp()

    return output_pdf_path

# -------------------------
# CLI entry point
# -------------------------
if __name__ == "__main__":
    main()
