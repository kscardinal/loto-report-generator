import json
import subprocess
import sys
import tempfile
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import List, Optional
from icecream import ic

from pydantic import BaseModel
import gridfs
from bson.objectid import ObjectId
from fastapi import FastAPI, UploadFile, File, Form, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pymongo import MongoClient

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

# -----------------------------
# Opens the page to create a report
# -----------------------------
@app.get("/create_report", response_class=HTMLResponse)
async def create_report(request: Request):
    """
    Serves the input_form.html page for creating a new report.
    """
    return templates.TemplateResponse("input_form.html", {"request": request})

# -----------------------------
# Remove a report from the database
# -----------------------------
@app.api_route("/remove_report/{report_name}", methods=["GET", "POST"])
async def remove_report(report_name: str):
    """
    Remove a report from the database by name.
    Does NOT delete photos, since multiple reports can share the same images.
    Returns the names of photos retained for logging.
    """
    # Find the report
    doc = uploads.find_one({"report_name": report_name})
    if not doc:
        return JSONResponse(status_code=404, content={"error": f"Report '{report_name}' not found"})

    # Collect photo names for logging
    photo_names = [p["photo_name"] for p in doc.get("photos", [])]

    # Delete the report document itself
    result = uploads.delete_one({"_id": doc["_id"]})
    if result.deleted_count == 0:
        return JSONResponse(status_code=500, content={"error": f"Failed to delete report '{report_name}'"})

    return {
        "message": f"Report '{report_name}' deleted successfully.",
        "photos_retained": photo_names
    }

# -----------------------------
# Cleanup orphaned photos from GridFS
# -----------------------------
@app.api_route("/cleanup_orphan_photos", methods=["GET", "POST"])
async def cleanup_orphan_photos():
    """
    Delete all photos in GridFS that are not referenced by any report.
    Returns a dictionary of deleted photos with their names and IDs.
    """
    deleted_photos = {}

    # Iterate over all files in GridFS
    for grid_out in fs.find():
        photo_id = grid_out._id
        photo_name = grid_out.filename

        # Check if this photo_id exists in any report
        usage_count = uploads.count_documents({"photos.photo_id": photo_id})
        if usage_count == 0:
            # Not used, delete from GridFS
            fs.delete(photo_id)
            deleted_photos[photo_name] = str(photo_id)

    return {
        "message": f"Cleanup complete. {len(deleted_photos)} orphaned photos deleted.",
        "deleted": deleted_photos
    }

# -----------------------------
# Returns a json package of the current reports in the database
# -----------------------------
@app.get("/pdf_list_json")
async def pdf_list_json():
    """
    Returns a JSON list of all reports with metadata only (no JSON data or photos).
    """
    docs = uploads.find({}, {"_id": 0, "json_data": 0, "photos": 0})  # exclude JSON and photos
    report_list = []

    for doc in docs:
        # Count number of photos in original report
        photo_count = len(doc.get("photos", [])) if "photos" in doc else 0

        # Convert datetime fields to ISO format
        for key in ["date_added", "last_modified", "last_generated"]:
            if key in doc and isinstance(doc[key], datetime):
                doc[key] = doc[key].isoformat()

        # Add photo count
        doc["num_photos"] = photo_count

        report_list.append(doc)

    return {"reports": report_list}


# -----------------------------
# Download JSON + all related photos (separately)
# -----------------------------
@app.get("/download_report_files/{report_name}", name="download_report_files")
def download_report_files(report_name: str):
    """
    Download the report JSON and all related photos for a given report name.
    Returns JSON with download URLs for each file.
    """
    doc = uploads.find_one({"report_name": report_name})
    if not doc:
        return JSONResponse(status_code=404, content={"error": f"Report '{report_name}' not found"})

    # Prepare response structure
    file_list = []

    # 1️⃣ Create JSON download URL
    file_list.append({
        "filename": f"{report_name}.json",
        "url": f"/download_json/{report_name}"
    })

    # 2️⃣ Create photo download URLs
    for photo in doc.get("photos", []):
        file_list.append({
            "filename": photo.get("photo_name", f"{photo['photo_id']}.jpg"),
            "url": f"/download_photo/{photo['photo_id']}"
        })

    return {"report_name": report_name, "files": file_list}


