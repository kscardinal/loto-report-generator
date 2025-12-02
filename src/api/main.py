import json
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path
from typing import List
import os
from icecream import ic
import shutil
import jwt
from dotenv import load_dotenv
from argon2 import PasswordHasher
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import pytz
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, TrackingSettings, ClickTracking
from math import ceil
from shapely.geometry import shape, box, Point
from shapely import maximum_inscribed_circle
from collections import defaultdict

from .logging_config import logger, log_requests_json
from .auth_utils import create_access_token, get_current_user, get_current_user_no_redirect, require_role, log_action, get_client_ip, lookup_ip_with_db
from .LatLngFinder import combined_largest_centers_and_plot 

import gridfs
from bson.objectid import ObjectId
from fastapi import FastAPI, UploadFile, File, Form, Request, Response, Depends, HTTPException, status, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, StreamingResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pymongo import MongoClient

app = FastAPI()
load_dotenv()

# -----------------------------
# CORS Configuration
# -----------------------------
origins = [
    "https://lotogenerator.app",   # your main website
    "http://localhost",            # optional: for local browser development
    "http://127.0.0.1",            # optional: for local browser development
    # Add any specific IPs or URLs of your own machines as needed
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["lotogenerator.app", "localhost", "127.0.0.1"])

# Logging
app.middleware("http")(log_requests_json)
logger.info("FastAPI app starting...")

# -----------------------------
# Project paths
# -----------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

from src.database.db_2 import get_report_entry

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "web" / "static"
TEMPLATES_DIR = BASE_DIR / "web" / "templates"     # /app/src/web/templates
DEPENDENCY_DIR = BASE_DIR / "web" / "static" / "dependencies"
TEMP_DIR = BASE_DIR.parent / "temp"
PROCESS_DIR = BASE_DIR / "pdf"
WEB_DIR = BASE_DIR / "src" / "web"

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Ensure TEMP_DIR exists
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# -----------------------------
# MongoDB Connection
# -----------------------------
# Environment variables from .env
MONGO_USER = os.getenv("MONGO_USER", "")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD", "")
MONGO_HOST = os.getenv("MONGO_HOST", "mongo")
MONGO_PORT = os.getenv("MONGO_PORT", "27017")
MONGO_DB = os.getenv("MONGO_DB", "loto_pdf")

# Build URI
if MONGO_USER and MONGO_PASSWORD:
    MONGO_URI = f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}"
else:
    MONGO_URI = f"mongodb://{MONGO_HOST}:{MONGO_PORT}"

client = MongoClient(MONGO_URI)
db = client[MONGO_DB]

# Collections
uploads = db['reports']    # collection for metadata + JSON
users = db['users']        # collection for users + metadata 
audit_logs = db["audit_logs"]
known_locations = db['known_locations']
cached_pdfs = db['cached_pdfs']
fs = gridfs.GridFS(db)     # GridFS for storing photos

# JWT
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY not set in .env")

# Hashing Passwords
ph = PasswordHasher(time_cost=4, memory_cost=102400, parallelism=8, hash_len=32)

# Get email and password from .env file
sender_email = os.getenv("SENDER_EMAIL")
sender_password = os.getenv("SENDER_PASSWORD")

# -----------------------------
# Email Functions
# -----------------------------
def send_email_gmail(to_email, subject, body):
    # Defining the variables for sending the message
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "html"))

    # Sending the data using gmail and variables in the .env file
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, sender_password)
        server.send_message(msg)

def send_email(to_email, subject, body_html, body_text=None):
    message = Mail(
        from_email='no-reply@lotogenerator.app',
        to_emails=to_email,
        subject=subject,
        plain_text_content=body_text if body_text else "Please view this email in an HTML-compatible client.",
        html_content=body_html
    )

    # Disable click tracking so links go straight to your URLs
    tracking_settings = TrackingSettings(click_tracking=ClickTracking(enable=False))
    message.tracking_settings = tracking_settings

    try:
        sg = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
        response = sg.send(message)
        print(f"Email sent! Status code: {response.status_code}")
    except Exception as e:
        print(f"Error sending email: {e}")

def send_email_auto(to_email, subject, body):
    ENV = os.getenv("APP_ENV", "dev").lower()

    if ENV == "dev":
        send_email_gmail(to_email, subject, body)
    elif ENV != "dev":
        send_email(to_email, subject, body)
    else:
        raise ValueError(f"Unknown APP_ENV value: {ENV}")

# -----------------------------
# Upload JSON + images
# -----------------------------
@app.post("/upload/")
async def upload_report(
    request: Request,
    username: str = Depends(get_current_user_no_redirect),
    files: List[UploadFile] = File(...),
    uploaded_by: str = Form("anonymous"),
    tags: List[str] = Form([]),
    notes: str = Form(""),
    background_tasks: BackgroundTasks = None
):
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
                "uploaded_by": username["username"],
                "tags": tags,
                "notes": notes
            }}
        )

        log_action(
            request=request,
            audit_logs_collection=audit_logs,
            known_locations_collection=known_locations,
            username=username["username"],
            action="upload",
            details={"report": report_name, "status": "update"},
            background_tasks=background_tasks
        )

    else:
        uploads.insert_one({
            "report_name": report_name,
            "json_data": json_data,
            "photos": photos_data,
            "uploaded_by": username["username"],
            "tags": tags,
            "notes": notes,
            "date_added": now,
            "last_modified": now,
            "last_generated": now,
            "version": 1
        })

        log_action(
            request=request,
            audit_logs_collection=audit_logs,
            known_locations_collection=known_locations,
            username=username["username"],
            action="upload",
            details={"report": report_name, "status": "insert"},
            background_tasks=background_tasks
        )

    return {"report_name": report_name, "photos": [p["photo_name"] for p in photos_data]}

# -----------------------------
# Download PDF (streams PDF directly to client with caching)
# -----------------------------
@app.get("/download_pdf/{report_name}", name="download_pdf")
def download_pdf(
    request: Request,
    report_name: str,
    username: str = Depends(get_current_user_no_redirect),
    background_tasks: BackgroundTasks = None
):
    doc = uploads.find_one({"report_name": report_name})
    if not doc:
        return JSONResponse(status_code=404, content={"error": f"Report '{report_name}' not found"})
        
    # --- 1. CHECK CACHE (Cache Hit) ---
    cached_doc = cached_pdfs.find_one({"report_name": report_name})
    if cached_doc:
        try:
            # Retrieve PDF from GridFS
            pdf_bytes = fs.get(cached_doc["gridfs_id"]).read()

            # Log cache hit
            log_action(
                request=request, audit_logs_collection=audit_logs, known_locations_collection=known_locations,
                username=username["username"], action="download_pdf_cache_hit", 
                details={"report": report_name}, background_tasks=background_tasks
            )

            # Update timestamp in cache to keep it "fresh" and prevent deletion
            cached_pdfs.update_one(
                {"_id": cached_doc["_id"]},
                {"$set": {"last_accessed": datetime.now(timezone.utc)}} # Use UTC for consistency
            )

            print(f"DEBUG: Cache hit for {report_name}")
            return StreamingResponse(
                BytesIO(pdf_bytes),
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename={report_name}.pdf"}
            )
        except Exception as e:
            # If GridFS retrieval fails, proceed to regenerate (Cache Miss path)
            print(f"DEBUG: Cache retrieval failed for {report_name}: {e}. Regenerating.")
            pass # continue to the generation path below

    # --- 2. CACHE MISS / PDF GENERATION (Expensive operation) ---
    pdf_bytes = None
    
    try:
        # ** Your existing PDF generation logic starts here **
        
        TEMP_DIR.mkdir(exist_ok=True) 

        # Write JSON data
        json_file_path = TEMP_DIR / f"{report_name}.json"
        with open(json_file_path, "w", encoding="utf-8") as f:
            json.dump(doc["json_data"], f, ensure_ascii=False, indent=2)

        # Write photos
        for photo in doc["photos"]:
            photo_file_path = TEMP_DIR / photo["photo_name"]
            with open(photo_file_path, "wb") as f:
                f.write(fs.get(photo["photo_id"]).read())

        # Generate PDF
        pdf_file_path = TEMP_DIR / f"{report_name}.pdf"
        subprocess.run(
            ["python", str(PROCESS_DIR / "generate_pdf.py"), str(json_file_path)],
            check=True
        )

        pdf_bytes = pdf_file_path.read_bytes() # Store the generated bytes

        # Update last_generated timestamp on the main report document
        uploads.update_one(
            {"_id": doc["_id"]},
            {"$set": {"last_generated": datetime.now()}}
        )

        # Clear TEMP_DIR (Your existing cleanup logic)
        for item in TEMP_DIR.iterdir():
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)

        # --- 3. CACHE UPDATE (After successful generation) ---
        if pdf_bytes:
            # Store the new PDF bytes in GridFS
            gridfs_id = fs.put(pdf_bytes, filename=f"{report_name}.pdf", content_type="application/pdf")
            
            # Record the cache metadata
            cached_pdfs.insert_one({
                "report_name": report_name,
                "gridfs_id": gridfs_id,
                "created_at": datetime.now(timezone.utc),
                "last_accessed": datetime.now(timezone.utc),
            })
            
            # Schedule cache cleanup to run in the background
            background_tasks.add_task(clean_pdf_cache, cached_pdfs, fs)


        # Log successful generation and stream response
        log_action(
            request=request, audit_logs_collection=audit_logs, known_locations_collection=known_locations,
            username=username["username"], action="download_pdf",
            details={"report": report_name, "status": "Generated & Cached"},
            background_tasks=background_tasks
        )

        return StreamingResponse(
            BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={report_name}.pdf"}
        )

    # --- 4. ERROR HANDLING ---
    except subprocess.CalledProcessError as e:
        log_action(
            request=request,
            audit_logs_collection=audit_logs,
            known_locations_collection=known_locations,
            username=username["username"],
            action="download_pdf",
            details={"report": report_name, "status": "Failed", "message": e.stderr },
            background_tasks=background_tasks
        )
        return JSONResponse(status_code=500, content={"error": "PDF generation failed.", "details": e.stderr})
    except Exception as e:
        import traceback
        log_action(
            request=request,
            audit_logs_collection=audit_logs,
            known_locations_collection=known_locations,
            username=username["username"],
            action="download_pdf",
            details={"report": report_name, "status": "Failed", "message": traceback.format_exc() },
            background_tasks=background_tasks
        )
        return JSONResponse(status_code=500, content={"error": "Unexpected error.", "details": traceback.format_exc()})
    
