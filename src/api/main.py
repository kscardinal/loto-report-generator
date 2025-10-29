from fastapi import FastAPI, UploadFile, File, Form, Request, Response
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List
from pathlib import Path
from datetime import datetime
from pymongo import MongoClient
import gridfs
from bson.objectid import ObjectId
import subprocess
import tempfile
import json
from io import BytesIO
import sys
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# -----------------------------
# CORS Configuration
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Project paths
# -----------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

from src.database.db_2 import get_report_entry

BASE_DIR = Path(__file__).parent.parent.parent
TEMP_DIR = BASE_DIR / "temp"
PROCESS_DIR = BASE_DIR / "src" / "pdf"
WEB_DIR = BASE_DIR / "src" / "web"

templates = Jinja2Templates(directory=str(BASE_DIR / "src" / "web" / "templates"))

# Ensure TEMP_DIR exists
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# Mount files
app.mount("/static", StaticFiles(directory=WEB_DIR / "static"), name="static")


# -----------------------------
# MongoDB Connection
# -----------------------------
MONGO_URI = "mongodb://localhost:27017/"
client = MongoClient(MONGO_URI)
db = client['loto_pdf']
uploads = db['reports']        # collection for metadata + JSON
fs = gridfs.GridFS(db)         # GridFS for storing photos

# -----------------------------
# Upload JSON + images
# -----------------------------
@app.post("/upload/")
async def upload_report(
    files: List[UploadFile] = File(...),
    uploaded_by: str = Form("anonymous"),
    tags: List[str] = Form([]),
    notes: str = Form("")
):
    """
    Upload a JSON report along with any image files.
    Saves files to temp, checks duplicates in GridFS, and updates/inserts metadata.
    """
    json_file = None
    include_files = []

    # Save uploaded files to temp folder
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

    # Load JSON
    with open(json_file, "r", encoding="utf-8") as f:
        json_data = json.load(f)

    report_name = json_file.stem
    now = datetime.now()
    existing_report = uploads.find_one({"report_name": report_name})

    # Process photos
    photos_data = []
    for path in include_files:
        file_bytes = path.read_bytes()
        duplicate = None
        for file in fs.find({"filename": path.name}):
            if file.read() == file_bytes:
                duplicate = file
                break
        photo_id = duplicate._id if duplicate else fs.put(file_bytes, filename=path.name)
        photos_data.append({"photo_name": path.name, "photo_id": photo_id})

    # Insert or update report
    if existing_report:
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
        uploads.insert_one({
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
        })

    return {"report_name": report_name, "photos": [p["photo_name"] for p in photos_data]}

# -----------------------------
# Trigger PDF generation
# -----------------------------
class GenerateRequest(BaseModel):
    report_name: str

@app.post("/generate/")
async def generate_pdf_from_db(request: GenerateRequest):
    """
    Generate a PDF for the specified report.
    Pulls JSON + images from DB, writes to temp, calls generate_pdf.py via subprocess.
    """
    report_name = request.report_name
    doc = uploads.find_one({"report_name": report_name})
    if not doc:
        return JSONResponse(status_code=404, content={"error": f"Report '{report_name}' not found"})

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            json_file_path = tmpdir_path / f"{report_name}.json"
            with open(json_file_path, "w", encoding="utf-8") as f:
                json.dump(doc["json_data"], f, ensure_ascii=False, indent=2)

            for photo in doc["photos"]:
                photo_file_path = tmpdir_path / photo["photo_name"]
                with open(photo_file_path, "wb") as f:
                    f.write(fs.get(photo["photo_id"]).read())

            subprocess.run(
                ["python", str(PROCESS_DIR / "generate_pdf.py"), str(json_file_path)],
                capture_output=True,
                text=True,
                check=True
            )

            pdf_filename = f"{report_name}.pdf"

    except subprocess.CalledProcessError as e:
        return JSONResponse(status_code=500, content={"error": "PDF generation failed.", "details": e.stderr or e.stdout})
    except Exception as e:
        import traceback
        return JSONResponse(status_code=500, content={"error": "Unexpected error.", "details": traceback.format_exc()})

    return {"message": "PDF generation triggered successfully.", "pdf_filename": pdf_filename}

