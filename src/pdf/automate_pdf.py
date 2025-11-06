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
def upload_files(
    json_file: str,
    include_files: list,
    uploaded_by: str = "automation",
    tags: list | None = None,
    notes: str = ""
):
    """
    Upload a JSON report + optional images to the FastAPI server.
    Sends uploaded_by, tags, and notes as form fields.
    """
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

    # Build form fields as list of tuples
    # Multiple 'tags' entries are required for FastAPI to parse them correctly
    form_data = [("uploaded_by", uploaded_by), ("notes", notes)]
    for t in tags:
        form_data.append(("tags", t))

    # Send POST request
    import requests
    res = requests.post(f"{SERVER}/upload/", files=files_payload, data=form_data)

    try:
        print("Upload response:", res.json())
    except Exception:
        print("Upload failed:", res.text)


# -------------------------
# Trigger PDF generation
# -------------------------
def generate_pdf(report_name: str):
    res = requests.get(f"{SERVER}/download_pdf/{report_name}")
    if res.status_code == 200:
        print("Generate Reponse: PDF generated successfully")
    else:
        print("Generate Reponse: Error generating PDF:", res.status_code)

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

# Example call
    upload_files(
        str(json_path),             # path to your JSON file
        included_files,             # list of images to include
        uploaded_by="Automation",         # set author
        tags=["tests", "automation"],      # any tags you want
        notes="This report was uploaded via a test automation" # sample note
    )
    output_pdf_path = download_pdf(report_name, BASE_DIR)
    clear_temp()

    return output_pdf_path

# -------------------------
# CLI entry point
# -------------------------
if __name__ == "__main__":
    main()
