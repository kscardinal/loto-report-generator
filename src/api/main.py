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

from .logging_config import logger, log_requests_json
from .auth_utils import create_access_token, get_current_user, get_current_user_no_redirect, require_role, log_action, get_client_ip, lookup_ip_with_db

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
                "uploaded_by": uploaded_by,
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
            "uploaded_by": uploaded_by,
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
# Download PDF (streams PDF directly to client)
# -----------------------------
@app.get("/download_pdf/{report_name}", name="download_pdf")
def download_pdf(
    request: Request,
    report_name: str,
    username: str = Depends(get_current_user_no_redirect),
    background_tasks: BackgroundTasks = None
):
    print(f"DEBUG: Processing download for {report_name}")
    doc = uploads.find_one({"report_name": report_name})
    if not doc:
        return JSONResponse(status_code=404, content={"error": f"Report '{report_name}' not found"})

    try:
        TEMP_DIR.mkdir(exist_ok=True)  # ensure the mounted folder exists

        json_file_path = TEMP_DIR / f"{report_name}.json"
        with open(json_file_path, "w", encoding="utf-8") as f:
            json.dump(doc["json_data"], f, ensure_ascii=False, indent=2)

        # Write all photos to TEMP_DIR
        for photo in doc["photos"]:
            photo_file_path = TEMP_DIR / photo["photo_name"]
            with open(photo_file_path, "wb") as f:
                f.write(fs.get(photo["photo_id"]).read())

        pdf_file_path = TEMP_DIR / f"{report_name}.pdf"
        subprocess.run(
            ["python", str(PROCESS_DIR / "generate_pdf.py"), str(json_file_path)],
            check=True
        )

        pdf_bytes = pdf_file_path.read_bytes()

        # Clear TEMP_DIR
        for item in TEMP_DIR.iterdir():
            if item.is_file():
                item.unlink()        # delete files
            elif item.is_dir():
                shutil.rmtree(item)  # delete subfolders

        log_action(
            request=request,
            audit_logs_collection=audit_logs,
            known_locations_collection=known_locations,
            username=username["username"],
            action="download_pdf",
            details={"report": report_name, "status": "Successful"},
            background_tasks=background_tasks
        )

        return StreamingResponse(
            BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={report_name}.pdf"}
        )

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
    docs = uploads.find({}, {"_id": 0, "report_name": 1}).sort("report_name", 1)
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

    # Format datetime fields
    for key in ["date_added", "last_modified", "last_generated"]:
        if key in doc and isinstance(doc[key], datetime):
            doc[key] = format_datetime_with_ordinal(doc[key], tz_offset)

    log_action(
        request=request,
        audit_logs_collection=audit_logs,
        known_locations_collection=known_locations,
        username=username["username"],
        action="view_report",
        details={"report": report_name},
        background_tasks=background_tasks
    )

    return templates.TemplateResponse("view_report.html", {"request": request, "report": doc})

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
            doc[key] = doc[key].strftime("%A, %B %d, %Y, %I:%M:%S %p")

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

    return templates.TemplateResponse("input_form.html", {"request": request})

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
    total_bytes = 0
    for grid_out in fs.find():
        photo_id = grid_out._id
        photo_name = grid_out.filename
        usage_count = uploads.count_documents({"photos.photo_id": photo_id})
        if usage_count == 0:
            fs.delete(photo_id)
            deleted_photos[str(photo_id)] = photo_name
            total_bytes += grid_out.length  # Get file size in bytes

    details = {}
    if not deleted_photos:
        details["status"] = "No orphaned photos to remove"
    else:
        count = len(deleted_photos)
        size = sizeof_fmt(total_bytes)
        photo_word = "photo" if count == 1 else "photos"
        details["status"] = f"{count} {photo_word} removed ({size} total)"
        for pid, name in deleted_photos.items():
            details[pid] = name

    log_action(
        request=request,
        audit_logs_collection=audit_logs,
        known_locations_collection=known_locations,
        username=username["username"],
        action="clean_orphan_photos",
        details=details,
        background_tasks=background_tasks
    )

    return {
        "message": f"Cleanup complete. {len(deleted_photos)} orphaned photos deleted.",
        "deleted": deleted_photos
    }

# -----------------------------
# JSON endpoints
# -----------------------------
@app.get("/pdf_list_json")
async def pdf_list_json(
    username: str = Depends(get_current_user_no_redirect)
):
    docs = uploads.find({}, {"_id": 0, "json_data": 0, "photos": 0})
    report_list = []
    for doc in docs:
        photo_count = len(doc.get("photos", [])) if "photos" in doc else 0
        for key in ["date_added", "last_modified", "last_generated"]:
            if key in doc and isinstance(doc[key], datetime):
                doc[key] = doc[key].isoformat()
        doc["num_photos"] = photo_count
        report_list.append(doc)

    return {"reports": report_list}

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
                doc[key] = value.isoformat() + "Z"  # send as UTC ISO string
        user_list.append(doc)

    return {"users": user_list}


