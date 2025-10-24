from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from pathlib import Path
import subprocess
import shutil
import traceback

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

# Define base paths
BASE_DIR = Path(__file__).parent.parent.parent
INCLUDES_DIR = BASE_DIR / "includes"
JSON_DIR = BASE_DIR / "src" / "tests"
TEMP_DIR = BASE_DIR / "temp"
PROCESS_DIR = BASE_DIR / "src" / "pdf"


# Create required directories
for directory in [TEMP_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# -----------------------------
# Upload route
# -----------------------------
@app.post("/upload/")
async def upload_files(files: List[UploadFile] = File(...)):
    saved_files = []

    for file in files:
        if file.filename.lower().endswith(".json"):
            dest_dir = TEMP_DIR
        else:
            dest_dir = TEMP_DIR

        file_location = dest_dir / file.filename
        contents = await file.read()
        with open(file_location, "wb") as f:
            f.write(contents)
        saved_files.append(str(file_location))

    return {"uploaded_files": saved_files}

# -----------------------------
# Generate PDF from JSON
# -----------------------------
class GenerateRequest(BaseModel):
    json_filename: str

@app.post("/generate/")
async def generate_pdf(request: GenerateRequest):
    json_filename = Path(request.json_filename).name
    json_path = JSON_DIR / json_filename

    if not json_path.exists():
        return JSONResponse(status_code=400, content={
            "error": f"JSON file '{json_filename}' not found in {JSON_DIR}"
        })

    try:
        result = subprocess.run(
            ["python", str(PROCESS_DIR / "generate_pdf.py"), str(JSON_DIR / json_filename)],
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
    file_path = JSON_DIR / safe_name

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