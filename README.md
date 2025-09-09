# 📌 loto-report-generator  
`loto-report-generator` is a Python application for generating PDF reports related to lockout/tagout procedures. It uses custom fonts and images, and can be configured for different server environments. 

![GitHub License](https://img.shields.io/github/license/kscardinal/loto-report-generator)
![GitHub Release](https://img.shields.io/github/v/release/kscardinal/loto-report-generator)
![GitHub commit activity](https://img.shields.io/github/commit-activity/t/kscardinal/loto-report-generator)
![GitHub last commit](https://img.shields.io/github/last-commit/kscardinal/loto-report-generator)
![GitHub contributors](https://img.shields.io/github/contributors/kscardinal/loto-report-generator)

---

## Table of Contents  
- [Overview](#Overview)
- [Features](#features)
- [Tech Stack](#Tech-Stack)
- [Project Structure](#project-structure)
- [Setup](#setup)
- [Usage](#usage)
- [Customization](#customization)
- [API Endpoints](#API-Endpoints)
- [License](#License)

---

## Overview  

`loto-report-generator` is a Python-based tool designed to automate the creation of PDF reports for lockout/tagout (LOTO) procedures. It streamlines the reporting process by integrating custom templates, images, and fonts, allowing users to generate professional and consistent documentation. The application is configurable for different environments and can be easily customized to fit specific organizational needs, making it ideal for safety compliance and operational record-keeping.  

---

## Features  

- **Automated PDF Generation**: Instantly creates professional LOTO reports using custom templates, images, and fonts for a polished look.
- **Environment Configuration via .env**: Easily adapts to different server setups and deployment scenarios with simple environment variable management.
- **Extensible Data Input**: Supports dynamic data sources (like JSON) for flexible report customization and integration with other systems.
- **Modular Design**: Separates logic for PDF creation, automation, and templating, making it easy to extend or modify for future enhancements.

---

## Tech Stack  

- **Frontend**: N/A  
- **Backend**: Python, FastAPI  
- **Database**: N/A  
- **Other Tools**: ReportLab

---

## Project Structure  

- loto-report-generator/
- ├── includes/               # Photos and fonts
- ├── tests/	# Tests folder
- ├    ├── [`test_data.json`](test_data.json) # Test JSON data
- ├── src/loto-report-generator                         # Python files
- ├    ├── [`generate_pdf.py`](generate_pdf.py)     # Generate PDF on device
- └    └── [`__init__.py`](__init__.py)       # Python Package


---

## Setup

1. **Install uv**
	Download and install [uv](https://github.com/astral-sh/uv) from the official repository or use:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv self update
uv python install 3.13
```

2. **Create a virtual environment**
```bash
uv venv
```

3. **Install dependencies**
```bash
uv pip install -e .
```

4. **Add a `.env` file**
	- Create a file named `.env` in the project root directory.
	- Add the following line (replace with your server IP, no quotes):
```bash
SERVER_IP = your.server.ip.address
```

---

## Usage

1. Add included photos to root folder
2. Run the automate_pdf script:
```python
python automate_pdf.py
```
-- or --
```python
python main.py
```

---

## Customization

- Upload `.json` file with your own data
- Modify `generate_pdf.py` for custom report layouts
- Place additional images or fonts in the `inlcudes/` folder as needed

---

## API Endpoints

| Endpoint                   | Method | Description                                       |
| -------------------------- | ------ | ------------------------------------------------- |
| `/upload`                  | POST   | Uploads files (JSON and other types) to server    |
| `/generate`                | POST   | Trigger PDF generation from a specified JSON file |
| `/transfer/{pdf_filename}` | GET    | Downloads a generated PDF by filename             |
| `/clear`                   | POST   | Clears all temporary files from the server        |


---

## License

This project is licensed under the MIT License, which means you are free to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the software, as long as you include the original copyright and license notice in any copy of the software. The software is provided "as is," without warranty of any kind.

