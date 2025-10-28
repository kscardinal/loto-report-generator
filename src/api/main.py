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
async def upload_files(files: List[UploadFile] = File(...)):
    saved_files = []
    photos_data = []
    json_data = None
    json_file_name = None

    for file in files:
        file_location = TEMP_DIR / file.filename
        contents = await file.read()
        with open(file_location, "wb") as f:
            f.write(contents)
        saved_files.append(str(file_location))

        if file.filename.lower().endswith(".json"):
            json_file_name = file.filename
            # attempt to load and update a 'last_modified' field in the JSON
            try:
                parsed = json.loads(contents.decode("utf-8"))
                parsed["last_modified"] = datetime.now().isoformat()
                updated_bytes = json.dumps(parsed, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
                json_data = Binary(updated_bytes)
            except Exception:
                # if JSON parsing fails, store original bytes
                json_data = Binary(contents)
        else:
            photos_data.append({
                "photo_name": file.filename,
                "photo_data": Binary(contents)
            })

    # Prepare a document only if we have json_data, otherwise adjust as needed
    if json_data:
        now = datetime.now()
        # Check if a document with this JSON already exists (by filename)
        existing = uploads.find_one({"json_filename": json_file_name})
        if existing:
            # Update last_generated and (optionally) replace json_data with the updated content
            uploads.update_one(
                {"_id": existing["_id"]},
                {"$set": {
                    "last_generated": now,
                    "json_data": json_data,
                    "metadata.last_modified": now
                }}
            )
        else:
            doc = {
                "pdf_name": json_file_name,  # or adjust as needed
                "date_added": now,
                "last_generated": now,
                "json_filename": json_file_name,
                "json_data": json_data,
                "photos": photos_data,
                "metadata": {
                    "uploaded_via": "upload_route",
                    "last_modified": now
                }
            }
            uploads.insert_one(doc)

    return {"uploaded_files": saved_files}


# -----------------------------
# Generate PDF from JSON
# -----------------------------
class GenerateRequest(BaseModel):
    json_filename: str


@app.post("/generate/")
async def generate_pdf(request: GenerateRequest):
    json_filename = Path(request.json_filename).name
    json_path = TEMP_DIR / json_filename

    if not json_path.exists():
        return JSONResponse(status_code=400, content={
            "error": f"JSON file '{json_filename}' not found in {TEMP_DIR}"
        })

    try:
        result = subprocess.run(
            ["python", str(PROCESS_DIR / "generate_pdf.py"), str(TEMP_DIR / json_filename)],
            capture_output=True,
            text=True,
            check=True
        )
    except subprocess.CalledProcessError as e:
        return JSONResponse(status_code=500, content={
            "error": "PDF generation failed.",
            "details": e.stderr or e.stdout or str(e)
        })
    except Exception as e:
        return JSONResponse(status_code=500, content={
            "error": "Unexpected error.",
            "details": traceback.format_exc()
        })

    # Optional: check if the file was created in temp/pdf instead
    pdf_filename = json_filename.rsplit(".", 1)[0] + ".pdf"

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
    doc = uploads.find_one({"report_name": report_name})
    if not doc:
        return {"error": "Report not found"}
    
    # Assuming you have a binary PDF stored somewhere or generate it from JSON
    pdf_data = doc.get("pdf_data")  # or generate_pdf(doc.json_data)
    if not pdf_data:
        return {"error": "PDF not available for this report"}

    return StreamingResponse(
        pdf_data,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={report_name}.pdf"}
    )