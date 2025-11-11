import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse
import os
from dotenv import load_dotenv
from argon2 import PasswordHasher
from urllib.parse import quote
from bson import ObjectId

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

def log_action(audit_logs_collection, username: str, action: str, details=None):
    audit_logs_collection.insert_one({
        "username": username,
        "action": action,
        "details": details or {},
        "timestamp": datetime.utcnow()
    })
