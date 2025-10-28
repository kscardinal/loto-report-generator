<div style="text-align: center;">
	<h1 align="center">📌 loto-report-generator</h1>
	<p align="center"><code>loto-report-generator</code>is a Python application for generating PDF reports related to lockout/tagout procedures. It uses custom fonts and images, and can be configured for different server environments.</p>
</div>

---

<div style="text-align: center;">
	<p align="center">
		<img src="https://img.shields.io/github/license/kscardinal/loto-report-generator?style=for-the-badge&logo=git&logoColor=white&color=0080ff" alt="GitHub License">
		<img src="https://img.shields.io/github/v/release/kscardinal/loto-report-generator?style=for-the-badge&logo=git&logoColor=white&color=0080ff" alt="GitHub Release">
		<img src="https://img.shields.io/github/commit-activity/t/kscardinal/loto-report-generator?style=for-the-badge&logo=git&logoColor=white&color=0080ff" alt="GitHub Commit Activity">
		<img src="https://img.shields.io/github/last-commit/kscardinal/loto-report-generator?style=for-the-badge&logo=git&logoColor=white&color=0080ff" alt="GitHub Last Commit">
		<img src="https://img.shields.io/github/contributors/kscardinal/loto-report-generator?style=for-the-badge&logo=git&logoColor=white&color=0080ff" alt="GitHub Contributors">
		<img src="https://img.shields.io/github/actions/workflow/status/kscardinal/loto-report-generator/tests.yml?label=PDF%20Generation&style=for-the-badge&logo=github&logoColor=white&color=4CAF50" alt="GitHub Actions Workflow Status">
	</p>
</div>
<div style="text-align: center; padding-top: 30px">
	<p align="center">
		<img src="https://img.shields.io/badge/python-3776AB.svg?style=for-the-badge&logo=python&logoColor=white" alt="Python Badge">
		<img src="https://img.shields.io/badge/JavaScript-F7DF1E.svg?style=for-the-badge&logo=javascript&logoColor=white" alt="JavaScript Badge">
		<img src="https://img.shields.io/badge/TypeScript-3178C6.svg?style=for-the-badge&logo=typescript&logoColor=white" alt="TypeScript Badge">
		<img src="https://img.shields.io/badge/FastAPI-009688.svg?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI Badge">
		<img src="https://img.shields.io/badge/Jinja-7E0C1B.svg?style=for-the-badge&logo=jinja&logoColor=white" alt="Jinja Badge">
		<img src="https://img.shields.io/badge/JSON-000000.svg?style=for-the-badge&logo=json&logoColor=white" alt="JSON Badge">
		<img src="https://img.shields.io/badge/Markdown-000000.svg?style=for-the-badge&logo=markdown&logoColor=white" alt="Markdown Badge">
		<img src="https://img.shields.io/badge/HTML-E34F26.svg?style=for-the-badge&logo=html5&logoColor=white" alt="HTML Badge">
		<img src="https://img.shields.io/badge/CSS-663399.svg?style=for-the-badge&logo=css&logoColor=white" alt="CSS Badge">
		<img src="https://img.shields.io/badge/MongoDB-47A248.svg?style=for-the-badge&logo=MongoDB&logoColor=white" alt="MongoDB Badge">
		<img src="https://img.shields.io/badge/env-ECD53F.svg?style=for-the-badge&logo=.env&logoColor=white" alt=".ENV Badge">
		<img src="https://img.shields.io/badge/Pytest-0A9EDC.svg?style=for-the-badge&logo=Pytest&logoColor=white" alt="Pytest Badge">
		<img src="https://img.shields.io/badge/UV-DE5FE9.svg?style=for-the-badge&logo=UV&logoColor=white" alt="UV Badge">
	</p>
</div>

