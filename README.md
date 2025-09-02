# loto-report-generator

## Setup Instructions

1. **Install uv**
	Download and install [uv](https://github.com/astral-sh/uv) from the official repository or use:
	```powershell
	curl -LsSf https://astral.sh/uv/install.sh | sh
 	uv self update
 	uv python install 3.13
 	
	```

2. **Create a virtual environment**
	```powershell
	uv venv
	```

3. **Install dependencies**
	```powershell
	uv pip install -e .
	```

4. **Add a `.env` file**
	- Create a file named `.env` in the project root directory.
	- Add the following line (replace with your server IP, no quotes):
	  ```
	  SERVER_IP = your.server.ip.address
	  ```

---

## Project Overview

`loto-report-generator` is a Python application for generating PDF reports related to lockout/tagout procedures. It uses custom fonts and images, and can be configured for different server environments.

### Main Files
- `main.py`: Entry point for running the application.
- `generate_pdf.py`: Handles PDF generation logic.
- `automate_pdf.py`: Automates PDF creation tasks.
- `main.html`: HTML template for report rendering.
- `test_data.json`: Example data for testing.
- `includes/`: Contains images and font files used in reports.

### Usage
After setup, run the main script:
```powershell
python main.py
```

### Customization
- Update `test_data.json` with your own data.
- Modify `main.html` for custom report layouts.
- Place additional images or fonts in the `includes/` folder as needed.

### License
See LICENSE file (if present) for details.

---

For questions or support, contact the repository owner.