# ---------------------------------------------------------
# Generate a single PDF and return the bytes
# ---------------------------------------------------------
def generate_pdf_bytes(report_name: str):
    doc = uploads.find_one({"report_name": report_name})
    if not doc:
        raise Exception(f"Report '{report_name}' not found")

    TEMP_DIR.mkdir(exist_ok=True)

    # Write JSON file
    json_file_path = TEMP_DIR / f"{report_name}.json"
    with open(json_file_path, "w", encoding="utf-8") as f:
        json.dump(doc["json_data"], f, ensure_ascii=False, indent=2)

    # Write photos
    for photo in doc["photos"]:
        p = TEMP_DIR / photo["photo_name"]
        with open(p, "wb") as f:
            f.write(fs.get(photo["photo_id"]).read())

    # Run PDF generator
    pdf_file_path = TEMP_DIR / f"{report_name}.pdf"
    subprocess.run(
        ["python", str(PROCESS_DIR / "generate_pdf.py"), str(json_file_path)],
        check=True
    )

    # Read PDF bytes
    pdf_bytes = pdf_file_path.read_bytes()

    # Clean up TEMP_DIR
    for item in TEMP_DIR.iterdir():
        if item.is_file():
            item.unlink()
        else:
            shutil.rmtree(item)

    # Update last_generated timestamp
    uploads.update_one(
        {"_id": doc["_id"]},
        {"$set": {"last_generated": datetime.now()}}
    )

    return pdf_bytes


# ---------------------------------------------------------
# Bulk PDF Download (returns ZIP)
# ---------------------------------------------------------
@app.post("/download_pdf_bulk", name="download_pdf_bulk")
async def download_pdf_bulk(
    request: Request,
    payload: dict,
    username: str = Depends(get_current_user_no_redirect),
    background_tasks: BackgroundTasks = None
):
    import io
    from zipfile import ZipFile

    report_names = payload.get("reports", [])
    if not isinstance(report_names, list) or not report_names:
        return JSONResponse(status_code=400, content={"error": "Missing or invalid 'reports' list"})

    zip_buffer = io.BytesIO()
    errors = []

    # Create ZIP in memory
    with ZipFile(zip_buffer, "w") as zipf:

        for report_name in report_names:
            try:
                # -----------------------------------------
                # 1. Try Cache First
                # -----------------------------------------
                cached_doc = cached_pdfs.find_one({"report_name": report_name})
                if cached_doc:
                    try:
                        pdf_bytes = fs.get(cached_doc["gridfs_id"]).read()

                        # Refresh cache timestamp
                        cached_pdfs.update_one(
                            {"_id": cached_doc["_id"]},
                            {"$set": {"last_accessed": datetime.now(timezone.utc)}}
                        )

                        zipf.writestr(f"{report_name}.pdf", pdf_bytes)
                        continue
                    except Exception:
                        pass  # Cache broken → regenerate

                # -----------------------------------------
                # 2. Cache miss → Regenerate (CPU-safe: sequential)
                # -----------------------------------------
                pdf_bytes = generate_pdf_bytes(report_name)

                zipf.writestr(f"{report_name}.pdf", pdf_bytes)

                # Save new PDF to cache
                gridfs_id = fs.put(
                    pdf_bytes, filename=f"{report_name}.pdf", content_type="application/pdf"
                )

                cached_pdfs.insert_one({
                    "report_name": report_name,
                    "gridfs_id": gridfs_id,
                    "created_at": datetime.now(timezone.utc),
                    "last_accessed": datetime.now(timezone.utc),
                })

            except Exception as e:
                errors.append(f"{report_name}: {str(e)}")

        # Add error log into ZIP
        if errors:
            zipf.writestr("errors.txt", "\n".join(errors))

    # Audit log
    log_action(
        request=request,
        audit_logs_collection=audit_logs,
        known_locations_collection=known_locations,
        username=username["username"],
        action="download_pdf_bulk",
        details={"reports": report_names},
        background_tasks=background_tasks
    )

    # Create a timestamped filename
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
    zip_filename = f"bulk_reports_{timestamp}.zip"

    # Return zipped buffer
    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={zip_filename}"}
    )

# -----------------------------
# CACHE MAINTENANCE FUNCTION (MUST BE DEFINED)
# -----------------------------

def clean_pdf_cache(cached_pdfs_collection, fs_gridfs, max_cache_size=100):
    """Deletes the oldest PDFs from the cache if the size exceeds the limit."""
    
    # Check current cache size
    current_size = cached_pdfs_collection.count_documents({})
    
    if current_size > max_cache_size:
        # Find the documents to delete (oldest first, based on last_accessed)
        # We delete all documents beyond the max_cache_size limit.
        docs_to_delete = cached_pdfs_collection.find().sort("last_accessed", 1).limit(current_size - max_cache_size)
        
        for doc in docs_to_delete:
            try:
                # 1. Delete the actual file from GridFS
                fs_gridfs.delete(doc["gridfs_id"])
                
                # 2. Delete the metadata record
                cached_pdfs_collection.delete_one({"_id": doc["_id"]})
                
            except Exception as e:
                # Log error if deletion fails, but continue to clean the rest
                print(f"Error cleaning cache document {doc.get('report_name', doc['_id'])}: {e}")


# -----------------------------
# Clear temp folder
# -----------------------------
@app.post("/clear/")
async def clear_temp_folders(
    username: str = Depends(get_current_user_no_redirect)
):
    for file in TEMP_DIR.iterdir():
        if file.is_file():
            file.unlink()
    return {"message": "All temp data cleared."}

# -----------------------------
# View all PDFs (HTML)
# -----------------------------
@app.get("/pdf_list", response_class=HTMLResponse)
async def pdf_list(
    request: Request, 
    current_user: dict = Depends(get_current_user),
    background_tasks: BackgroundTasks = None
):
    if isinstance(current_user, RedirectResponse):
        return current_user

    # Fetch report names
    docs = uploads.find({}, {"_id": 0, "report_name": 1}).sort("last_modified", -1)
    report_names = [doc.get("report_name") for doc in docs if doc.get("report_name")]

    return templates.TemplateResponse(
        "pdf_list.html",
        {"request": request, "report_names": report_names, "current_user": current_user}
    )

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

def format_datetime_with_ordinal(dt: datetime, tz_offset: int = 0) -> str:
    """
    Format datetime with ordinal, weekday, month, year, and 12-hour time.
    tz_offset: integer, hours to offset from UTC (can be negative)
    """
    if tz_offset != 0:
        dt = dt + timedelta(hours=tz_offset)
    day_with_suffix = ordinal(dt.day)
    return dt.strftime(f"%A, %B {day_with_suffix}, %Y at %I:%M:%S %p")\
             .lstrip("0").replace("AM","am").replace("PM","pm")

# -----------------------------
# View single report (HTML)
# -----------------------------
@app.get("/view_report/{report_name}", response_class=HTMLResponse)
async def view_report(
    request: Request,
    report_name: str,
    username: str = Depends(get_current_user),
    tz_offset: int = 0,
    background_tasks: BackgroundTasks = None  
):
    if isinstance(username, RedirectResponse):
        return username

    doc = get_report_entry(uploads, fs, report_name, fetch_photos=True)
    if not doc:
        return HTMLResponse(f"<h1>Report '{report_name}' not found</h1>", status_code=404)

    log_action(
        request=request,
        audit_logs_collection=audit_logs,
        known_locations_collection=known_locations,
        username=username["username"],
        action="view_report",
        details={"report": report_name},
        background_tasks=background_tasks
    )

    for key in ["date_added", "last_modified", "last_generated"]:
        if key in doc and isinstance(doc[key], datetime):
            doc[key] = doc[key].isoformat()

    return templates.TemplateResponse("view_report.html", {"request": request, "report": doc, "current_user": username})

# -----------------------------
# Fetch individual photo
# -----------------------------
@app.get("/photo/{photo_id}")
def get_photo(
    photo_id: str, 
    username: str = Depends(get_current_user_no_redirect)
):
    photo = fs.get(ObjectId(photo_id))
    return Response(photo.read(), media_type="image/jpeg")

# -----------------------------
# Fetch metadata for a given report
# -----------------------------
@app.get("/metadata/{report_name}")
async def get_metadata(
    report_name: str, 
    username: str = Depends(get_current_user_no_redirect)
):
    doc = uploads.find_one(
        {"report_name": report_name},
        {"_id": 0, "json_data": 0, "photos": 0}
    )
    if not doc:
        return JSONResponse(status_code=404, content={"error": f"Report '{report_name}' not found"})

    for key in ["date_added", "last_modified", "last_generated"]:
        if key in doc and isinstance(doc[key], datetime):
            doc[key] = doc[key].isoformat()

    return JSONResponse(content=doc)

# -----------------------------
# Check status of database
# -----------------------------
@app.get("/db_status")
async def db_status(
    current_user: dict = Depends(get_current_user_no_redirect)
):
    # Ensure only admins can modify
    error = require_role("admin")(current_user)
    if error:
        return error
    
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
async def create_report(
    request: Request, 
    username: str = Depends(get_current_user),
    background_tasks: BackgroundTasks = None
):
    if isinstance(username, RedirectResponse):
        return username
    
    log_action(
        request=request,
        audit_logs_collection=audit_logs,
        known_locations_collection=known_locations,
        username=username["username"],
        action="create_report",
        details={},
        background_tasks=background_tasks
    )

    return templates.TemplateResponse("input_form.html", {"request": request, "current_user": username})

# -----------------------------
# Remove a report from the database
# -----------------------------
@app.api_route("/remove_report/{report_name}", methods=["GET", "POST"])
async def remove_report(
    request: Request, 
    report_name: str, 
    username: str = Depends(get_current_user_no_redirect),
    background_tasks: BackgroundTasks = None
):
    doc = uploads.find_one({"report_name": report_name})
    if not doc:
        return JSONResponse(status_code=404, content={"error": f"Report '{report_name}' not found"})

    photo_names = [p["photo_name"] for p in doc.get("photos", [])]
    result = uploads.delete_one({"_id": doc["_id"]})
    if result.deleted_count == 0:
        return JSONResponse(status_code=500, content={"error": f"Failed to delete report '{report_name}'"})

    details = {"report": report_name}
    if photo_names:  # Only add if not empty
        details["photos_retained"] = photo_names

    log_action(
        request=request,
        audit_logs_collection=audit_logs,
        known_locations_collection=known_locations,
        username=username["username"],
        action="remove_report",
        details=details,
        background_tasks=background_tasks
    )

    return {
        "message": f"Report '{report_name}' deleted successfully.",
        "photos_retained": photo_names
    }

