import json
import subprocess
import sys
import tempfile
from datetime import datetime
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

from .logging_config import logger, log_requests_json
from .auth_utils import create_access_token, get_current_user

import gridfs
from bson.objectid import ObjectId
from fastapi import FastAPI, UploadFile, File, Form, Request, Response, Depends, HTTPException, status
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
fs = gridfs.GridFS(db)     # GridFS for storing photos

# JWT
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY not set in .env")

# Hashing Passwords
ph = PasswordHasher(time_cost=4, memory_cost=102400, parallelism=8, hash_len=32)


# -----------------------------
# Upload JSON + images
# -----------------------------
@app.post("/upload/")
async def upload_report(
    request: Request,
    username: str = Depends(get_current_user),
    files: List[UploadFile] = File(...),
    uploaded_by: str = Form("anonymous"),
    tags: List[str] = Form([]),
    notes: str = Form("")
):
    if isinstance(username, RedirectResponse):
        return username
    
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
def download_pdf(
    report_name: str,
    username: str = Depends(get_current_user)
):
    if isinstance(username, RedirectResponse):
        return username
    
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

        print(f"DEBUG: Returning StreamingResponse")
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
async def clear_temp_folders(username: str = Depends(get_current_user)):
    if isinstance(username, RedirectResponse):
        return username

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
    username: str = Depends(get_current_user)  # ✅ requires JWT
):
    """
    Render HTML listing of all reports in the DB.
    Works for both web (cookies) and mobile (Authorization header).
    """
    # If the dependency returned a RedirectResponse (for web), return it
    if isinstance(username, RedirectResponse):
        return username

    # Fetch report names
    docs = uploads.find({}, {"_id": 0, "report_name": 1}).sort("report_name", 1)
    report_names = [doc.get("report_name") for doc in docs if doc.get("report_name")]

    return templates.TemplateResponse(
        "pdf_list.html",
        {"request": request, "report_names": report_names}
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

def format_datetime_with_ordinal(dt: datetime) -> str:
    """Format datetime with full weekday, month, day with ordinal, year, and 12-hour time"""
    day_with_suffix = ordinal(dt.day)
    # %I is hour (12-hour), %M minutes, %S seconds, %p AM/PM
    return dt.strftime(f"%A, %B {day_with_suffix}, %Y at %I:%M:%S %p").lstrip("0").replace("AM","am").replace("PM","pm")

# -----------------------------
# View single report (HTML)
# -----------------------------
@app.get("/view_report/{report_name}", response_class=HTMLResponse)
async def view_report(
    request: Request,
    report_name: str,
    username: str = Depends(get_current_user)
):
    if isinstance(username, RedirectResponse):
        return username

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
def get_photo(photo_id: str, username: str = Depends(get_current_user)):
    if isinstance(username, RedirectResponse):
        return username

    photo = fs.get(ObjectId(photo_id))
    return Response(photo.read(), media_type="image/jpeg")

# -----------------------------
# Fetch metadata for a given report
# -----------------------------
@app.get("/metadata/{report_name}")
async def get_metadata(report_name: str, username: str = Depends(get_current_user)):
    if isinstance(username, RedirectResponse):
        return username

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
async def create_report(request: Request, username: str = Depends(get_current_user)):
    if isinstance(username, RedirectResponse):
        return username

    return templates.TemplateResponse("input_form.html", {"request": request})

# -----------------------------
# Remove a report from the database
# -----------------------------
@app.api_route("/remove_report/{report_name}", methods=["GET", "POST"])
async def remove_report(report_name: str, username: str = Depends(get_current_user)):
    if isinstance(username, RedirectResponse):
        return username

    doc = uploads.find_one({"report_name": report_name})
    if not doc:
        return JSONResponse(status_code=404, content={"error": f"Report '{report_name}' not found"})

    photo_names = [p["photo_name"] for p in doc.get("photos", [])]
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
async def cleanup_orphan_photos(username: str = Depends(get_current_user)):
    if isinstance(username, RedirectResponse):
        return username

    deleted_photos = {}
    for grid_out in fs.find():
        photo_id = grid_out._id
        photo_name = grid_out.filename
        usage_count = uploads.count_documents({"photos.photo_id": photo_id})
        if usage_count == 0:
            fs.delete(photo_id)
            deleted_photos[photo_name] = str(photo_id)

    return {
        "message": f"Cleanup complete. {len(deleted_photos)} orphaned photos deleted.",
        "deleted": deleted_photos
    }

# -----------------------------
# JSON endpoints
# -----------------------------
@app.get("/pdf_list_json")
async def pdf_list_json(username: str = Depends(get_current_user)):
    if isinstance(username, RedirectResponse):
        return username

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
def download_report_files(report_name: str, username: str = Depends(get_current_user)):
    if isinstance(username, RedirectResponse):
        return username

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
def download_json(report_name: str, username: str = Depends(get_current_user)):
    if isinstance(username, RedirectResponse):
        return username

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
def download_photo(photo_id: str, username: str = Depends(get_current_user)):
    if isinstance(username, RedirectResponse):
        return username

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
async def jwt_test(request: Request, username: str = Depends(get_current_user)):
    """
    A test endpoint to verify JWT authentication.
    Works for both web and mobile clients.
    """
    if isinstance(username, RedirectResponse):
        return username  # redirect for web if not authenticated

    # If mobile or logged in web user
    return JSONResponse({"message": f"JWT verified successfully! Welcome {username}"})










@app.get("/users_json")
async def users_json(username: str = Depends(get_current_user)):
    """
    Returns all users in the database as JSON.
    Works for both web (cookies) and mobile (Authorization header).
    """
    # Redirect web users if not authenticated
    #if isinstance(username, RedirectResponse):
    #    return username

    # Fetch all users, exclude Mongo _id
    users_cursor = users.find({}, {"_id": 0})
    user_list = []

    for doc in users_cursor:
        # Convert any datetime fields to ISO strings
        for key, value in doc.items():
            if isinstance(value, datetime):
                doc[key] = value.isoformat()
        user_list.append(doc)

    return {"users": user_list}


# -----------------------------
# Login Page
# -----------------------------
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@app.post("/login", response_class=HTMLResponse)
async def login_action(request: Request, username: str = Form(...), password: str = Form(...)):
    # Find user by username OR email
    user = users.find_one({"$or": [{"username": username}, {"email": username}]})
    
    if not user:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid username or email"}
        )

    # Verify password
    try:
        ph.verify(user["password"], password)
    except (VerifyMismatchError, VerificationError):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Incorrect password"}
        )

    # Create JWT token and set as cookie
    token = create_access_token({"sub": user["username"]})
    response = RedirectResponse(url="/pdf_list", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="access_token", value=token, httponly=True)
    return response


# -----------------------------
# Create Account Page
# -----------------------------
@app.get("/create-account")
def create_account_form(request: Request):
    return templates.TemplateResponse("create_account.html", {"request": request})

@app.post("/create-account")
def create_account(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...)
):
    # Password confirmation
    if password != confirm_password:
        return templates.TemplateResponse("create_account.html", {"request": request, "error": "Passwords do not match"})

    # Check if username/email already exists
    if users.find_one({"$or": [{"username": username}, {"email": email}]}):
        return templates.TemplateResponse("create_account.html", {"request": request, "error": "Username or email already exists"})

    # Hash the password
    hashed_password = ph.hash(password)

    # Insert into users collection
    users.insert_one({
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "username": username,
        "password": hashed_password
    })

    # Redirect to login after successful account creation
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)