# -----------------------------
# Login Page
# -----------------------------
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

@app.post("/login")
async def login_endpoint(
    request: Request, 
    data: dict,
    background_tasks: BackgroundTasks = None
):
    username_or_email = data.get("username_or_email")
    password = data.get("password")
    username_or_email_lower = username_or_email.lower()

    user = users.find_one({
        "$or": [
            {"username": username_or_email_lower},
            {"email": username_or_email}
        ]
    })

    if not user:
        log_action(
            request=request,
            audit_logs_collection=audit_logs,
            known_locations_collection=known_locations,
            username=username_or_email_lower,
            action="login",
            details={"status": f"fail: no user matching {username_or_email_lower}"},
            background_tasks=background_tasks
        )
        return JSONResponse({"message": "User not found"}, status_code=404)

    try:
        ph.verify(user["password"], password)
    except Exception:
        log_action(
            request=request,
            audit_logs_collection=audit_logs,
            known_locations_collection=known_locations,
            username=username_or_email_lower,
            action="login",
            details={"status": "fail: invlaid password"},
            background_tasks=background_tasks
        )
        return JSONResponse({"message": "Wrong password"}, status_code=401)

    if user.get("is_active") != 1:
        log_action(
            request=request,
            audit_logs_collection=audit_logs,
            known_locations_collection=known_locations,
            username=username_or_email_lower,
            action="login",
            details={"status": "fail: account not active"},
            background_tasks=background_tasks
        )
        return JSONResponse({"message": "Account is not active"}, status_code=403)

    users.update_one({"_id": user["_id"]}, {"$set": {"last_accessed": datetime.utcnow()}})

    token_data = {"sub": user["username"], "role": user.get("role", "user")}
    token = create_access_token(token_data)

    # --- Determine where to redirect ---
    return_url = request.cookies.get("return_url") or "/pdf_list"

    response = JSONResponse({"message": "Login successful", "return_url": return_url}, status_code=200)
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
        <p>In the meantime, you can visit our site:</p>
        <p><a href="https://lotogenerator.app/users" class="button">Visit LOTO Generator</a></p>
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

    # Insert user
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
        "verification_attempts": 0
    })

    # IP
    client_ip = get_client_ip(request)
    geo = known_locations.find_one({"ip_address": client_ip})
    if geo:
        geo = geo
    else:
        # Optional: fallback to API if not found
        geo = await lookup_ip_with_db(client_ip, known_locations)

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

    return {
        "message": f"User '{target_username}' status updated",
        "is_active": new_status_int
    }


@app.post("/update_role")
async def update_role(
    request: Request,
    data: dict,
    current_user: dict = Depends(get_current_user_no_redirect),
    background_tasks: BackgroundTasks = None
):
    # Only owner can update roles
    error = require_role("owner")(current_user)
    if error:
        return error

    target_username = data.get("username")
    new_role = data.get("role")

    if new_role == "owner":
        raise HTTPException(status_code=403, detail="Cannot assign owner role")

    if new_role not in ["admin", "user"]:
        raise HTTPException(status_code=400, detail="Invalid role value")

    users.update_one(
        {"username": target_username},
        {"$set": {"role": new_role}}
    )

    log_action(
        request=request,
        audit_logs_collection=audit_logs,
        known_locations_collection=known_locations,
        username=current_user["username"],
        action="update_role",
        details={"target": target_username, "new_role": new_role},
        background_tasks=background_tasks
    )

    return {"message": f"Updated role for {target_username} to {new_role}"}

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

    # Prevent deleting owner
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
async def audit_logs_json(current_user: dict = Depends(get_current_user_no_redirect)):
    # Require owner access
    error = require_role("owner")(current_user)
    if error:
        return error

    logs_cursor = audit_logs.find({}, {"_id": 0}).sort("timestamp", -1).limit(500)
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

    backup_code = user.get("backup_code")
    if not backup_code:
        raise HTTPException(status_code=400, detail="User has no backup code stored")

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
# Reset password endpoint
# -----------------------------
@app.post("/reset_password")
async def reset_password(
    data: dict,
):
    target_email = data.get("email")
    new_password = data.get("new_password")

    if not target_email or new_password is None:
        raise HTTPException(status_code=400, detail="Missing 'email' or 'new_password' in request")
    
    # Hash password
    hashed_password = ph.hash(new_password)

    # Update password, latest_reset, and increment password_resets
    result = users.update_one(
        {"email": target_email.lower()},
        {
            "$set": {"password": hashed_password, "latest_reset": datetime.utcnow()},
            "$inc": {"password_resets": 1}
        }
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    return JSONResponse({"message": f"Reset password for {target_email}"}, status_code=200)