---

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup](#setup)
- [PDF Generation](#pdf-generation)
- [Database Management](#database-management)
- [PyTest](#pytest)
- [Customization](#customization)
- [API Endpoints](#api-endpoints)
- [License](#license)

---

## Overview  

`loto-report-generation` is a Python-based tool designed to automate the creation of PDF reports for lockout/tagout (LOTO) procedures. It streamlines the reporting process by integrating custom templates, images, and fonts, allowing users to generate professional and consistent documentation. The application is configurable for different environments and can be easily customized to fit specific organizational needs, making it ideal for safety compliance and operational record-keeping.  

---

## Features  

- **Automated PDF Generation**: Instantly creates professional LOTO reports using custom templates, images, and fonts for a polished look.
- **Environment Configuration via .env**: Easily adapts to different server setups and deployment scenarios with simple environment variable management.
- **Extensible Data Input**: Supports dynamic data sources (like JSON) for flexible report customization and integration with other systems.
- **Modular Design**: Separates logic for PDF creation, automation, and templating, making it easy to extend or modify for future enhancements.

---

## Tech Stack  

- **Frontend**: HTML, CSS, JavaScript, TypeScript, Markdown  
- **Backend**:  Python, FastAPI, Jinja  
- **Database**:  MongoDB  
- **Other Tools**: ReportLab, UV, Pytest


---

## Project Structure  

- `loto-report-generator/`
- ├── `includes/` # Includes all the assets needed to make the LOTO PDF
- ├── `src/`
- ├───── [`api/`](src/api)
- ├──────── [`main.py`](src/api/main.py) # Server component that receives the requests and handles them
- ├───── [`database/`](src/database)
- ├──────── [`db.py`](src/database/db.py) # Creates the MongoDB database used to store all the files
- ├──────── [`db_template.json`](src/database/db_template.json) # Template for a new entry into the database will all properties and descriptions
- ├───── [`pdf/`](src/pdf)
- ├──────── [`automate_pdf.py`](src/pdf/automate_pdf.py) # Automates the creation of the PDF file using the server component
- ├──────── [`generate_pdf.py`](src/pdf/generate_pdf.py) # Generates the PDF with a given JSON file
- ├───── [`tests/`](src/tests)
- ├──────── [`test_data.json`](src/tests/test_data.json) # Main testing data set
- ├──────── `test_data_....json` # More test data sets to test edge cases of the PDF generation
- ├───── [`web/`](src/web)
- ├──────── [`templates/`](src/web/templates)
- ├─────────── [`pdf_list.html`](src/web/templates/pdf_list.html) # Template for webpage that shows all current files in the database
- ├── `temp/`
- └── [`.env`](.env) # Where the secrets go

---

## Setup

1. **Install uv**
	Download and install [uv](https://github.com/astral-sh/uv) from the official repository or use:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv self update
uv python install 3.13.2
```

2. **Create a virtual environment**
```bash
uv venv
source .venv/bin/activate
# --- OR ---
source .venv/Scripts/activate
```

3. **Confirm virtual environment**
```bash
# --- MacOS ---
where python
# --- Windows ---
which python
```

3. **Install dependencies**
```bash
# --- Might need to clear cache if it is an issue ---
uv cache clean  # Optional
uv sync
uv pip install -e .
```

4. **Add a `.env` file**
	- Create a file named `.env` in the project root directory.
	- Add the following line (replace with your server IP, no quotes):
```bash
SERVER_IP = your.server.ip.address
```
- Should start with http:// (ex. SERVER_IP=http://127.0.0.1:8000)

---

## PDF Generation

1. Start server
``` bash
uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8000
```
2. Add temp assets to the `temp/` folder for usage in the scripts
3. Run the automate_pdf script:
```python
python automate_pdf.py $JSON_FILE
```
-- or --
```python
python generate_pdf.py $JSON_FILE
```

---

## Database Management

1. Configure and start MongoDB (Mac example)
``` bash
# one-time
brew tap mongodb/brew
brew install mongodb-community@7.0

# run on login (recommended)
brew services start mongodb-community@7.0

# verify it’s listening
lsof -nP -iTCP:27017 -sTCP:LISTEN
```

2. Double check mongosh
```bash
mongosh "mongodb://127.0.0.1:27017/?directConnection=true" --eval "db.adminCommand({ ping: 1 })"
```

3. Look at the current database on the web
``` txt
http://localhost:8000/pdf_list
```

---

### PyTest

1. Install `poppler`
``` bash
# Windows
https://github.com/oschwartz10612/poppler-windows/releases/
```
- Download latest ZIP release on GitHub
- Extract the zip somewhere, e.g. `C:\tools\poppler-23.12.0\`
	- or latest release number
	- if folder doesn't exist, add it
- Add the `bin` folder to your`PATH` environment variable:
	- `C:\tools\poppler-23.12.0\Library\bin`
	- System variables

``` bash
# MacOS
brew install poppler
```

2. Check `poppler` installation
``` bash
pdfinfo -v
pdftoppm -v
```

3. Double check `pre-commit` and `pre-push` hooks are updated
``` bash
uv add pre-commit # if not already added
pre-commit install --hook-type pre-commit --hook-type pre-push
pre-commit autoupdate
pre-commit run --all-files
```

4. Run the tests
``` bash
pytest -v -s --no-summary src/tests/test_pdf_scripts.py
```
- `-q` is optional to reduce more of the unnecessary text in the test

5Check the results
<pre style="color:green;">
============= ___ passed in ___s =============
</pre>
- You are looking out for all of them to say `PASSED`

--- 

## Customization

- Upload `.json` file with your own data
- Modify `generate_pdf.py` for custom report layouts
- Place additional images or fonts in the `inlcudes/` folder as needed

---

## API Endpoints

| Endpoint                   | Method | Description                                                     |
|----------------------------|--------|-----------------------------------------------------------------|
| `/upload`                  | POST   | Uploads files (JSON and other types) to server                  |
| `/generate`                | POST   | Trigger PDF generation from a specified JSON file               |
| `/transfer/{pdf_filename}` | GET    | Downloads a generated PDF by filename                           |
| `/clear`                   | POST   | Clears all temporary files from the server                      |
| `/pdf_list`                | GET    | Gets all PDFs in the DB and hosts a webpage with them in a list | 


---

## License

This project is licensed under the MIT License, which means you are free to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the software, as long as you include the original copyright and license notice in any copy of the software. The software is provided "as is," without warranty of any kind.
