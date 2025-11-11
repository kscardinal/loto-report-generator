import sys
import json
from pathlib import Path
import os
from dotenv import load_dotenv
from icecream import ic
from datetime import datetime, timedelta
import jwt
import subprocess

# Load .env file
load_dotenv()

# -------------------------
# CONFIGURATION
# -------------------------
# Determine which server to use based on environment
APP_ENV = os.getenv("APP_ENV", "dev").lower()
if APP_ENV == "dev":
    SERVER = os.getenv("TEST_SERVER_IP")
else:
    SERVER = os.getenv("SERVER_IP")

BASE_DIR = Path(__file__).parent.parent.parent
TEMP_DIR = BASE_DIR / "temp"

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY not set in .env")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

def create_access_token(data: dict, expires_delta: int = ACCESS_TOKEN_EXPIRE_MINUTES):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_delta)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# -----------------------------
# JWT setup
# -----------------------------
TEST_USERNAME = "testuser"
TEST_TOKEN = create_access_token({"sub": TEST_USERNAME, "role": "admin"})

# Headers for mobile/API endpoints
HEADERS = {"Authorization": f"Bearer {TEST_TOKEN}"}

# Cookies for web endpoints
COOKIES = {"access_token": TEST_TOKEN}

import requests

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
def upload_files(
    json_file: str,
    include_files: list,
    uploaded_by: str = "automation",
    tags: list | None = None,
    notes: str = ""
):
    if tags is None:
        tags = []

    # Build files payload
    files_payload = [('files', open(json_file, 'rb'))]
    for name in include_files:
        file_path = TEMP_DIR / name
        if not file_path.exists():
            print(f"[Warning] Included file not found: {name}")
            continue
        files_payload.append(('files', (name, open(file_path, 'rb'))))

    # Form fields
    form_data = [("uploaded_by", uploaded_by), ("notes", notes)]
    for t in tags:
        form_data.append(("tags", t))

    # Send POST request with JWT cookie for web compatibility
    res = requests.post(
        f"{SERVER}/upload/",
        files=files_payload,
        data=form_data,
        cookies=COOKIES,   # Include JWT
        headers=HEADERS     # Optional: also include Authorization for API
    )

    try:
        print("Upload response:", res.json())
    except Exception:
        print("Upload failed:", res.text)

# -------------------------
# Trigger PDF generation
# -------------------------
def generate_pdf(report_name: str):
    res = requests.get(
        f"{SERVER}/download_pdf/{report_name}",
        cookies=COOKIES,
        headers=HEADERS,
        stream=True
    )
    if res.status_code == 200:
        print("PDF generated successfully")
    else:
        print("Error generating PDF:", res.status_code)

# -------------------------
# Download PDF
# -------------------------
def download_pdf(report_name: str, output_dir: Path):
    output_pdf_path = output_dir / f"{report_name}.pdf"
    res = requests.get(
        f"{SERVER}/download_pdf/{report_name}",
        stream=True,
        cookies=COOKIES,
        headers=HEADERS
    )
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
    res = requests.post(f"{SERVER}/clear/", cookies=COOKIES, headers=HEADERS)
    try:
        print("Clear response:", res.json())
    except Exception:
        print("Clear failed:", res.text)

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

    upload_files(
        str(json_path),
        included_files,
        uploaded_by="Automation",
        tags=["tests", "automation"],
        notes="Uploaded via test automation"
    )
    output_pdf_path = download_pdf(report_name, BASE_DIR)
    clear_temp()

    return output_pdf_path

# -------------------------
# CLI entry point
# -------------------------
if __name__ == "__main__":
    main()
