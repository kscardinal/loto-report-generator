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
		<img src="https://img.shields.io/badge/NGINX-009639.svg?style=for-the-badge&logo=nginx&logoColor=white" alt="NGINX Badge">
		<img src="https://img.shields.io/badge/Jinja-7E0C1B.svg?style=for-the-badge&logo=jinja&logoColor=white" alt="Jinja Badge">
		<img src="https://img.shields.io/badge/JSON-000000.svg?style=for-the-badge&logo=json&logoColor=white" alt="JSON Badge">
		<img src="https://img.shields.io/badge/Markdown-000000.svg?style=for-the-badge&logo=markdown&logoColor=white" alt="Markdown Badge">
		<img src="https://img.shields.io/badge/HTML-E34F26.svg?style=for-the-badge&logo=html5&logoColor=white" alt="HTML Badge">
		<img src="https://img.shields.io/badge/CSS-663399.svg?style=for-the-badge&logo=css&logoColor=white" alt="CSS Badge">
		<img src="https://img.shields.io/badge/MongoDB-47A248.svg?style=for-the-badge&logo=MongoDB&logoColor=white" alt="MongoDB Badge">
		<img src="https://img.shields.io/badge/.env-ECD53F.svg?style=for-the-badge&logo=.env&logoColor=white" alt=".ENV Badge">
		<img src="https://img.shields.io/badge/YAML-CB171E.svg?style=for-the-badge&logo=YAML&logoColor=white" alt="YAML Badge">
		<img src="https://img.shields.io/badge/Pytest-0A9EDC.svg?style=for-the-badge&logo=Pytest&logoColor=white" alt="Pytest Badge">
		<img src="https://img.shields.io/badge/UV-DE5FE9.svg?style=for-the-badge&logo=UV&logoColor=white" alt="UV Badge">
		<img src="https://img.shields.io/badge/docker-2496ED.svg?style=for-the-badge&logo=docker&logoColor=white" alt="Docker Badge">
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
- [Web Interface](#web-interface)
- [SSH](#ssh)
- [Misc](#misc)
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

```
loto-report-generator/
├─ .env                                 # Stores environment variables and secrets (not committed to Git)
├─ .github/
│  └── workflows/                       # GitHub Actions workflows for automated testing and CI/CD
│      └── tests.yml                    # Runs pytest on pushes/merges to verify PDF generation works
├─ .pre-commit-config.yaml              # Pre-commit hook configuration (runs pytest before pushing)
├─ Dockerfile                           # Defines the custom Python Docker image used by the app
├─ docker-compose.yml                   # Sets up and links containers for FastAPI, MongoDB, and Nginx
├─ includes/                            # Static assets and resources used in LOTO PDF generation
├─ logs/                                # Directory for runtime and application logs
├─ mongod.conf                          # MongoDB configuration file
├─ nginx.conf                           # Nginx reverse proxy configuration for serving the FastAPI app
├─ readme_helper.py                     # Script to generate or update the directory structure readme
├─ src/
│  ├── api/
│  │   ├── endpoints.json               # Metadata or route definitions for available API endpoints
│  │   ├── logging_config.py            # Centralized logging configuration for the FastAPI app
│  │   └── main.py                      # FastAPI server entry point; handles API requests and routing
│  ├── database/
│  │   ├── clear_db.py                  # Utility script to clear or reset the MongoDB database
│  │   ├── db.py                        # Handles database initialization and connections
│  │   ├── db_2.py                      # Contains MongoDB helper functions for data management
│  │   ├── db_template.txt              # Template describing schema and properties for new database entries
│  │   └── decode.py                    # Functions to decode data (e.g., images or base64-encoded files)
│  ├── pdf/
│  │   ├── automate_pdf.py              # Automates PDF generation from test data or API triggers
│  │   └── generate_pdf.py              # Core script that builds PDFs from JSON input data
│  ├── tests/
│  │   ├── test_pdf_scripts.py          # Main pytest suite verifying PDF generation and app logic
│  │   ├── test_data.json               # Primary dataset used for PDF testing
│  │   ├── test_data_2.json             # Additional dataset for secondary test case
│  │   ├── test_data_3.json             # Additional dataset for tertiary test case
│  │   └── test_data_....json           # Placeholder for other test datasets covering edge cases
│  └── web/
│      ├── main.html                    # Entry HTML page for the web interface
│      ├── static/
│      │   ├── css/
│      │   │   └── input_form.css       # Stylesheet for the main data input form
│      │   ├── dependencies/
│      │   │   └── energySources.json   # Defines available energy sources and dropdown options
│      │   ├── includes/                # Images, icons, and shared frontend assets
│      │   └── js/
│      │       ├── input_form.js        # Frontend logic for user data input handling
│      │       ├── json_handlers.js     # Manages JSON generation, download, and data processing
│      │       └── upload_json.js       # Handles JSON and photo uploads to the backend/database
│      └── templates/
│          ├── input_form.html          # Jinja2 template for the data entry form page
│          ├── pdf_list.html            # Jinja2 template displaying all reports stored in the database
│          └── view_report.html         # Jinja2 template for viewing a specific report in detail
└─ temp/                                # Temporary storage for generated files or cached data
```

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

### Docker / Server

1. Clone the repo
```bash
git clone <your-repo-url>
cd loto-report-generator
```

2. Create the `.env` file
```bash
vi .env
```
- add the following
```text
# Mongo Credentials
MONGO_USER=...
MONGO_PASSWORD=...
MONGO_HOST=...
MONGO_PORT=...
MONGO_DB=...

# App Config (dev = auto-reload, production = no auto-reload)
APP_ENV=dev

# Server IP (used by PDF scripts)
SERVER_IP=http://<your-server-domain-or-ip>
TEST_SERVER_IP=http://backend:8000
```

3. Start Docker
```bash
docker-compose up -d --build
```
- remove `-d` if you want to see everything behind the covers

4. Test Connection
```bash
docker logs -f fastapi_app
docker logs -f mongo_db
curl http://<server-ip>/api/docs
```
- The first 2 should open logs for both `uvicron` and `mongo`
- The last should return the FastAPI docs page if Nginx is configured correctly

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

5. Check the results
<pre style="color:green;">
============= ___ passed in ___s =============
</pre>
- You are looking out for all of them to say `PASSED`

---

## Web Interface

1. Get TypeScript running
```bash
npm install -D typescript
npx tsc --init
```

2. Compile TypeScript to JavaScript
```bash
npx tsc src/web/scripts/input_form_3.ts --outDir src/web/scripts
```

---

### SSH

1. Start agent
``` bash
eval "$(ssh-agent -s)"
```

2. Add key to agent
```bash
ssh-add ~/.ssh/id_ed25519
```
- Enter passphrase and it should stop bugging you

3. Add this to the `.bashrc` or `.zshrc` file
```bashrc
SSH_ENV="$HOME/.ssh/agent-environment"

function start_agent {
    echo "Starting ssh-agent..."
    ssh-agent -s > "$SSH_ENV"
    source "$SSH_ENV" > /dev/null
    ssh-add -t 8h ~/.ssh/id_ed25519
}

# Source ssh-agent environment file if exists
if [ -f "$SSH_ENV" ]; then
    source "$SSH_ENV" > /dev/null
    # Check if agent is still running
    ps -p $SSH_AGENT_PID > /dev/null || {
        start_agent;
    }
else
    start_agent;
fi
```

---

### Misc

1. Count lines of code
```bash
git ls-files src | xargs wc -l
find . -type f -print0 | xargs -0 wc -l
```

2. Git file endings
```bash
git config --global core.autocrlf
```

--- 

## Customization

- Upload `.json` file with your own data
- Modify `generate_pdf.py` for custom report layouts
- Place additional images or fonts in the `inlcudes/` folder as needed

---

## API Endpoints

```
http://localhost:8000/docs
```
- For more info on each endpoint

| Endpoint                               | Method(s)      | Description                                                                             |
|----------------------------------------|----------------|-----------------------------------------------------------------------------------------|
| `/upload/`                             | POST           | Uploads JSON and other files to the server, storing metadata and photos in the database |
| `/create_report`                       | GET            | Displays a webpage for creating a report with options to download/upload                |
| `/pdf_list`                            | GET            | Displays a webpage listing all PDFs/reports available in the database                   |
| `/pdf_list_json`                       | GET            | Returns JSON of all reports with metadata only (no JSON data or photos)                 |
| `/view_report/{report_name}`           | GET            | Displays detailed report metadata and associated photos (HTML page)                     |
| `/metadata/{report_name}`              | GET            | Returns stored metadata for a specific report as JSON (excluding JSON data/photos)      |
| `/download_report_files/{report_name}` | GET            | Downloads the report JSON and all related photos for a given report name as URLs        |
| `/download_json/{report_name}`         | GET            | Downloads the JSON file for a specific report                                           |
| `/download_photo/{photo_id}`           | GET            | Downloads an individual photo from GridFS by its ID                                     |
| `/download_pdf/{report_name}`          | GET            | Downloads/streams the generated PDF file for the specified report                       |
| `/photo/{photo_id}`                    | GET            | Returns an image stored in GridFS by its ID                                             |
| `/remove_report/{report_name}`         | GET, POST      | Deletes a report from the database (retains shared photos)                              |
| `/cleanup_orphan_photos`               | GET, POST      | Deletes all photos in GridFS not referenced by any report                               |
| `/clear/`                              | POST           | Clears all temporary files in the server's temp directory                               |
| `/db_status`                           | GET            | Checks database connection and returns success or error message                         |



---

## License

This project is licensed under the MIT License, which means you are free to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the software, as long as you include the original copyright and license notice in any copy of the software. The software is provided "as is," without warranty of any kind.
