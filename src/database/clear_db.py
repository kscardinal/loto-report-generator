from pymongo import MongoClient
from pathlib import Path
import shutil

# --- Configure your MongoDB connection ---
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "loto_pdf"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

# --- Collections to clear ---
collections_to_clear = ["reports", "fs.files", "fs.chunks"]

for coll_name in collections_to_clear:
    coll = db[coll_name]
    result = coll.delete_many({})
    print(f"Cleared {result.deleted_count} documents from '{coll_name}'")

print("All specified collections cleared.")

# --- Paths ---
BASE_DIR = Path(__file__).parent.parent.parent
TEMP_DIR = BASE_DIR / "temp"
TEST_DIR = BASE_DIR / "src" / "tests"

# Ensure temp folder exists
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# --- Copy test_data*.json files to temp ---
for json_file in TEST_DIR.glob("test_data*.json"):
    dest_file = TEMP_DIR / json_file.name
    shutil.copy2(json_file, dest_file)
    print(f"Copied '{json_file.name}' to temp folder")

print("Test JSON files are ready in temp folder.")
