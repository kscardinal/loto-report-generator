from pymongo import MongoClient
from bson.binary import Binary
from datetime import datetime
from pathlib import Path
import json


BASE_DIR = Path(__file__).parent.parent.parent  # Adjust if generate_pdf.py is inside src/pdf/
INCLUDES_DIR = BASE_DIR / "includes"
JSON_DIR = BASE_DIR / "src" / "tests"
TEMP_DIR = BASE_DIR / "temp"


# -------------------------------
# Initialize the database for further use
# -------------------------------
def initialize_db(mongo_uri:str="mongodb://localhost:27017/", db_name:str="loto_pdf"):
    client = MongoClient(mongo_uri)
    db = client[db_name]
    uploads = db['uploads']
    return client, db, uploads


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
        included.add(str(TEMP_DIR / machine_image))

    # From each source
    sources = data.get("sources", [])
    for src in sources:
        for key in ("isolation_point", "verification_device"):
            img = src.get(key)
            if img:
                included.add(str(TEMP_DIR / img))

    return list(included)


# -------------------------------
# Add or update a PDF entry
# -------------------------------
def add_pdf_entry(uploads_collection:MongoClient, pdf_name: str, json_file: Path, include_files: list, metadata: dict = None):
    if metadata is None:
        metadata = {}

    # Read JSON
    with open(json_file, "rb") as f:
        json_data = f.read()

    # Read photos
    photos_data = []
    for file_path in include_files:
        if not Path(file_path).exists():
            print(f"[Warning] Included file not found: {file_path}")
            continue
        with open(file_path, "rb") as f:
            photos_data.append({
                "photo_name": Path(file_path).name,
                "photo_data": Binary(f.read())
            })

    # Prepare document
    doc = {
        "pdf_name": pdf_name,
        "date_added": datetime.now(),
        "last_generated": datetime.now(),
        "json_filename": json_file.name,
        "json_data": Binary(json_data),
        "photos": photos_data,
        "metadata": metadata
    }

    # Upsert: replace existing PDF entry with same name
    uploads_collection.replace_one({"pdf_name": pdf_name}, doc, upsert=True)
    print(f"PDF entry '{pdf_name}' added/updated in database.")

# -------------------------------
# Fetch PDF entry
# -------------------------------
def get_pdf_entry(uploads_collection:MongoClient, pdf_name: str):
    return uploads_collection.find_one({"pdf_name": pdf_name})

# -------------------------------
# Example usage / test
# -------------------------------
if __name__ == "__main__":
    client, db, uploads = initialize_db()
    print("Database initialized, ready for use.")

    # Example files (adjust paths)
    json_file = TEMP_DIR / "test_data.json"
    include_files = extract_included_files(json_file)

    pdf_name = str(json_file.stem) + ".pdf"

    add_pdf_entry(uploads, pdf_name, json_file, include_files, metadata={"uploaded_by": "test_user"})
    doc = get_pdf_entry(uploads, "test_data.pdf")
    if doc:
        print("Retrieved document from DB:")
        print("PDF name:", doc["pdf_name"])
        print("JSON filename:", doc["json_filename"])
        print("Number of photos stored:", len(doc["photos"]))