# -----------------------------
# Download JSON file for a report
# -----------------------------
@app.get("/download_json/{report_name}", name="download_json")
def download_json(report_name: str):
    doc = uploads.find_one({"report_name": report_name})
    if not doc:
        return JSONResponse(status_code=404, content={"error": f"Report '{report_name}' not found"})

    json_bytes = BytesIO(json.dumps(doc["json_data"], indent=2).encode("utf-8"))
    headers = {"Content-Disposition": f"attachment; filename={report_name}.json"}
    return StreamingResponse(json_bytes, media_type="application/json", headers=headers)


# -----------------------------
# Download photo by its GridFS ID
# -----------------------------
@app.get("/download_photo/{photo_id}", name="download_photo")
def download_photo(photo_id: str):
    try:
        grid_out = fs.get(ObjectId(photo_id))
    except Exception:
        return JSONResponse(status_code=404, content={"error": f"Photo '{photo_id}' not found"})

    headers = {"Content-Disposition": f"attachment; filename={grid_out.filename}"}
    return StreamingResponse(grid_out, media_type="image/jpeg", headers=headers)



# -----------------------------
# Upload new report to database
# -----------------------------
def reformat_date(date_val: Optional[str]) -> Optional[str]:
    """
    Convert a date string from 'dd/MM/yyyy' or 'dd-MM-yyyy' to 'yyyy-MM-dd'.
    Returns None if input is empty or invalid.
    """
    if not date_val or not isinstance(date_val, str):
        return None

    # Try to parse common formats
    for fmt in ("%m/%d/%Y", "%m-%d-%Y"):
        try:
            dt = datetime.strptime(date_val.strip(), fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue

    # Could not parse
    return None

@app.get("/update/{report_name}", response_class=HTMLResponse)
async def update(request: Request, report_name: str):
    doc = get_report_entry(uploads, fs, report_name, fetch_photos=True)
    if not doc:
        return HTMLResponse(f"<h1>Report '{report_name}' not found</h1>", status_code=404)

    # Format datetime fields
    for key in ["date_added", "last_modified", "last_generated"]:
        if key in doc and isinstance(doc[key], datetime):
            doc[key] = format_datetime_with_ordinal(doc[key])

    # Format report dates to yyyy-MM-dd inside json_data
    if "json_data" in doc:
        for key in ["date", "completed_date"]:
            if key in doc["json_data"]:
                doc["json_data"][key] = reformat_date(doc["json_data"][key])

    return templates.TemplateResponse("update_report.html", {"request": request, "report": doc})


@app.get("/get_report_json/{report_name}")
async def get_report_json(report_name: str):
    """
    Return only the json_data of a report as JSON.
    """
    # Find the report in the database
    doc = uploads.find_one({"report_name": report_name})
    if not doc:
        raise HTTPException(status_code=404, detail=f"Report '{report_name}' not found")
    
    # Return only the json_data field
    return JSONResponse(content=doc.get("json_data", {}))


# Schema for update
class FieldUpdate(BaseModel):
    field: str
    value: str

class UpdateReportRequest(BaseModel):
    report_name: str
    updates: List[FieldUpdate]

@app.post("/update_report_json")
async def update_report_json(request: UpdateReportRequest):
    # Find the report
    doc = uploads.find_one({"report_name": request.report_name})
    if not doc:
        raise HTTPException(status_code=404, detail=f"Report '{request.report_name}' not found")

    # Prepare update dictionary
    update_dict = {}
    for item in request.updates:
        update_dict[f"json_data.{item.field}"] = item.value

    if update_dict:
        result = uploads.update_one(
            {"report_name": request.report_name},
            {"$set": update_dict}
        )
        return {"message": "Report updated successfully", "modified_count": result.modified_count}
    else:
        return JSONResponse(status_code=400, content={"message": "No valid updates provided"})
    
