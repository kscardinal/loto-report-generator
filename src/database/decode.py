from pymongo import MongoClient
from bson.binary import Binary
from pathlib import Path

def decode_photos_from_db():
    MONGO_URI = "mongodb://localhost:27017/"
    client = MongoClient(MONGO_URI)
    db = client['loto_pdf']  # Change if needed
    uploads = db['uploads']  # Change if needed

    # Find the document by pdf_name
    doc = uploads.find_one({"pdf_name": "test_data.pdf"})
    if not doc:
        print("Document not found.")
        return

    photos = doc.get("photos", [])
    if not photos:
        print("No photos field in document.")
        return

    for photo in photos:
        photo_name = photo.get("photo_name")
        photo_data = photo.get("photo_data")
        if photo_name is None or photo_data is None:
            print(f"Skipping invalid photo entry: {photo}")
            continue

        if isinstance(photo_data, Binary):
            image_bytes = bytes(photo_data)
        else:
            image_bytes = photo_data

        # Save the photo data to a file named photo_name
        path = Path(photo_name)
        with open(path, "wb") as f:
            f.write(image_bytes)

        print(f"Saved photo {photo_name}")

if __name__ == "__main__":
    decode_photos_from_db()
