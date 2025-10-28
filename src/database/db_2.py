from pymongo import MongoClient
from bson.objectid import ObjectId
from bson.binary import Binary
from datetime import datetime
from pathlib import Path
import json
import gridfs

BASE_DIR = Path(__file__).parent.parent.parent
TEMP_DIR = BASE_DIR / "temp"

# -------------------------------
# Initialize the database with GridFS
# -------------------------------
def initialize_db(mongo_uri: str = "mongodb://localhost:27017/", db_name: str = "loto_pdf"):
    client = MongoClient(mongo_uri)
    db = client[db_name]
    uploads = db['reports']        # main collection for metadata and JSON
    fs = gridfs.GridFS(db)         # GridFS for large files (photos)
    return client, db, uploads, fs

# -------------------------------
# Load JSON and gather image filenames
# -------------------------------
def extract_included_files(json_file_path: Path):
    with open(json_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    included = set()
    machine_image = data.get("machine_image")
    if machine_image:
        included.add(str(TEMP_DIR / machine_image))

    sources = data.get("sources", [])
    for src in sources:
        for key in ("isolation_point", "verification_device"):
            img = src.get(key)
            if img:
                included.add(str(TEMP_DIR / img))

    return list(included)


# -------------------------------
# Checks for dublicates in the database
# -------------------------------
def store_photo_dedup(fs: gridfs.GridFS, file_path: Path):
    """
    Store a photo in GridFS with deduplication.
    Returns the ObjectId of the stored (or reused) file.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(path, "rb") as f:
        new_data = f.read()

    # Check for files with the same name
    existing_files = fs.find({"filename": path.name})

    for ef in existing_files:
        existing_data = fs.get(ef._id).read()
        if existing_data == new_data:
            # File content matches, reuse ObjectId
            print(f"[Dedup] Reusing existing file for {path.name}")
            return ef._id

    # No match found, store as new
    new_id = fs.put(new_data, filename=path.name)
    print(f"[Dedup] Stored new file for {path.name} with ObjectId {new_id}")
    return new_id

# -------------------------------
# Add or update a report entry with photos stored in GridFS
# -------------------------------
def add_or_update_report_entry(
    uploads_collection,
    fs,
    report_name: str,
    json_file: Path,
    include_files: list,
    uploaded_by: str,
    tags: list = None,
    notes: str = "",
    version: int = 1
):
    if tags is None:
        tags = []

    # Read and parse JSON
    with open(json_file, "r", encoding="utf-8") as f:
        json_data = json.load(f)

    # Store photos in GridFS and collect ObjectIDs
    photos_data = []
    for file_path in include_files:
        try:
            photo_id = store_photo_dedup(fs, Path(file_path))
            photos_data.append({
                "photo_name": Path(file_path).name,
                "photo_id": photo_id
            })
        except FileNotFoundError:
            print(f"[Warning] Included file not found: {file_path}")

    # Update or insert document
    uploads_collection.update_one(
        {"report_name": report_name},
        {"$set": {
            "json_data": json_data,
            "photos": photos_data,
            "uploaded_by": uploaded_by,
            "tags": tags,
            "notes": notes,
            "last_modified": datetime.now(),
            "version": version
        },
         "$setOnInsert": {
             "date_added": datetime.now(),
             "last_generated": datetime.now()
         }
        },
        upsert=True
    )
    print(f"Report entry '{report_name}' added or updated in database.")


# -------------------------------
# Fetch report entry and optionally retrieve photos from GridFS
# -------------------------------
def get_report_entry(uploads_collection, fs, report_name: str, fetch_photos: bool = False):
    doc = uploads_collection.find_one({"report_name": report_name})
    if not doc:
        return None

    if fetch_photos:
        for photo in doc.get("photos", []):
            photo_id = photo.get("photo_id")
            if photo_id:
                photo_data = fs.get(photo_id).read()
                photo["photo_data"] = photo_data  # attach binary content
    return doc

# -------------------------------
# Example usage
# -------------------------------
if __name__ == "__main__":
    client, db, uploads, fs = initialize_db()
    print("Database initialized with GridFS support.")

    json_file = TEMP_DIR / "test_data_22.json"
    include_files = extract_included_files(json_file)

    report_name = json_file.stem  # no .pdf extension

    add_or_update_report_entry(
        uploads,
        fs,
        report_name,
        json_file,
        include_files,
        uploaded_by="test_user",
        tags=["lockout", "tagout"],
        notes="Initial upload"
    )

    doc = get_report_entry(uploads, fs, report_name, fetch_photos=True)
    if doc:
        print("Retrieved document from DB:")
        print("Report name:", doc["report_name"])
        print("Number of photos stored:", len(doc["photos"]))
        print("Uploaded by:", doc["uploaded_by"])
