from fastapi import FastAPI, UploadFile, File, Request, Response
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List
from pathlib import Path
import subprocess
import traceback
from datetime import datetime
from pymongo import MongoClient
from bson.binary import Binary
from fastapi.templating import Jinja2Templates
import json
import gridfs
import sys
from bson.objectid import ObjectId
import tempfile
from io import BytesIO
from fastapi import Form

app = FastAPI()

origins = [
    "*"  # optional: allow all origins
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Resolve project paths ===
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))  # if your scripts import local modules

from src.database.db_2 import get_report_entry

# MongoDB connection (adjust as needed)
MONGO_URI = "mongodb://localhost:27017/"
client = MongoClient(MONGO_URI)
db = client['loto_pdf']
uploads = db['reports']        # main collection for metadata and JSON
fs = gridfs.GridFS(db)         # GridFS for large files (photos)

# Define base paths
BASE_DIR = Path(__file__).parent.parent.parent
INCLUDES_DIR = BASE_DIR / "includes"
JSON_DIR = BASE_DIR / "src" / "tests"
TEMP_DIR = BASE_DIR / "temp"
PROCESS_DIR = BASE_DIR / "src" / "pdf"

templates = Jinja2Templates(directory=str(BASE_DIR / "src" / "web" / "templates"))

# Create required directories
for directory in [TEMP_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


# -----------------------------
# Upload route
# -----------------------------
@app.post("/upload/")
@app.post("/upload/")
async def upload_report(
    files: List[UploadFile] = File(...),
    uploaded_by: str = Form("anonymous"),
    tags: List[str] = Form([]),
    notes: str = Form(""),
):

    json_file = None
    include_files = []

    # Save incoming files to temp and classify
    for file in files:
        file_location = TEMP_DIR / file.filename
        contents = await file.read()
        with open(file_location, "wb") as f:
            f.write(contents)

        if file.filename.lower().endswith(".json"):
            json_file = file_location
        else:
            include_files.append(file_location)

    if not json_file:
        return {"error": "No JSON file uploaded"}

    # Read JSON
    with open(json_file, "r", encoding="utf-8") as f:
        json_data = json.load(f)

    report_name = json_file.stem

    # Check if report already exists
    existing_report = uploads.find_one({"report_name": report_name})
    now = datetime.now()

    photos_data = []
    for path in include_files:
        # Check for duplicate photos in GridFS
        file_bytes = path.read_bytes()
        duplicate = None
        for file in fs.find({"filename": path.name}):
            if file.read() == file_bytes:
                duplicate = file
                break

        if duplicate:
            photo_id = duplicate._id
        else:
            photo_id = fs.put(file_bytes, filename=path.name)

        photos_data.append({"photo_name": path.name, "photo_id": photo_id})

    if existing_report:
        # Update report (keep date_added, update last_modified, last_generated, JSON, photos, metadata)
        uploads.update_one(
            {"_id": existing_report["_id"]},
            {"$set": {
                "json_data": json_data,
                "photos": photos_data,
                "last_modified": now,
                "last_generated": now,
                "uploaded_by": uploaded_by,
                "tags": tags,
                "notes": notes
            }}
        )
    else:
        # Insert new report
        doc = {
            "report_name": report_name,
            "json_data": json_data,
            "photos": photos_data,
            "uploaded_by": uploaded_by,
            "tags": tags,
            "notes": notes,
            "date_added": now,
            "last_modified": now,
            "last_generated": now,
            "version": 1
        }
        uploads.insert_one(doc)

    return {"report_name": report_name, "photos": [p["photo_name"] for p in photos_data]}


# -----------------------------
# Generate PDF from JSON
# -----------------------------
class GenerateRequest(BaseModel):
    report_name: str  # Use report_name instead of json_filename

@app.post("/generate/")
async def generate_pdf_from_db(request: GenerateRequest):
    report_name = request.report_name

    # Fetch report from DB
    doc = uploads.find_one({"report_name": report_name})
    if not doc:
        return JSONResponse(status_code=404, content={"error": f"Report '{report_name}' not found"})

    try:
        # Create a temporary folder to dump JSON and photos
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Save JSON file
            json_file_path = tmpdir_path / f"{report_name}.json"
            with open(json_file_path, "w", encoding="utf-8") as f:
                json.dump(doc["json_data"], f, ensure_ascii=False, indent=2)

            # Save all photos locally
            for photo in doc["photos"]:
                photo_file_path = tmpdir_path / photo["photo_name"]
                file_bytes = fs.get(photo["photo_id"]).read()
                with open(photo_file_path, "wb") as f:
                    f.write(file_bytes)

            # Call the existing generate_pdf.py with the JSON path
            result = subprocess.run(
                ["python", str(PROCESS_DIR / "generate_pdf.py"), str(json_file_path)],
                capture_output=True,
                text=True,
                check=True
            )

            # Optional: return the expected PDF filename
            pdf_filename = f"{report_name}.pdf"

    except subprocess.CalledProcessError as e:
        return JSONResponse(status_code=500, content={
            "error": "PDF generation failed.",
            "details": e.stderr or e.stdout or str(e)
        })
    except Exception as e:
        import traceback
        return JSONResponse(status_code=500, content={
            "error": "Unexpected error.",
            "details": traceback.format_exc()
        })

    return {"message": "PDF generation triggered successfully.", "pdf_filename": pdf_filename}


# -----------------------------
# Transfer route - download PDF
# -----------------------------
@app.get("/transfer/{pdf_filename}")
async def transfer_pdf(pdf_filename: str):
    safe_name = Path(pdf_filename).name
    file_path = TEMP_DIR / safe_name

    if not file_path.exists() or file_path.stat().st_size == 0:
        return JSONResponse(status_code=404, content={
            "error": f"PDF file '{safe_name}' not found or is empty."
        })

    return FileResponse(
        path=file_path,
        filename=safe_name,
        media_type="application/pdf"
    )


# -----------------------------
# Clear all temp files
# -----------------------------
@app.post("/clear/")
async def clear_temp_folders():
    for folder in [TEMP_DIR]:
        for file in folder.iterdir():
            if file.is_file():
                file.unlink()
    return {"message": "All temp data cleared."}


# -----------------------------
# Gets all pdfs in the database
# -----------------------------
@app.get("/pdf_list", response_class=HTMLResponse)
async def pdf_list(request: Request):
    # Fetch all reports, sorted by date_added descending (newest first)
    docs = uploads.find({}, {"_id": 0, "report_name": 1}).sort("date_added", -1)
    report_names = [doc.get("report_name") for doc in docs if doc.get("report_name")]
    print("Fetched report names:", report_names)  # Debug
    return templates.TemplateResponse(
        "pdf_list.html",
        {"request": request, "report_names": report_names}
    )


@app.get("/view_report/{report_name}", response_class=HTMLResponse)
async def view_report(request: Request, report_name: str):
    doc = get_report_entry(uploads, fs, report_name, fetch_photos=True)
    if not doc:
        return HTMLResponse(f"<h1>Report '{report_name}' not found</h1>", status_code=404)

    # You can render a template with details, JSON, and images
    return templates.TemplateResponse("view_report.html", {"request": request, "report": doc})

@app.get("/photo/{photo_id}")
def get_photo(photo_id: str):
    photo = fs.get(ObjectId(photo_id))
    return Response(photo.read(), media_type="image/jpeg")  # or detect type dynamically


@app.get("/download_pdf/{report_name}", name="download_pdf")
def download_pdf(report_name: str):
    # Fetch report from DB
    doc = uploads.find_one({"report_name": report_name})
    if not doc:
        return JSONResponse(status_code=404, content={"error": f"Report '{report_name}' not found"})

    try:
        # Create temporary files for generate_pdf.py
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Save JSON
            json_file_path = tmpdir_path / f"{report_name}.json"
            with open(json_file_path, "w", encoding="utf-8") as f:
                json.dump(doc["json_data"], f, ensure_ascii=False, indent=2)

            # Save photos
            for photo in doc["photos"]:
                photo_file_path = tmpdir_path / photo["photo_name"]
                file_bytes = fs.get(photo["photo_id"]).read()
                with open(photo_file_path, "wb") as f:
                    f.write(file_bytes)

            # Generate PDF using subprocess
            pdf_file_path = tmpdir_path / f"{report_name}.pdf"
            subprocess.run(
                ["python", str(PROCESS_DIR / "generate_pdf.py"), str(json_file_path)],
                check=True
            )

            # Read PDF bytes into memory
            with open(pdf_file_path, "rb") as f:
                pdf_bytes = f.read()

            # Stream PDF back to client
            pdf_stream = BytesIO(pdf_bytes)
            return StreamingResponse(
                pdf_stream,
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename={report_name}.pdf"}
            )

    except subprocess.CalledProcessError as e:
        return JSONResponse(status_code=500, content={"error": "PDF generation failed.", "details": e.stderr})
    except Exception as e:
        import traceback
        return JSONResponse(status_code=500, content={"error": "Unexpected error.", "details": traceback.format_exc()})