# -----------------------------
# Download PDF (streams PDF directly to client)
# -----------------------------
@app.get("/download_pdf/{report_name}", name="download_pdf")
def download_pdf(report_name: str):
    """
    Stream the generated PDF for a report back to the client.
    """
    doc = uploads.find_one({"report_name": report_name})
    if not doc:
        return JSONResponse(status_code=404, content={"error": f"Report '{report_name}' not found"})

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            json_file_path = tmpdir_path / f"{report_name}.json"
            with open(json_file_path, "w", encoding="utf-8") as f:
                json.dump(doc["json_data"], f, ensure_ascii=False, indent=2)

            for photo in doc["photos"]:
                photo_file_path = tmpdir_path / photo["photo_name"]
                with open(photo_file_path, "wb") as f:
                    f.write(fs.get(photo["photo_id"]).read())

            pdf_file_path = tmpdir_path / f"{report_name}.pdf"
            subprocess.run(
                ["python", str(PROCESS_DIR / "generate_pdf.py"), str(json_file_path)],
                check=True
            )

            pdf_bytes = pdf_file_path.read_bytes()
            return StreamingResponse(
                BytesIO(pdf_bytes),
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename={report_name}.pdf"}
            )
    except subprocess.CalledProcessError as e:
        return JSONResponse(status_code=500, content={"error": "PDF generation failed.", "details": e.stderr})
    except Exception as e:
        import traceback
        return JSONResponse(status_code=500, content={"error": "Unexpected error.", "details": traceback.format_exc()})

# -----------------------------
# Clear temp folder
# -----------------------------
@app.post("/clear/")
async def clear_temp_folders():
    """
    Clear all files in TEMP_DIR.
    """
    for file in TEMP_DIR.iterdir():
        if file.is_file():
            file.unlink()
    return {"message": "All temp data cleared."}

# -----------------------------
# View all PDFs (HTML)
# -----------------------------
@app.get("/pdf_list", response_class=HTMLResponse)
async def pdf_list(request: Request):
    """
    Render HTML listing of all reports in the DB.
    """
    docs = uploads.find({}, {"_id": 0, "report_name": 1}).sort("report_name", 1)
    report_names = [doc.get("report_name") for doc in docs if doc.get("report_name")]
    return templates.TemplateResponse("pdf_list.html", {"request": request, "report_names": report_names})

# -----------------------------
# View single report (HTML)
# -----------------------------
def ordinal(n: int) -> str:
    """Return ordinal string for a number, e.g., 1 -> 1st"""
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"

def format_datetime_with_ordinal(dt: datetime) -> str:
    """Format datetime with full weekday, month, day with ordinal, year, and 12-hour time"""
    day_with_suffix = ordinal(dt.day)
    # %I is hour (12-hour), %M minutes, %S seconds, %p AM/PM
    return dt.strftime(f"%A, %B {day_with_suffix}, %Y at %I:%M:%S %p").lstrip("0").replace("AM","am").replace("PM","pm")

@app.get("/view_report/{report_name}", response_class=HTMLResponse)
async def view_report(request: Request, report_name: str):
    doc = get_report_entry(uploads, fs, report_name, fetch_photos=True)
    if not doc:
        return HTMLResponse(f"<h1>Report '{report_name}' not found</h1>", status_code=404)

    # Format datetime fields
    for key in ["date_added", "last_modified", "last_generated"]:
        if key in doc and isinstance(doc[key], datetime):
            doc[key] = format_datetime_with_ordinal(doc[key])

    return templates.TemplateResponse("view_report.html", {"request": request, "report": doc})

# -----------------------------
# Fetch individual photo
# -----------------------------
@app.get("/photo/{photo_id}")
def get_photo(photo_id: str):
    """
    Return an image stored in GridFS by ID.
    """
    photo = fs.get(ObjectId(photo_id))
    return Response(photo.read(), media_type="image/jpeg")

# -----------------------------
# Fetch metadata for a given report
# -----------------------------
@app.get("/metadata/{report_name}")
async def get_metadata(report_name: str):
    doc = uploads.find_one(
        {"report_name": report_name},
        {"_id": 0, "json_data": 0, "photos": 0}  # exclude JSON and photos
    )
    if not doc:
        return JSONResponse(status_code=404, content={"error": f"Report '{report_name}' not found"})
    
    # Convert all datetime objects to ISO strings
    for key in ["date_added", "last_modified", "last_generated"]:
        if key in doc and isinstance(doc[key], datetime):
            doc[key] = doc[key].strftime("%A, %B %d, %Y, %I:%M:%S %p")
    
    return JSONResponse(content=doc)

# -----------------------------
# Check status of database
# -----------------------------
@app.get("/db_status")
async def db_status():
    try:
        # Try a lightweight operation
        client.admin.command("ping")
        return {"status": "ok", "message": "Database connection successful"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})



@app.get("/create_report", response_class=HTMLResponse)
async def create_report(request: Request):
    """
    Serves the input_form.html page for creating a new report.
    """
    return templates.TemplateResponse("input_form.html", {"request": request})

