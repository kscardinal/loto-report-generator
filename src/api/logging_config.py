# logging_config.py
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import json
from datetime import datetime
from fastapi import Request

# --- Directories ---
LOGS_DIR = Path(__file__).parent.parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# --- Normal App Logging ---
app_log_file = LOGS_DIR / "app.log"
app_handler = RotatingFileHandler(
    filename=app_log_file,
    maxBytes=1 * 1024 * 1024,  # 5 MB per file
    backupCount=5,             # keep 5 old log files
    encoding="utf-8"
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        app_handler
    ]
)
logger = logging.getLogger("app")  # use logger.info(...) in your code

# --- Structured JSON Logging ---
structured_log_file = LOGS_DIR / "structured_app.log"
structured_file_handler = RotatingFileHandler(
    filename=structured_log_file,
    maxBytes=5 * 1024 * 1024,
    backupCount=5,
    encoding="utf-8"
)

structured_logger = logging.getLogger("structured_app")
structured_logger.setLevel(logging.INFO)
structured_logger.addHandler(structured_file_handler)

# --- Middleware for FastAPI ---
async def log_requests_json(request: Request, call_next):
    start_time = datetime.utcnow()
    response = await call_next(request)
    end_time = datetime.utcnow()

    log_entry = {
        "timestamp": end_time.isoformat(),
        "client_ip": request.client.host,
        "method": request.method,
        "endpoint": request.url.path,
        "status": response.status_code,
        "duration_ms": (end_time - start_time).total_seconds() * 1000,
        "user_agent": request.headers.get("user-agent")
    }

    # Correct way: use the logger instead of opening the file
    structured_logger.info(json.dumps(log_entry))

    return response
