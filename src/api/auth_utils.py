import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends, Request, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse
import os
from dotenv import load_dotenv
from argon2 import PasswordHasher
from urllib.parse import quote
from bson import ObjectId
import requests
from typing import Optional, Dict
from typing import Optional, Dict
import httpx
from pymongo.collection import Collection
from icecream import ic

ph = PasswordHasher()

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY not set in .env")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

security = HTTPBearer()

def create_access_token(data: dict, expires_delta: int = ACCESS_TOKEN_EXPIRE_MINUTES):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_delta)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(request: Request, redirect: bool = True):
    token = None

    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]

    if not token:
        token = request.cookies.get("access_token")

    if not token:
        if redirect and "text/html" in request.headers.get("accept", ""):
            response = RedirectResponse("/login")
            response.set_cookie(
                "return_url",
                str(request.url),
                max_age=60*5,  # optional: expires in 5 min
                httponly=True
            )
            return response
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return {
            "username": payload.get("sub"),
            "role": payload.get("role", "user")
        }
    except jwt.PyJWTError:
        if redirect and "text/html" in request.headers.get("accept", ""):
            response = RedirectResponse("/login")
            response.set_cookie(
                "return_url",
                str(request.url),
                max_age=60*5,
                httponly=True
            )
            return response
        raise HTTPException(status_code=401, detail="Invalid token")
    
def get_current_user_no_redirect(request: Request):
    user = get_current_user(request, redirect=False)
    if not user:
        raise HTTPException(status_code=403, detail="Forbidden: Not authenticated")
    return user

def require_role(required_role: str):
    def wrapper(user):
        if isinstance(user, RedirectResponse):
            return user

        role = user.get("role")

        # Hierarchy: owner > admin > user
        hierarchy = {"owner": 3, "admin": 2, "user": 1}

        if hierarchy.get(role, 0) < hierarchy.get(required_role, 0):
            raise HTTPException(status_code=403, detail="Insufficient permissions")

        return None  # No error
    return wrapper

# --- Get client IP ---
def get_client_ip(request: Request) -> str:
    xff = request.headers.get("X-Forwarded-For") or request.headers.get("x-forwarded-for")
    if xff:
        ip = xff.split(",")[0].strip()
        if ip:
            return ip
    client = request.client
    if client is not None:
        return client.host
    return "unknown"


# --- Async IP lookup with DB cache ---
async def lookup_ip_with_db(ip: str, known_locations_collection: Collection, timeout: int = 5) -> Optional[Dict]:
    if ip in ("127.0.0.1", "localhost", "unknown"):
        return None

    # Check DB first
    existing = known_locations_collection.find_one({"ip_address": ip})
    if existing:
        location = existing.get("location")
        if location and any(location.values()):  # at least one field is non-empty
            return location
        else:
            print(f"Location missing or incomplete for {ip}, trying IPAPI again")


    # Query API
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            res = await client.get(f"https://ipapi.co/{ip}/json/")
            if res.status_code == 200:
                data = res.json()
                location = {
                    "city": data.get("city"),
                    "region": data.get("region"),
                    "country": data.get("country_name"),
                    "latitude": data.get("latitude"),
                    "longitude": data.get("longitude")
                }
                # Store in DB
                known_locations_collection.update_one(
                    {"ip_address": ip},
                    {"$set": {"location": location, "last_updated": datetime.utcnow()}},
                    upsert=True
                )
                return location
            elif res.status_code == 429:
                print(f"Rate limit hit for IPAPI on {ip}")
    except Exception as e:
        print(f"IPAPI lookup failed for {ip}: {e}")

    return None


# --- Background task for logging ---
async def update_log_location(audit_logs_collection: Collection, known_locations_collection: Collection, log_id, ip):
    geo = await lookup_ip_with_db(ip, known_locations_collection)
    if geo:
        audit_logs_collection.update_one({"_id": log_id}, {"$set": {"location": geo}})


def update_log_location_sync(audit_logs_collection: Collection, known_locations_collection: Collection, log_id, ip):
    import asyncio
    asyncio.run(update_log_location(audit_logs_collection, known_locations_collection, log_id, ip))


# --- Main logging function ---
def log_action(
    request: Request,
    audit_logs_collection: Collection,
    known_locations_collection: Collection,
    username: str,
    action: str,
    details=None,
    background_tasks: BackgroundTasks = None
):
    client_ip = get_client_ip(request)

    log_entry = {
        "ip_address": client_ip,
        "location": None,  # filled later
        "username": username,
        "action": action,
        "details": details or {},
        "timestamp": datetime.utcnow()
    }

    inserted = audit_logs_collection.insert_one(log_entry)
    log_id = inserted.inserted_id

    if background_tasks:
        background_tasks.add_task(update_log_location_sync, audit_logs_collection, known_locations_collection, log_id, client_ip)