# -----------------------------
# Cleanup orphaned photos from GridFS
# -----------------------------
def sizeof_fmt(num, suffix="B"):
    """Human-readable file size."""
    for unit in ["", "K", "M", "G", "T"]:
        if abs(num) < 1024:
            return f"{num:.1f} {unit}{suffix}"
        num /= 1024
    return f"{num:.1f}P{suffix}"

@app.api_route("/cleanup_orphan_photos", methods=["GET", "POST"])
async def cleanup_orphan_photos(
    request: Request,  # for logging
    background_tasks: BackgroundTasks,
    username: dict = Depends(get_current_user_no_redirect)
):
    # Require admin access
    error = require_role("admin")(username)
    if error:
        log_action(
            request=request,
            audit_logs_collection=audit_logs,
            known_locations_collection=known_locations,
            username=username["username"],
            action="cleanup_orphan_photos",
            details={"status": "Invalid Permission"},
            background_tasks=background_tasks
        )
        return error

    deleted_photos = {}
    deleted_cached_pdfs = {}
    total_photo_bytes = 0
    total_pdf_bytes = 0
    errors = []

    # --- Build sets of referenced IDs ---
    # Photos referenced by reports
    referenced_photo_ids = set()
    for doc in uploads.find({}, {"photos.photo_id": 1}):
        for p in doc.get("photos", []):
            pid = p.get("photo_id")
            if pid is not None:
                referenced_photo_ids.add(pid)

    # Cached PDFs: gather all cache docs and referenced ids
    pdf_cache_docs = list(cached_pdfs.find({}))
    referenced_pdf_ids = set()
    for cache_doc in pdf_cache_docs:
        fid = cache_doc.get("gridfs_id")
        if fid is not None:
            referenced_pdf_ids.add(fid)

    # Existing report names (to know if a cached PDF's report still exists)
    existing_reports = set(uploads.distinct("report_name"))

    # --- Handle cached PDFs first: remove only when report no longer exists ---
    for cache_doc in pdf_cache_docs:
        report_name = cache_doc.get("report_name")
        file_id = cache_doc.get("gridfs_id")

        if not file_id:
            errors.append({
                "photo_id": None,
                "filename": None,
                "error": "cached_pdfs entry missing gridfs_id",
            })
            continue

        # If the related report still exists, keep this cached PDF
        if report_name in existing_reports:
            continue

        # Report no longer exists -> delete cached PDF and its cache document
        try:
            try:
                grid_out = fs.get(ObjectId(file_id))
                filename = grid_out.filename
                length = getattr(grid_out, "length", 0) or 0
                fs.delete(ObjectId(file_id))
                deleted_cached_pdfs[str(file_id)] = {
                    "filename": filename,
                    "report_name": report_name,
                }
                total_pdf_bytes += int(length)
            except Exception as e:
                # Couldn't delete the GridFS file, log as error but still attempt to delete cache doc
                errors.append({
                    "photo_id": str(file_id),
                    "filename": None,
                    "error": f"Failed to delete cached PDF from GridFS: {e}",
                })

            # Remove the cache document itself
            try:
                cached_pdfs.delete_one({"_id": cache_doc["_id"]})
            except Exception as e:
                errors.append({
                    "photo_id": str(file_id),
                    "filename": None,
                    "error": f"Failed to delete cached_pdfs document: {e}",
                })
        except Exception as e:
            errors.append({
                "photo_id": str(file_id),
                "filename": None,
                "error": f"Unexpected error while cleaning cached PDF: {e}",
            })

    # --- Now clean truly orphaned files from GridFS ---
    for grid_out in fs.find():
        file_id = grid_out._id

        # Skip if this file is referenced as a photo
        if file_id in referenced_photo_ids:
            continue

        # Skip if this file is currently referenced by cached_pdfs (active cached PDF)
        if file_id in referenced_pdf_ids:
            continue

        filename = grid_out.filename
        length = getattr(grid_out, "length", 0) or 0

        # Treat PDFs separately as cached/stray PDFs
        if isinstance(filename, str) and filename.lower().endswith(".pdf"):
            try:
                fs.delete(file_id)
                deleted_cached_pdfs[str(file_id)] = {
                    "filename": filename,
                    "report_name": None,
                }
                total_pdf_bytes += int(length)
            except Exception as e:
                errors.append({
                    "photo_id": str(file_id),
                    "filename": filename,
                    "error": str(e),
                })
            continue

        # Regular photo: delete if no references
        try:
            fs.delete(file_id)
            deleted_photos[str(file_id)] = filename
            total_photo_bytes += int(length)
        except Exception as e:
            errors.append({
                "photo_id": str(file_id),
                "filename": filename,
                "error": str(e),
            })

    # --- Build details for audit log ---
    details = {}
    num_photos = len(deleted_photos)
    num_pdfs = len(deleted_cached_pdfs)
    total_bytes = total_photo_bytes + total_pdf_bytes

    if num_photos == 0 and num_pdfs == 0:
        details["status"] = "No orphaned photos or cached PDFs to remove"
    else:
        size = sizeof_fmt(total_bytes)
        details["status"] = f"{num_photos} photos and {num_pdfs} cached PDFs removed ({size} total)"
        details["photos_removed"] = deleted_photos
        details["cached_pdfs_removed"] = deleted_cached_pdfs

    log_action(
        request=request,
        audit_logs_collection=audit_logs,
        known_locations_collection=known_locations,
        username=username["username"],
        action="clean_orphan_photos",
        details=details,
        background_tasks=background_tasks
    )

    # --- Send summary email to DEFAULT_EMAIL ---
    try:
        to_email = os.getenv("DEFAULT_EMAIL", "")
        subject = "LOTO Generator - Orphaned Photos & Cached PDFs Cleanup Report"
        utc_time = datetime.utcnow()
        eastern = pytz.timezone("US/Eastern")
        local_time = utc_time.replace(tzinfo=pytz.utc).astimezone(eastern)
        formatted_time = local_time.strftime("%B %d, %Y %I:%M %p %Z")

        # Build rows for removed photos
        photo_rows = ""
        if deleted_photos:
            for pid, name in deleted_photos.items():
                photo_rows += f"<tr><td>{pid}</td><td>{name}</td></tr>"
        else:
            photo_rows = "<tr><td colspan=2>No orphaned photos removed</td></tr>"

        # Build rows for removed cached PDFs
        pdf_rows = ""
        if deleted_cached_pdfs:
            for pid, info in deleted_cached_pdfs.items():
                fname = info.get("filename")
                rname = info.get("report_name")
                pdf_rows += f"<tr><td>{pid}</td><td>{fname}</td><td>{rname}</td></tr>"
        else:
            pdf_rows = "<tr><td colspan=3>No cached PDFs removed</td></tr>"

        # Build rows for errors if any
        error_rows = ""
        if errors:
            for err in errors:
                error_rows += f"<tr><td>{err.get('photo_id')}</td><td>{err.get('filename')}</td><td>{err.get('error')}</td></tr>"
        else:
            error_rows = "<tr><td colspan=3>No errors reported</td></tr>"

        size_str = sizeof_fmt(total_bytes) if total_bytes else "0 B"

        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin-right:5%; margin-left:5%; padding:0; }}
                h2 {{ color: #C32026; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
                th, td {{ text-align: left; padding: 8px; border-bottom: 1px solid #dddddd; }}
                th {{ background-color: #f0f0f0; }}
                .footer {{ margin-top: 20px; font-size: 12px; color: #777777; }}
            </style>
        </head>
        <body>
            <h2>Orphaned Photos &amp; Cached PDFs Cleanup Report</h2>
            <p>Cleanup run time: <strong>{formatted_time}</strong></p>
            <p>Summary: <strong>{num_photos} photos</strong> and <strong>{num_pdfs} cached PDFs</strong> removed — total size {size_str}.</p>

            <h3>Removed Photos</h3>
            <table>
                <tr><th>Photo ID</th><th>Filename</th></tr>
                {photo_rows}
            </table>

            <h3>Removed Cached PDFs</h3>
            <table>
                <tr><th>PDF ID</th><th>Filename</th><th>Report Name</th></tr>
                {pdf_rows}
            </table>

            <h3>Errors</h3>
            <table>
                <tr><th>ID</th><th>Filename</th><th>Error</th></tr>
                {error_rows}
            </table>

            <p class="footer">This is an automated report from LOTO Report Generator.</p>
        </body>
        </html>
        """

        if to_email:
            try:
                send_email_auto(to_email, subject, html_content)
            except Exception:
                logger.exception("Failed to send cleanup email report")
    except Exception:
        logger.exception("Failed while preparing or sending cleanup email report")

    return {
        "message": (
            f"Cleanup complete. {len(deleted_photos)} orphaned photos and "
            f"{len(deleted_cached_pdfs)} cached PDFs deleted."
        ),
        "deleted_photos": deleted_photos,
        "deleted_cached_pdfs": deleted_cached_pdfs,
        "errors": errors
    }

@app.get("/photos_info")
async def photos_info(
    request: Request, 
    username: dict = Depends(get_current_user_no_redirect)
):
    # Require admin access
    error = require_role("admin")(username)
    if error:
        return JSONResponse(status_code=403, content={"error": "forbidden"})

    photos = []

    # Use the default GridFS collections (fs.files and fs.chunks)
    files_coll = db.get_collection("fs.files")
    chunks_coll = db.get_collection("fs.chunks")

    # Iterate GridFS entries via files collection for predictable metadata
    for file_doc in files_coll.find({}, sort=[("uploadDate", -1)]):
        file_id = file_doc.get("_id")
        filename = file_doc.get("filename")
        length = file_doc.get("length")
        chunk_size = file_doc.get("chunkSize")
        upload_date = file_doc.get("uploadDate")
        md5 = file_doc.get("md5")
        metadata = file_doc.get("metadata")

        # Get chunks for this file
        chunk_docs = list(chunks_coll.find({"files_id": file_id}).sort([("n", 1)]))
        chunk_ids = [str(c.get("_id")) for c in chunk_docs]
        num_chunks = len(chunk_ids)

        # Find reports referencing this photo id
        related_reports_cursor = uploads.find({"photos.photo_id": file_id}, {"report_name": 1, "_id": 0})
        related_reports = [r.get("report_name") for r in related_reports_cursor]

        photos.append({
            "photo_id": str(file_id),
            "filename": filename,
            "size_bytes": int(length) if length is not None else None,
            "chunk_size": int(chunk_size) if chunk_size is not None else None,
            "num_chunks": num_chunks,
            "chunk_ids": chunk_ids,
            "upload_date": upload_date.isoformat() if upload_date is not None else None,
            "md5": md5,
            "metadata": metadata,
            "related_reports": related_reports,
        })

    # Summary statistics
    total_photos = len(photos)
    total_chunks = sum(p.get("num_chunks", 0) for p in photos)
    total_size_bytes = sum(p.get("size_bytes", 0) or 0 for p in photos)
    photos_without_report = [p["photo_id"] for p in photos if not p.get("related_reports")]

    summary = {
        "total_photos": total_photos,
        "total_chunks": total_chunks,
        "total_size_bytes": total_size_bytes,
        "photos_without_report_count": len(photos_without_report),
        "photos_without_report_ids": photos_without_report,
    }

    return JSONResponse(content={"summary": summary, "photos": photos})

# -----------------------------
# JSON endpoints - Server-side pagination
# -----------------------------
@app.get("/pdf_list_json")
async def pdf_list_json(
    page: int = 1,
    per_page: int = 25,
    username: str = Depends(get_current_user_no_redirect)
):
    # Ensure valid values
    if page < 1:
        page = 1
    if per_page < 1:
        per_page = 25

    skip = (page - 1) * per_page

    total_reports = uploads.count_documents({})

    # Query paginated + sorted by report_name
    cursor = (
        uploads.find({}, {"_id": 0, "json_data": 0, "photos": 0})
        .sort([("last_modified", -1), ("report_name", 1)])
        .skip(skip)
        .limit(per_page)
    )

    report_list = []
    for doc in cursor:
        # Photo count (you excluded "photos" so doc.get might be missing)
        photo_count = len(doc.get("photos", [])) if "photos" in doc else 0

        # Convert datetimes into ISO strings
        for key in ["date_added", "last_modified", "last_generated"]:
            if key in doc and isinstance(doc[key], datetime):
                eastern = pytz.timezone("US/Eastern")
                local_time = doc[key].replace(tzinfo=pytz.utc).astimezone(eastern)
                formatted_time = local_time.strftime("%B %d, %Y %I:%M:%S %p %Z")
                doc[key] = formatted_time

        doc["num_photos"] = photo_count
        report_list.append(doc)

    return {
        "page": page,
        "per_page": per_page,
        "total": total_reports,
        "reports": report_list,
        "total_pages": (total_reports + per_page - 1) // per_page,
    }

# -----------------------------
# Download JSON + all related photos (separately)
# -----------------------------
@app.get("/download_report_files/{report_name}", name="download_report_files")
def download_report_files(
    report_name: str, 
    username: str = Depends(get_current_user_no_redirect)
):
    doc = uploads.find_one({"report_name": report_name})
    if not doc:
        return JSONResponse(status_code=404, content={"error": f"Report '{report_name}' not found"})

    file_list = [{"filename": f"{report_name}.json", "url": f"/download_json/{report_name}"}]
    for photo in doc.get("photos", []):
        file_list.append({"filename": photo.get("photo_name", f"{photo['photo_id']}.jpg"), "url": f"/download_photo/{photo['photo_id']}"})

    return {"report_name": report_name, "files": file_list}

# -----------------------------
# Download JSON file for a report
# -----------------------------
@app.get("/download_json/{report_name}", name="download_json")
def download_json(
    report_name: str, 
    username: str = Depends(get_current_user_no_redirect)
):
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
def download_photo(
    photo_id: str, 
    username: str = Depends(get_current_user_no_redirect)
):
    try:
        grid_out = fs.get(ObjectId(photo_id))
    except Exception:
        return JSONResponse(status_code=404, content={"error": f"Photo '{photo_id}' not found"})

    headers = {"Content-Disposition": f"attachment; filename={grid_out.filename}"}
    return StreamingResponse(grid_out, media_type="image/jpeg", headers=headers)



# -----------------------------
# JWT Test Page
# -----------------------------
@app.get("/jwt_test", response_class=HTMLResponse)
async def jwt_test(
    request: Request, 
    username: str = Depends(get_current_user_no_redirect)
):
    if isinstance(username, RedirectResponse):
        return username  # redirect for web if not authenticated

    # If mobile or logged in web user
    return JSONResponse({"message": f"JWT verified successfully! Welcome {username}"})










# -----------------------------
# Users List Page
# -----------------------------
@app.get("/users", response_class=HTMLResponse)
async def users_page(
    request: Request, 
    current_user: dict = Depends(get_current_user),
    background_tasks: BackgroundTasks = None
):
    if isinstance(current_user, RedirectResponse):
        return current_user

    # Require owner access
    error = require_role("owner")(current_user)
    if error:
        log_action(
            request=request,
            audit_logs_collection=audit_logs,
            known_locations_collection=known_locations,
            username=current_user["username"],
            action="users",
            details={"status": "Invalid Permission"},
            background_tasks=background_tasks
        )
        return error

    return templates.TemplateResponse("user_list.html", {
        "request": request,
        "current_user": current_user
    })


@app.get("/users_json")
async def users_json(
    current_user: dict = Depends(get_current_user_no_redirect)
):
    # Require owner access
    error = require_role("owner")(current_user)
    if error:
        return error
    
    users_cursor = users.find({}, {"_id": 0})
    user_list = []

    for doc in users_cursor:
        for key, value in doc.items():
            if isinstance(value, datetime):
                doc[key] = value.isoformat()
        user_list.append(doc)

    return {"users": user_list}


# -----------------------------
# Login Page
# -----------------------------
def login_email(user, geo):
    """
    Sends a formatted HTML email when a user logs in.
    `user` is a dictionary with first_name, last_name, email, username, date_created, etc.
    """
    to_email = user.get("email")
    if not to_email:
        return
    subject = f"LOTO Generator - A new device is using your account"

    # Convert UTC to Eastern Time
    utc_time = datetime.utcnow()
    eastern = pytz.timezone("US/Eastern")  # change this to your timezone if needed
    local_time = utc_time.replace(tzinfo=pytz.utc).astimezone(eastern)
    formatted_time = local_time.strftime("%B %d, %Y %I:%M %p %Z")

    # IP
    if geo is None:
        location_str = "unknown"
    else:
        city = geo["location"].get("city")
        region = geo["location"].get("region")
        country = geo["location"].get("country")

        # if all are missing, just say "unknown"
        if not any([city, region, country]):
            location_str = "unknown"
        else:
            # join non-empty values with commas
            location_str = ", ".join(filter(None, [city, region, country]))


    # Build the HTML content
    html_content = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: transparent;
                margin-right: 5%;
                margin-left: 5%;
                padding: 0;
            }}
            h2 {{
                color: #C32026;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
            }}
            th, td {{
                text-align: left;
                padding: 8px;
                border-bottom: 1px solid #dddddd;
            }}
            th {{
                background-color: #f0f0f0;
            }}
            .footer {{
                margin-top: 20px;
                font-size: 12px;
                color: #777777;
            }}
        </style>
    </head>
    <body>
        <h2>New Login Detected</h2>
        <p>A new device is using your account:</p>
        <table>
            <tr><th>Field</th><th>Value</th></tr>
            <tr><td>First Name</td><td>{user.get('first_name', '')[:1].upper() + user.get('first_name', '')[1:] if user.get('first_name') else ''}</td></tr>
            <tr><td>Last Name</td><td>{user.get('last_name', '')[:1].upper() + user.get('last_name', '')[1:] if user.get('last_name') else ''}</td></tr>
            <tr><td>Username</td><td>{user.get('username', '')}</td></tr>
            <tr><td>Email</td><td>{user.get('email', '')}</td></tr>
            <tr><td>Date Accessed</td><td>{formatted_time}</td></tr>
            <tr><td>IP Address</td><td>{geo.get('ip_address', 'unknown') if geo else 'unknown'}</td></tr>
            <tr><td>Location</td><td>{location_str}</td></tr>
        </table>
        <p>If this wasn't you, please change password using the link below</p>
        <p>
          <a href="https://lotogenerator.app/forgot_password" 
             style="background-color:#C32026; color:#ffffff; text-decoration:none; padding:10px 20px; border-radius:5px; display:inline-block;">
             Change Password
          </a>
        </p>
        <p class="footer">This is an automated message from LOTO Report Generator. Do not reply.</p>
    </body>
    </html>
    """

    # Send email using your auto function
    send_email_auto(to_email, subject, html_content)

def lockout_email(user, lockout_time):
    """
    Sends an email when a user account is locked due to too many failed attempts.
    """
    to_email = user.get("email")
    if not to_email:
        return
    
    # Check if the lock is a "hard lock" (24 hours or more)
    is_hard_lock = (lockout_time - datetime.now(timezone.utc)).total_seconds() >= (23 * 3600) # Check for 23 hours to be safe
    
    subject = "LOTO Generator - Your Account Has Been Locked"

    # Convert lockout_time (which is UTC aware) to Eastern Time for the user
    eastern = pytz.timezone("US/Eastern")
    local_unlock_time = lockout_time.astimezone(eastern)
    formatted_unlock_time = local_unlock_time.strftime("%B %d, %Y at %I:%M %p %Z")
    
    # Adjust message for hard lock
    if is_hard_lock:
        lock_detail_paragraph = """
        <p>This is a <strong>hard lock</strong> due to repeated failed login attempts. To unlock your account, you must <strong>reset your password</strong> immediately.</p>
        """
    else:
        lock_detail_paragraph = f"""
        <p>You may attempt to log in again after:</p>
        <p style="font-size: 1.2em; font-weight: bold; color: #C32026;">
            {formatted_unlock_time}
        </p>
        <p>If you made these attempts, you can wait for the lockout to expire or immediately reset your password.</p>
        """


    html_content = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: transparent;
                margin-right: 5%;
                margin-left: 5%;
                padding: 0;
            }}
            h2 {{
                color: #C32026;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
            }}
            th, td {{
                text-align: left;
                padding: 8px;
                border-bottom: 1px solid #dddddd;
            }}
            th {{
                background-color: #f0f0f0;
            }}
            .footer {{
                margin-top: 20px;
                font-size: 12px;
                color: #777777;
            }}
        </style>
    </head>
    <body>
        <h2>Account Locked</h2>
        <p>Dear {user.get('first_name', 'User')},</p>
        <p>Your account, <strong>{user.get('username', '')}</strong>, has been temporarily locked because there were too many unsuccessful login attempts.</p>
        
        <h3>Lockout Details</h3>
        {lock_detail_paragraph}
        
        <p>If you did not attempt to log in, this indicates someone else may be trying to access your account. <strong>We strongly recommend you change your password immediately.</strong></p>
        
        <p>
          <a href="https://lotogenerator.app/forgot_password" 
             style="background-color:#C32026; color:#ffffff; text-decoration:none; padding:10px 20px; border-radius:5px; display:inline-block;">
            Reset Password Now
          </a>
        </p>
        <p class="footer">This is an automated security message from LOTO Report Generator. Do not reply.</p>
    </body>
    </html>
    """

    send_email_auto(to_email, subject, html_content)

@app.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request,
    background_tasks: BackgroundTasks = None
):
    log_action(
        request=request,
        audit_logs_collection=audit_logs,
        known_locations_collection=known_locations,
        username="N/A",
        action="login page",
        details={},
        background_tasks=background_tasks
    )
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

# --- Configuration Constants (Repeat for context) ---
LOCKOUT_STAGES = {
    5: 5,        # Stage 1: 5 attempts -> 5 minutes lock
    10: 15,      # Stage 2: 10 attempts -> 15 minutes lock
    15: 60,      # Stage 3: 15 attempts -> 60 minutes (1 hour) lock
    20: 525600   # Hard Lock: 20 attempts -> 1 year lockout (Requires Admin/Support)
}
HARD_LOCK_ATTEMPTS = 20 # The final threshold for the hardest lock

@app.post("/login")
async def login_endpoint(
    request: Request,
    data: dict,
    background_tasks: BackgroundTasks = None
):
    username_or_email = data.get("username_or_email")
    password = data.get("password")
    username_or_email_lower = username_or_email.lower()
    current_time = datetime.now(timezone.utc)

    user = users.find_one({
        "$or": [
            {"username": username_or_email_lower},
            {"email": username_or_email}
        ]
    })

    if not user:
        # Prevent user enumeration: Return 401
        log_action(
            request=request,
            audit_logs_collection=audit_logs,
            known_locations_collection=known_locations,
            username=username_or_email_lower,
            action="login",
            details={"status": f"fail: no user matching {username_or_email_lower}"},
            background_tasks=background_tasks
        )
        return JSONResponse({"message": "Wrong password"}, status_code=401)
    
    # 🔒 STEP 1: Check Lockout Status BEFORE verifying the password
    lockout_time = user.get("lockout_until")
    current_attempts = user.get("login_attempts", 0)

    # Ensure lockout_time is timezone-aware for comparison (handles legacy naive dates)
    if lockout_time and lockout_time.tzinfo is None:
        lockout_time = lockout_time.replace(tzinfo=timezone.utc)
    
    if lockout_time and lockout_time > current_time:
        
        if current_attempts >= HARD_LOCK_ATTEMPTS:
            message = "Account is locked due to excessive failed attempts. Please contact support or reset password."
        else:
            remaining_time = lockout_time - current_time
            total_seconds = max(0, remaining_time.total_seconds())
            minutes = int(total_seconds // 60)
            seconds = int(total_seconds % 60)
            
            message = f"Account locked due to too many failed attempts. Try again in {minutes}m {seconds}s."
        
        log_action(
            request=request,
            audit_logs_collection=audit_logs,
            known_locations_collection=known_locations,
            username=user["username"],
            action="login",
            details={"status": "fail: locked out"},
            background_tasks=background_tasks
        )
        # Return 429 Too Many Requests
        return JSONResponse({"message": message}, status_code=429)

    # 🔒 STEP 2: Verify Password and Handle Success/Failure
    try:
        ph.verify(user["password"], password)
        
        # --- SUCCESSFUL LOGIN ---
        
        # Reset login attempts and lockout status
        users.update_one(
            {"_id": user["_id"]}, 
            {"$set": {"last_accessed": current_time, "login_attempts": 0, "lockout_until": None}}
        )
        
    except Exception:
        # --- FAILED LOGIN (Wrong password) ---
        
        # Increment the failed attempts counter atomically
        users.update_one(
            {"_id": user["_id"]},
            {"$inc": {"login_attempts": 1}}
        )
        
        # Re-fetch user data to get the new attempts count
        updated_user = users.find_one({"_id": user["_id"]})
        new_attempts = updated_user.get("login_attempts", 1) 
        
        log_action(
            request=request,
            audit_logs_collection=audit_logs,
            known_locations_collection=known_locations,
            username=user["username"],
            action="login",
            details={"status": f"fail: invalid password, attempt {new_attempts}"},
            background_tasks=background_tasks
        )

        # 🔒 C. Check if the new count triggers a lockout stage
        
        # ⭐ FIX: Only set lockout_duration_minutes if the new attempt count IS an exact stage threshold
        lockout_duration_minutes = LOCKOUT_STAGES.get(new_attempts, 0)

        # The old iterative logic is now safely removed/replaced:
        # lockout_duration_minutes = 0
        # for attempts, duration in sorted(LOCKOUT_STAGES.items()):
        #     if new_attempts >= attempts:
        #         lockout_duration_minutes = duration
        #     else:
        #         break 

        if lockout_duration_minutes > 0:
            
            lockout_time_db = updated_user.get("lockout_until")
            
            # This check resolves the TypeError and ensures timezone awareness
            if lockout_time_db and lockout_time_db.tzinfo is None:
                lockout_time_db = lockout_time_db.replace(tzinfo=timezone.utc)
            
            # The lock is applied ONLY if the current lock is expired (or missing)
            if lockout_time_db is None or lockout_time_db < current_time:
                
                # Lock the account for the calculated duration
                lockout_time = current_time + timedelta(minutes=lockout_duration_minutes)
                users.update_one(
                    {"_id": user["_id"]},
                    {"$set": {"lockout_until": lockout_time}}
                )

                # 📧 Send Lockout Email Notification (Only send if we are actively setting a new lock)
                if background_tasks is not None:
                    background_tasks.add_task(lockout_email, user, lockout_time)
                else:
                    try:
                        lockout_email(user, lockout_time)
                    except Exception:
                        logger.exception("Failed to send account lockout email")
                
                # Log the lockout event
                log_action(
                    request=request,
                    audit_logs_collection=audit_logs,
                    known_locations_collection=known_locations,
                    username=user["username"],
                    action="login",
                    details={"status": f"fail: lockout triggered (stage {lockout_duration_minutes}m)"},
                    background_tasks=background_tasks
                )
            
                # Return 401 with a specific message for the client (same message hides the stage info)
                return JSONResponse({"message": "Wrong password. Maximum login attempts reached."}, status_code=401)
            
            # If the account is locked but the lock time hasn't expired, 
            # the request would have been caught in STEP 1. 
            # If the lock expired but the new attempt is NOT a stage threshold (e.g., attempt 6), 
            # we skip this entire block and return the standard error below.

        # Standard wrong password response (attempts logged, but no lockout threshold hit yet)
        return JSONResponse({"message": "Wrong password"}, status_code=401)


    # 🔒 STEP 3: Handle Account Not Active (only runs on correct password)
    if user.get("is_active") != 1:
        # Increment attempts counter
        users.update_one(
            {"_id": user["_id"]},
            {"$inc": {"login_attempts": 1}}
        )
        
        log_action(
            request=request,
            audit_logs_collection=audit_logs,
            known_locations_collection=known_locations,
            username=user["username"],
            action="login",
            details={"status": "fail: account not active"},
            background_tasks=background_tasks
        )
        return JSONResponse({"message": "Account is not active"}, status_code=403)

    try:
        client_ip = get_client_ip(request)
        registered_ips = user.get("registered_ips") or []
        if client_ip and client_ip not in registered_ips:
            # Persist the new IP
            users.update_one({"_id": user["_id"]}, {"$push": {"registered_ips": client_ip}})

            # Resolve geo information (best-effort); mirror create_account approach
            try:
                geo = known_locations.find_one({"ip_address": client_ip})
            except Exception:
                geo = None

            if user.get("is_active") == 1:
                # Send email notification in background when possible
                if background_tasks is not None:
                    background_tasks.add_task(login_email, user, geo)
                else:
                    try:
                        login_email(user, geo)
                    except Exception:
                        logger.exception("Failed to send new-IP notification email")
    except Exception:
        logger.exception("Error checking/recording client IP for login")

    token_data = {"sub": user["username"], "role": user.get("role", "user")}
    token = create_access_token(token_data)

    # --- Determine where to redirect ---
    return_url = request.cookies.get("return_url") or "/pdf_list"

    response = JSONResponse(
        {
            "message": "Login successful",
            "return_url": return_url,
            "access_token": token,
            "token_type": "bearer",
        },
        status_code=200,
    )
    response.set_cookie(key="access_token", value=token, httponly=True)
    response.delete_cookie("return_url")  # clean up after reading


    log_action(
        request=request,
        audit_logs_collection=audit_logs,
        known_locations_collection=known_locations,
        username=user["username"],
        action="login",
        details={"status": "successful"},
        background_tasks=background_tasks
    )
    return response


# -----------------------------
# Update login attempts endpoint
# -----------------------------
@app.post("/update-login-attempts")
async def update_login_attempts(
    data: dict,
    current_user: dict = Depends(get_current_user_no_redirect)  # JWT-protected
):
    target_username = data.get("username")
    attempts = data.get("login_attempts")

    if not target_username or attempts is None:
        raise HTTPException(status_code=400, detail="Missing 'username' or 'login_attempts' in request")

    # Normalize username to lowercase for consistency
    users.update_one(
        {"username": target_username.lower()},
        {"$set": {"login_attempts": int(attempts)}}
    )

    return JSONResponse({"message": f"Updated login attempts for {target_username} to {attempts}"}, status_code=200)



# -----------------------------
# Create Account Page
# -----------------------------
def new_user_activation_email(user, geo):
    """
    Sends a formatted HTML email when a new user signs up.
    `user` is a dictionary with first_name, last_name, email, username, date_created, etc.
    """
    to_email = os.getenv("DEFAULT_EMAIL", "")
    subject = f"LOTO Generator - Actication: {user['username']}"

    # Convert UTC to Eastern Time
    utc_time = datetime.utcnow()
    eastern = pytz.timezone("US/Eastern")  # change this to your timezone if needed
    local_time = utc_time.replace(tzinfo=pytz.utc).astimezone(eastern)
    formatted_time = local_time.strftime("%B %d, %Y %I:%M %p %Z")

    # IP
    if geo is None:
        location_str = "unknown"
    else:
        city = geo["location"].get("city")
        region = geo["location"].get("region")
        country = geo["location"].get("country")

        # if all are missing, just say "unknown"
        if not any([city, region, country]):
            location_str = "unknown"
        else:
            # join non-empty values with commas
            location_str = ", ".join(filter(None, [city, region, country]))


    # Build the HTML content
    html_content = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: transparent;
                margin-right: 5%;
                margin-left: 5%;
                padding: 0;
            }}
            h2 {{
                color: #C32026;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
            }}
            th, td {{
                text-align: left;
                padding: 8px;
                border-bottom: 1px solid #dddddd;
            }}
            th {{
                background-color: #f0f0f0;
            }}
            .footer {{
                margin-top: 20px;
                font-size: 12px;
                color: #777777;
            }}
        </style>
    </head>
    <body>
        <h2>New User Account Created</h2>
        <p>A new user has signed up and may require activation:</p>
        <table>
            <tr><th>Field</th><th>Value</th></tr>
            <tr><td>First Name</td><td>{user.get('first_name', '')[:1].upper() + user.get('first_name', '')[1:] if user.get('first_name') else ''}</td></tr>
            <tr><td>Last Name</td><td>{user.get('last_name', '')[:1].upper() + user.get('last_name', '')[1:] if user.get('last_name') else ''}</td></tr>
            <tr><td>Username</td><td>{user.get('username', '')}</td></tr>
            <tr><td>Email</td><td>{user.get('email', '')}</td></tr>
            <tr><td>Date Created</td><td>{formatted_time}</td></tr>
            <tr><td>IP Address</td><td>{geo.get('ip_address', 'unknown') if geo else 'unknown'}</td></tr>
            <tr><td>Location</td><td>{location_str}</td></tr>
        </table>
        <p>If you wish to activate this account, please follow the link below:</p>
        <p>
          <a href="https://lotogenerator.app/users" 
             style="background-color:#C32026; color:#ffffff; text-decoration:none; padding:10px 20px; border-radius:5px; display:inline-block;">
             Login & Activate
          </a>
        </p>
        <p class="footer">This is an automated message from LOTO Report Generator. Do not reply.</p>
    </body>
    </html>
    """

    # Send email using your auto function
    send_email_auto(to_email, subject, html_content)

def new_user_welcome_email(user, geo):
    """
    Sends a formatted HTML email to a new user notifying them that their account
    is created and waiting for admin approval before they can access it.
    `user` is a dictionary with first_name, last_name, email, username, date_created, etc.
    """
    to_email = user.get('email', '')
    subject = f"LOTO Generator Account Created - Awaiting Approval"

    # Convert UTC to Eastern Time for date_created (or current time if missing)
    utc_time = user.get('date_created', datetime.utcnow())
    if isinstance(utc_time, str):
        utc_time = datetime.fromisoformat(utc_time)
    eastern = pytz.timezone("US/Eastern")
    local_time = utc_time.replace(tzinfo=pytz.utc).astimezone(eastern)
    formatted_time = local_time.strftime("%B %d, %Y %I:%M %p %Z")

    # Geo location string
    if geo is None:
        location_str = "unknown"
    else:
        city = geo["location"].get("city")
        region = geo["location"].get("region")
        country = geo["location"].get("country")
        location_str = ", ".join(filter(None, [city, region, country])) or "unknown"

    # Build the HTML content
    html_content = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: transparent;
                margin-right: 5%;
                margin-left: 5%;
                padding: 0;
            }}
            h2 {{
                color: #C32026;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
            }}
            th, td {{
                text-align: left;
                padding: 8px;
                border-bottom: 1px solid #dddddd;
            }}
            th {{
                background-color: #f0f0f0;
            }}
            .footer {{
                margin-top: 20px;
                font-size: 12px;
                color: #777777;
            }}
            .button {{
                background-color:#C32026; 
                color:#ffffff; 
                text-decoration:none; 
                padding:10px 20px; 
                border-radius:5px; 
                display:inline-block;
                font-weight: bold;
            }}
        </style>
    </head>
    <body>
        <h2>Welcome {user.get('first_name', '')[:1].upper() + user.get('first_name', '')[1:] if user.get('first_name') else ''}!</h2>
        <p>Your account has been successfully created and is now awaiting administrator approval before you can access it.</p>
        <p>Here are your account details:</p>
        <table>
            <tr><th>Field</th><th>Value</th></tr>
            <tr><td>First Name</td><td>{user.get('first_name', '')[:1].upper() + user.get('first_name', '')[1:] if user.get('first_name') else ''}</td></tr>
            <tr><td>Last Name</td><td>{user.get('last_name', '')[:1].upper() + user.get('last_name', '')[1:] if user.get('last_name') else ''}</td></tr>
            <tr><td>Username</td><td>{user.get('username', '')}</td></tr>
            <tr><td>Email</td><td>{user.get('email', '')}</td></tr>
            <tr><td>Date Created</td><td>{formatted_time}</td></tr>
            <tr><td>IP Address</td><td>{geo.get('ip_address', 'unknown') if geo else 'unknown'}</td></tr>
            <tr><td>Location</td><td>{location_str}</td></tr>
        </table>
        <p>Once your account is approved by the administrator, you will receive another notification with instructions on how to log in.</p>
        <p>
          <a href="https://lotogenerator.app" 
             style="background-color:#C32026; color:#ffffff; text-decoration:none; padding:10px 20px; border-radius:5px; display:inline-block;">
             Login
          </a>
        </p>
        <p class="footer">This is an automated message. Please do not reply to this email.</p>
    </body>
    </html>
    """

    # Use your email sending function here
    send_email_auto(to_email, subject, html_content)

# Function to generate the backup_code (6 random digits)
def generate_backup_code():
    # Generates a 10-digit numeric string
    return ''.join([str(secrets.randbelow(6)) for _ in range(6)])


@app.get("/create_account")
def create_account_form(
    request: Request,
    background_tasks: BackgroundTasks = None
):
    log_action(
        request=request,
        audit_logs_collection=audit_logs,
        known_locations_collection=known_locations,
        username="N/A",
        action="create-account page",
        details={},
        background_tasks=background_tasks
    )
    return templates.TemplateResponse("create_account.html", {"request": request})

@app.post("/create_account")
async def create_account(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    background_tasks: BackgroundTasks = None
):
    # Password confirmation
    if password != confirm_password:
        return templates.TemplateResponse("create_account.html", {"request": request, "error": "Passwords do not match"})

    username_lower = username.lower()

    # Check if username/email already exists (use lowercase for username)
    if users.find_one({"$or": [{"username": username_lower}, {"email": email}]}):
        log_action(
            request=request,
            audit_logs_collection=audit_logs,
        known_locations_collection=known_locations,
            username=username_lower,
            action="create-account",
            details={"status": "fail: account with email or username already exits"},
            background_tasks=background_tasks
        )
        return templates.TemplateResponse(
            "create_account.html",
            {"request": request, "error": "Username or email already exists"}
        )
    
    
    # Hash password
    hashed_password = ph.hash(password)

    # Capture client IP now and include it in the user document as a registered IP
    client_ip = get_client_ip(request)
    initial_ips = [client_ip] if client_ip else []

    # Insert user (persist initial registered IPs)
    users.insert_one({
        "first_name": first_name,
        "last_name": last_name,
        "email": email.lower(),
        "username": username_lower,  # store lowercase for login
        "display_username": username,  # optional: keep original for display
        "password": hashed_password,
        "date_created": datetime.utcnow(),
        "last_accessed": None,
        "is_active": 0,
        "role": "user",
        "backup_code": generate_backup_code(),
        "login_attempts": 0,
        "latest_reset": None,
        "password_resets": 0,
        "verification_attempts": 0,
        "registered_ips": initial_ips
    })

    # IP -> try to resolve geo info from DB or fallback to lookup helper
    geo = known_locations.find_one({"ip_address": client_ip}) if client_ip else None
    if not geo and client_ip:
        # lookup_ip_with_db may store/return geo info; use it as a fallback
        try:
            geo = await lookup_ip_with_db(client_ip, known_locations)
        except Exception:
            geo = None

    new_user_activation_email({
        "first_name": first_name,
        "last_name": last_name,
        "username": username_lower,
        "email": email,
        "date_created": datetime.utcnow()
    }, geo)

    new_user_welcome_email({
        "first_name": first_name,
        "last_name": last_name,
        "username": username_lower,
        "email": email,
        "date_created": datetime.utcnow()
    }, geo)

    log_action(
        request=request,
        audit_logs_collection=audit_logs,
        known_locations_collection=known_locations,
        username=username_lower,
        action="create-account",
        details={"status": "successful"},
        background_tasks=background_tasks
    )

    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)



# -----------------------------
# Email for account status change (activate/deactivate)
# -----------------------------
def status_change_email(user, performed_by, new_status):
    """
    Sends an email notifying the user their account status was updated.
    Includes who changed it and when.
    """
    to_email = user.get("email", "")
    subject = "LOTO Generator Account Status Updated"
    status_str = "Activated" if new_status else "Deactivated"

    # Convert UTC to Eastern Time for date_created (or current time if missing)
    utc_time = datetime.utcnow()
    if isinstance(utc_time, str):
        utc_time = datetime.fromisoformat(utc_time)
    eastern = pytz.timezone("US/Eastern")
    local_time = utc_time.replace(tzinfo=pytz.utc).astimezone(eastern)
    formatted_time = local_time.strftime("%B %d, %Y %I:%M %p %Z")

    html_content = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: transparent;
                margin-right: 5%;
                margin-left: 5%;
                padding: 0;
            }}
            h2 {{
                color: #C32026;
            }}
            .button {{
                background-color:#C32026; 
                color:#ffffff; 
                text-decoration:none; 
                padding:10px 20px; 
                border-radius:5px; 
                display:inline-block;
                font-weight: bold;
            }}
            .footer {{
                margin-top: 20px;
                font-size: 12px;
                color: #777777;
            }}
        </style>
    </head>
    <body>
        <h2>Account Status Updated</h2>
        <p>Hello {user.get('first_name','')},</p>
        <p>Your account status was updated to <strong>{status_str}</strong>.</p>
        <p><strong>Changed by:</strong> {performed_by}</p>
        <p><strong>Time:</strong> {formatted_time}</p>
        <p>If you did not request this change, please contact support immediately.</p>
        <p>
          <a href="https://lotogenerator.app" 
             style="background-color:#C32026; color:#ffffff; text-decoration:none; padding:10px 20px; border-radius:5px; display:inline-block;">
             Login
          </a>
        </p>
        <p class="footer">This is an automated message. Please do not reply.</p>
    </body>
    </html>
    """

    send_email_auto(to_email, subject, html_content)

# -----------------------------
# Endpoint: change_status
# -----------------------------
@app.post("/change_status")
async def change_status(
    request: Request,
    data: dict,
    current_user: dict = Depends(get_current_user_no_redirect),
    background_tasks: BackgroundTasks = None
):
    """
    Change a user's active status (activate or deactivate).
    Only owners users may use this endpoint.
    """
    # Ensure only owner can modify
    error = require_role("owner")(current_user)
    if error:
        return error

    target_username = data.get("username")
    new_status = data.get("is_active")

    # Validate fields
    if target_username is None or new_status is None:
        raise HTTPException(status_code=400, detail="Missing username or is_active")

    if not isinstance(new_status, (int, bool)):
        raise HTTPException(status_code=400, detail="is_active must be int or boolean")

    # Normalize to integer (Mongo stores as 0/1)
    new_status_int = int(bool(new_status))

    # Check if user exists
    user = users.find_one({"username": target_username})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update user's active flag
    users.update_one(
        {"username": target_username},
        {"$set": {"is_active": new_status_int}}
    )

    log_action(
        request=request,
        audit_logs_collection=audit_logs,
        known_locations_collection=known_locations,
        username=current_user["username"],
        action="change_status",
        details={"target": target_username, "is_active": new_status_int},
        background_tasks=background_tasks
    )

    # Send email notification in background
    background_tasks.add_task(status_change_email, user, current_user["username"], new_status_int)

    return {
        "message": f"User '{target_username}' status updated",
        "is_active": new_status_int
    }

# -----------------------------
# Email for role update
# -----------------------------
def role_update_email(user, performed_by, new_role):
    """
    Sends an email notifying the user their account role was updated.
    Includes who changed it and when.
    """
    to_email = user.get("email", "")
    subject = "LOTO Generator Account Role Updated"

    # Convert UTC to Eastern Time for date_created (or current time if missing)
    utc_time = datetime.utcnow()
    if isinstance(utc_time, str):
        utc_time = datetime.fromisoformat(utc_time)
    eastern = pytz.timezone("US/Eastern")
    local_time = utc_time.replace(tzinfo=pytz.utc).astimezone(eastern)
    formatted_time = local_time.strftime("%B %d, %Y %I:%M %p %Z")

    html_content = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: transparent;
                margin-right: 5%;
                margin-left: 5%;
                padding: 0;
            }}
            h2 {{
                color: #C32026;
            }}
            .footer {{
                margin-top: 20px;
                font-size: 12px;
                color: #777777;
            }}
            .button {{
                background-color:#C32026; 
                color:#ffffff; 
                text-decoration:none; 
                padding:10px 20px; 
                border-radius:5px; 
                display:inline-block;
                font-weight: bold;
            }}
        </style>
    </head>
    <body>
        <h2>Account Role Updated</h2>
        <p>Hello {user.get('first_name','')},</p>
        <p>Your account role has been updated to <strong>{new_role}</strong>.</p>
        <p><strong>Changed by:</strong> {performed_by}</p>
        <p><strong>Time:</strong> {formatted_time}</p>
        <p>If you did not request this change, please contact support immediately.</p>
        <p>
          <a href="https://lotogenerator.app" 
             style="background-color:#C32026; color:#ffffff; text-decoration:none; padding:10px 20px; border-radius:5px; display:inline-block;">
             Login
          </a>
        </p>
        <p class="footer">This is an automated message. Please do not reply.</p>
    </body>
    </html>
    """

    send_email_auto(to_email, subject, html_content)

# -----------------------------
# Endpoint: update_role
# -----------------------------
@app.post("/update_role")
async def update_role(
    request: Request,
    data: dict,
    current_user: dict = Depends(get_current_user_no_redirect),
    background_tasks: BackgroundTasks = None
):
    error = require_role("owner")(current_user)
    if error:
        return error

    target_username = data.get("username")
    new_role = data.get("role")

    if new_role == "owner":
        raise HTTPException(status_code=403, detail="Cannot assign owner role")
    if new_role not in ["admin", "user"]:
        raise HTTPException(status_code=400, detail="Invalid role value")

    user = users.find_one({"username": target_username})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    users.update_one({"username": target_username}, {"$set": {"role": new_role}})

    log_action(
        request=request,
        audit_logs_collection=audit_logs,
        known_locations_collection=known_locations,
        username=current_user["username"],
        action="update_role",
        details={"target": target_username, "new_role": new_role},
        background_tasks=background_tasks
    )

    # Send email notification in background
    background_tasks.add_task(role_update_email, user, current_user["username"], new_role)

    return {"message": f"Updated role for {target_username} to {new_role}"}

# -----------------------------
# Email for deleted user
# -----------------------------
def user_deleted_email(user, performed_by):
    """
    Sends an email notifying the user their account was deleted.
    Includes who deleted it and when.
    """
    to_email = user.get("email", "")
    subject = "LOTO Generator Account Deleted"

    # Convert UTC to Eastern Time for date_created (or current time if missing)
    utc_time = datetime.utcnow()
    if isinstance(utc_time, str):
        utc_time = datetime.fromisoformat(utc_time)
    eastern = pytz.timezone("US/Eastern")
    local_time = utc_time.replace(tzinfo=pytz.utc).astimezone(eastern)
    formatted_time = local_time.strftime("%B %d, %Y %I:%M %p %Z")

    html_content = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: transparent;
                margin-right: 5%;
                margin-left: 5%;
                padding: 0;
            }}
            h2 {{
                color: #C32026;
            }}
            .footer {{
                margin-top: 20px;
                font-size: 12px;
                color: #777777;
            }}
        </style>
    </head>
    <body>
        <h2>Account Deleted</h2>
        <p>Hello {user.get('first_name','')},</p>
        <p>Your account has been <strong>deleted</strong>.</p>
        <p><strong>Deleted by:</strong> {performed_by}</p>
        <p><strong>Time:</strong> {formatted_time}</p>
        <p>If you believe this was done in error, please contact support immediately.</p>
        <p>
          <a href="mailto:support@lotogenerator.app" 
             style="background-color:#C32026; color:#ffffff; text-decoration:none; padding:10px 20px; border-radius:5px; display:inline-block;">
             Contact Support
          </a>
        </p>
        <p class="footer">This is an automated message. Please do not reply.</p>
    </body>
    </html>
    """

    send_email_auto(to_email, subject, html_content)

# -----------------------------
# Endpoint: delete_user
# -----------------------------
@app.post("/delete_user")
async def delete_user(
    request: Request,
    data: dict, 
    current_user: dict = Depends(get_current_user_no_redirect),
    background_tasks: BackgroundTasks = None
):
    # Only owner can delete users
    error = require_role("owner")(current_user)
    if error:
        log_action(
            request=request,
            audit_logs_collection=audit_logs,
            known_locations_collection=known_locations,
            username=current_user["username"],
            action="delete_user",
            details={"target": target_username, "deleted": False, "status": "insufficient permissions"},
            background_tasks=background_tasks
        )
        return error

    target_username = data.get("username")
    if not target_username:
        raise HTTPException(status_code=400, detail="Missing 'username' in request")

    target_user = users.find_one({"username": target_username.lower()})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    if target_user.get("role") == "owner":
        raise HTTPException(status_code=403, detail="Cannot delete owner")

    users.delete_one({"username": target_username.lower()})

    log_action(
        request=request,
        audit_logs_collection=audit_logs,
        known_locations_collection=known_locations,
        username=current_user["username"],
        action="delete_user",
        details={"target": target_username, "deleted": True},
        background_tasks=background_tasks
    )

    # Send email notification in background
    background_tasks.add_task(user_deleted_email, target_user, current_user["username"])

    return JSONResponse({"message": f"Deleted user {target_username}"}, status_code=200)

# -----------------------------
# Audit Logs Page (Owner Only)
# -----------------------------
@app.get("/audit_logs", response_class=HTMLResponse)
async def audit_logs_page(
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    if isinstance(current_user, RedirectResponse):
        return current_user

    # Require owner access
    error = require_role("owner")(current_user)
    if error:
        log_action(
            request=request,
            audit_logs_collection=audit_logs,
            known_locations_collection=known_locations,
            username=current_user["username"],
            action="audit_logs page",
            details={"status": "insufficient permissions"},
            background_tasks=background_tasks
        )
        return error
    
    return templates.TemplateResponse("audit_logs.html", {
        "request": request,
        "current_user": current_user
    })

@app.get("/audit_logs_json")
async def audit_logs_json(
    current_user: dict = Depends(get_current_user_no_redirect),
    limit: int = Query(500, ge=1, le=2500)
):
    # Require owner access
    error = require_role("owner")(current_user)
    if error:
        return error

    # Respect client-requested limit (default 500, capped at 2500)
    logs_cursor = audit_logs.find({}, {"_id": 0}).sort("timestamp", -1).limit(limit)
    log_list = []

    for doc in logs_cursor:
        # Convert datetime to ISO string
        if isinstance(doc.get("timestamp"), datetime):
            doc["timestamp"] = doc["timestamp"].isoformat() + "Z"
        log_list.append(doc)

    return {"logs": log_list}

# -----------------------------
# Public API for website status
# -----------------------------
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint for monitoring and badges.
    Returns a simple 200 OK response.
    """
    return JSONResponse(content={"status": "ok"}, status_code=200)

@app.get("/check-username-email")
async def check_username_email(
    username: str = Query(None),
    email: str = Query(None)
):
    if username:
        field = "username"
        value = username.lower()  # ensure lowercase for querying username
    elif email:
        field = "email"
        value = email.lower()  # fix here to use email.lower()
    else:
        return JSONResponse({"exists": False})

    exists = users.find_one({field: value}) is not None
    return JSONResponse({"exists": exists})


@app.get("/forgot_password")
def forgot_password_form(
    request: Request,
    background_tasks: BackgroundTasks = None
):
    log_action(
        request=request,
        audit_logs_collection=audit_logs,
        known_locations_collection=known_locations,
        username="N/A",
        action="forgot_password page",
        details={},
        background_tasks=background_tasks
    )
    return templates.TemplateResponse("forgot_password.html", {"request": request})


@app.post("/send_backup_code")
async def send_backup_code(
    request: Request,
    data: dict,
    background_tasks: BackgroundTasks = None
):
    """
    Send the backup code to a user's email.
    No authentication required.
    """
    target_email = data.get("email")
    if not target_email:
        raise HTTPException(status_code=400, detail="Missing email")

    # Normalize email
    target_email = target_email.strip().lower()

    # Look up user in DB
    user = users.find_one({"email": target_email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Regenerate a fresh backup code for every send so codes are never repeated
    new_code = generate_backup_code()
    try:
        users.update_one({"email": target_email}, {"$set": {"backup_code": new_code}})
    except Exception:
        logger.exception("Failed to persist new backup code for send_backup_code")

    backup_code = new_code

    # Email template
    html_body = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: transparent;
                margin-right: 5%;
                margin-left: 5%;
                padding: 0;
            }}
            h2 {{
                color: #C32026;
            }}
            .footer {{
                margin-top: 20px;
                font-size: 12px;
                color: #777777;
            }}
        </style>
    </head>
    <body>
        <h2>Your Backup Code</h2>
        <p>Hello,</p>
        <p>Here is your backup code:</p>
        <div style="
            font-size: 26px;
            font-weight: bold;
            padding: 12px 20px;
            background: #f1f1f1;
            border-radius: 6px;
            display: inline-block;
            letter-spacing: 2px;
            margin: 15px 0;
        ">
            {backup_code}
        </div>

        <p class="footer">This is an automated message. Please do not reply to this email.</p>
    </body>
    </html>
    """

    # Send email in background
    background_tasks.add_task(
        send_email_auto,
        to_email=target_email,
        subject="LOTO Generator Backup Code",
        body=html_body
    )

    # Log action (no current_user available → mark as "public")
    log_action(
        request=request,
        audit_logs_collection=audit_logs,
        known_locations_collection=known_locations,
        username=target_email,
        action="send_backup_code",
        details={"target_email": target_email},
        background_tasks=background_tasks
    )

    return {"message": f"Backup code sent to {target_email}", "code": f"{backup_code}"}

@app.post("/verify_backup_code")
async def verify_backup_code(
    request: Request,
    data: dict,
    background_tasks: BackgroundTasks = None
):
    """
    Verify a user's backup code.
    No authentication required.
    """
    email = data.get("email")
    code = data.get("code")

    if not email or not code:
        raise HTTPException(status_code=400, detail="Missing email or code")

    email = email.strip().lower()
    code = code.strip()

    # Look up user
    user = users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    backup_code = user.get("backup_code")
    if not backup_code:
        raise HTTPException(status_code=400, detail="No backup code stored for this user")

    # Compare codes
    if backup_code != code:
        raise HTTPException(status_code=400, detail="Invalid backup code")

    # Generate a new backup code
    new_backup_code = generate_backup_code()

    # Update the user document with the new code
    users.update_one(
        {"email": email},
        {"$set": {"backup_code": new_backup_code}}
    )

    # Log action
    log_action(
        request=request,
        audit_logs_collection=audit_logs,
        known_locations_collection=known_locations,
        username=email,
        action="verify_backup_code",
        details={"status": "successful validation", "new_code_generated": True},
        background_tasks=background_tasks
    )

    return {
        "message": "Backup code verified successfully. A new backup code has been generated.",
        "new_backup_code": new_backup_code  # optionally return for testing
    }

# -----------------------------
# Update verification attempts endpoint
# -----------------------------
@app.post("/update-verification-attempts")
async def update_verification_attempts(
    data: dict,
):
    target_email = data.get("email")
    attempts = data.get("verification_attempts")

    if not target_email or attempts is None:
        raise HTTPException(status_code=400, detail="Missing 'email' or 'login_attempts' in request")

    # Normalize username to lowercase for consistency
    users.update_one(
        {"email": target_email.lower()},
        {"$set": {"verification_attempts": int(attempts)}}
    )

    return JSONResponse({"message": f"Updated login attempts for {target_email} to {attempts}"}, status_code=200)

# -----------------------------
# Password reset email
# -----------------------------
def password_reset_email(user):
    """
    Sends an HTML email notifying the user their password was reset.
    `user` is a dict with at least 'email' and optionally 'first_name'.
    """
    to_email = user.get("email", "")
    subject = "LOTO Generator Password Reset Notification"

    # Current time in Eastern Time
    utc_now = datetime.utcnow()
    eastern = pytz.timezone("US/Eastern")
    local_time = utc_now.replace(tzinfo=pytz.utc).astimezone(eastern)
    formatted_time = local_time.strftime("%B %d, %Y %I:%M %p %Z")

    html_content = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: transparent;
                margin: 5%;
                padding: 0;
            }}
            h2 {{
                color: #C32026;
            }}
            .footer {{
                margin-top: 20px;
                font-size: 12px;
                color: #777777;
            }}
            .button {{
                background-color:#C32026; 
                color:#ffffff; 
                text-decoration:none; 
                padding:10px 20px; 
                border-radius:5px; 
                display:inline-block;
                font-weight: bold;
            }}
        </style>
    </head>
    <body>
        <h2>Password Reset Notification</h2>
        <p>Hello {user.get('first_name', '')},</p>
        <p>Your password was successfully reset on {formatted_time}.</p>
        <p>If you did not perform this action, please contact support immediately.</p>
        <p>For security, do not share your password and keep your account private.</p>
        <p>You can log in here:</p>
        <p><a href="https://lotogenerator.app/login" class="button">Log In to LOTO Generator</a></p>
        <p class="footer">This is an automated message. Please do not reply to this email.</p>
    </body>
    </html>
    """

    # Use your existing email function
    send_email_auto(to_email, subject, html_content)


# -----------------------------
# Reset password endpoint
# -----------------------------
@app.post("/reset_password")
async def reset_password(data: dict, background_tasks: BackgroundTasks):
    target_email = data.get("email")
    new_password = data.get("new_password")

    if not target_email or new_password is None:
        raise HTTPException(status_code=400, detail="Missing 'email' or 'new_password' in request")
    
    # Hash password
    hashed_password = ph.hash(new_password)
    target_email_normalized = target_email.lower()

    # Get a current UTC-aware time for the update
    current_time_utc = datetime.now(timezone.utc)
    
    # Update password, latest_reset, increment password_resets, AND CLEAR LOCKOUT STATUS
    result = users.update_one(
        {"email": target_email_normalized},
        {
            "$set": {
                "password": hashed_password, 
                "latest_reset": current_time_utc,
                "lockout_until": None,
                "login_attempts": 0
            },
            "$inc": {"password_resets": 1}
        }
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=401, detail="User not found")

    # Fetch user document to include in email
    user = users.find_one({"email": target_email_normalized})

    # Send password reset email in the background
    background_tasks.add_task(password_reset_email, user)

    return JSONResponse({"message": f"Reset password for {target_email_normalized}"}, status_code=200)

@app.post("/logout")
def logout(response: Response):
    # Clear the access_token cookie
    response.delete_cookie(key="access_token", path="/")
    return {"message": "Logged out"}

@app.get("/map")
def map_page(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    if isinstance(current_user, RedirectResponse):
        return current_user
    
    # Require owner access
    error = require_role("admin")(current_user)
    if error:
        return error
    
    return templates.TemplateResponse("map.html", {
        "request": request,
        "current_user": current_user
    })

COLORS = ["#FF6666", "#66FF66", "#6666FF", "#FFFF66"]

def greedy_color(adjacency):
    colors = {}
    for name in adjacency:
        used = set(colors.get(n) for n in adjacency[name] if n in colors)
        colors[name] = next((c for c in COLORS if c not in used), COLORS[0])
    return colors

def build_adjacency(features, name_key="name"):
    adjacency = {}
    # Build bounding boxes for all features
    bboxes = {f['properties'][name_key]: box(*shape(f['geometry']).bounds) for f in features}

    for name_a, bbox_a in bboxes.items():
        adjacency[name_a] = []
        for name_b, bbox_b in bboxes.items():
            if name_a == name_b:
                continue
            if bbox_a.intersects(bbox_b):
                adjacency[name_a].append(name_b)
    return adjacency

@app.get("/locations_summary")
async def locations_summary(current_user: dict = Depends(get_current_user)):
    # --- Get visited countries and states from DB ---
    docs = list(known_locations.find({}))
    visited_countries = set()
    visited_states = set()

    # Count unique IPs
    country_ips = defaultdict(set)
    state_ips = defaultdict(set)

    for doc in docs:
        loc = doc.get("location") or {}
        country = loc.get("country")
        state = loc.get("region")
        ip = doc.get("ip_address")
        if country:
            visited_countries.add(country)
            if ip:
                country_ips[country].add(ip)
        if state:
            visited_states.add(state)
            if ip:
                state_ips[state].add(ip)

    # --- Load GeoJSON ---
    with open(DEPENDENCY_DIR / "countries.geojson") as f:
        countries_geo = json.load(f)
    with open(DEPENDENCY_DIR / "states.json") as f:
        states_geo = json.load(f)

    # --- Build adjacency & assign colors ---
    countries_adj = build_adjacency(countries_geo['features'], name_key="name")
    countries_colors = greedy_color(countries_adj)

    states_adj = build_adjacency(states_geo['features'], name_key="NAME")
    states_colors = greedy_color(states_adj)

    # Only include visited places
    visited_countries_colors = {c: countries_colors[c] for c in visited_countries if c in countries_colors}
    visited_states_colors = {s: states_colors[s] for s in visited_states if s in states_colors}

    # Convert IP sets to counts
    country_counts = {c: len(country_ips[c]) for c in visited_countries}
    state_counts = {s: len(state_ips[s]) for s in visited_states}

    # --- Compute geographic centers for visited states ---
    state_centers = {}
    for s in visited_states:
        center_data = combined_largest_centers_and_plot(
            region_name=s,
            geojson_file=DEPENDENCY_DIR / "states.json",
            name_property="NAME",
            do_print=False,
            do_plot=False
        )
        if center_data and center_data.get("average"):
            avg_lon, avg_lat = center_data["average"]
            state_centers[s] = [avg_lat, avg_lon]  # Leaflet expects [lat, lon]

    # --- Compute geographic centers for visited countries ---
    country_centers = {}
    for c in visited_countries:
        center_data = combined_largest_centers_and_plot(
            region_name=c,
            geojson_file=DEPENDENCY_DIR / "countries.geojson",
            name_property="name",
            do_print=False,
            do_plot=False
        )
        if center_data and center_data.get("average"):
            avg_lon, avg_lat = center_data["average"]
            country_centers[c] = [avg_lat, avg_lon]

    return {
        "countries": list(visited_countries),
        "us_states": list(visited_states),
        "countries_colors": visited_countries_colors,
        "states_colors": visited_states_colors,
        "countries_counts": country_counts,
        "states_counts": state_counts,
        "states_centers": state_centers,
        "countries_centers": country_centers
    }
