from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import FileResponse
from typing import List
import json
import uuid
import os
from generate_pdf import generate_pdf_from_json

app = FastAPI()

UPLOAD_DIR = "/tmp/pdf_uploads"

@app.post("/generate-pdf/")
async def generate_pdf_endpoint(
    json_file: UploadFile = File(...),
    image_files: List[UploadFile] = File(default=[]),
):
    # Make sure upload directory exists
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # Save all images to temp dir
    for image in image_files:
        image_path = os.path.join(UPLOAD_DIR, image.filename)
        with open(image_path, "wb") as f:
            f.write(await image.read())

    # Load and patch JSON
    try:
        contents = await json_file.read()
        json_data = json.loads(contents)
    except Exception as e:
        return {"error": f"Invalid JSON: {str(e)}"}

    # Update image paths in JSON if needed (optional — depends on your code)
    # If your PDF generator loads images like: Image.open("includes/image.jpg")
    # then just symlink/copy to that folder or point it to UPLOAD_DIR

    # Set working dir if needed
    os.chdir(UPLOAD_DIR)

    # Generate PDF
    output_pdf = f"/tmp/output_{uuid.uuid4().hex}.pdf"
    try:
        generate_pdf_from_json(data, output_pdf)
        return FileResponse(output_pdf, media_type='application/pdf', filename="generated.pdf")
    except Exception as e:
        return {"error": f"PDF generation failed: {str(e)}"}
