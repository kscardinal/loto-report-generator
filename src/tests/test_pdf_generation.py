import pytest
from pathlib import Path
import shutil
import sys
import subprocess
import os
import contextlib


# Add project root to path
sys.path.append(str(Path(__file__).resolve().parents[2]))


# === Directories ===
BASE_DIR = Path(__file__).resolve().parents[2]
GENERATE_PDF_SCRIPT = Path(__file__).resolve().parents[2] / "src" / "pdf" / "generate_pdf.py"
INCLUDES_DIR = BASE_DIR / "includes"
TEST_DIR = BASE_DIR / "src" / "tests"
TEMP_DIR = BASE_DIR / "temp"
COMPARE_DIR = TEST_DIR / "comparison"

# === Create TEMP_DIR if it doesn't arleady exist ===
TEMP_DIR.mkdir(parents=True, exist_ok=True)


# === Utility: Copy matching files ===
def copy_files_from(source: Path, pattern: str):
    copied = []
    for file in source.glob(pattern):
        dest = TEMP_DIR / file.name
        if dest.exists():
            print(f"Skipped (already exists): {file.name}")
            continue
        shutil.copy(file, dest)
        copied.append(file.name)
        print(f"Copied {file.name}")
    return copied


# === Fixture: Copy everything needed for tests ===
@pytest.fixture(scope="session")
def setup_test_files():
    print("\nCopying test files...")
    copied_json = copy_files_from(TEST_DIR, "*.json")
    copied_images = copy_files_from(INCLUDES_DIR, "test_*.jpg")
    print(f"Copied {len(copied_json)} JSON files and {len(copied_images)} images.")
    return {"json": copied_json, "images": copied_images}


# === Test: Loop over all JSON and JPG file and transfer them to TEMP_DIR ===
def test_files_copied(setup_test_files):
    """Verify test assets were copied into temp/."""
    copied = setup_test_files

    # Check JSON files exist in temp/
    assert all((TEMP_DIR / name).exists() for name in copied["json"]), "Missing JSON files in temp/"

    # Check image files exist in temp/
    assert all((TEMP_DIR / name).exists() for name in copied["images"]), "Missing images in temp/"


# === Test: Loop over all JSON files and run generate_pdf.py ===
def test_generate_pdfs(setup_test_files):
    """Run generate_pdf.py for every JSON file in TEMP_DIR."""
    json_files = list(TEMP_DIR.glob("*.json"))

    for json_file in json_files:
        output_pdf = TEMP_DIR / f"{json_file.stem}.pdf"

        # Suppress stdout for generate_pdf.py only
        with open(os.devnull, "w") as fnull, contextlib.redirect_stdout(fnull):
            result = subprocess.run(
                ["python", str(GENERATE_PDF_SCRIPT), str(json_file)],
                stdout=subprocess.DEVNULL,  # hide all stdout (icecream prints)
                stderr=subprocess.PIPE,      # still capture errors
                text=True
            )

        # Print your helper/diagnostic statements as usual
        print(f"Processed {json_file.name}")
        if result.stderr:
            print("Errors from script:")
            print(result.stderr)

        # Assertions
        assert result.returncode == 0, f"PDF generation failed for {json_file.name}"
        assert output_pdf.exists(), f"PDF not created for {json_file.name}"


