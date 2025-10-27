import pytest
from pathlib import Path
import shutil
import sys

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.pdf.generate_pdf import generate_pdf
from src.pdf.automate_pdf import main as automate_pdf_main


# === Directories ===
BASE_DIR = Path(__file__).resolve().parents[2]
INCLUDES_DIR = BASE_DIR / "includes"
TEST_DIR = BASE_DIR / "src" / "tests"
TEMP_DIR = BASE_DIR / "temp"
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


# === Actual test ===
def test_files_copied(setup_test_files):
    """Verify test assets were copied into temp/."""
    copied = setup_test_files

    # Check JSON files exist in temp/
    assert all((TEMP_DIR / name).exists() for name in copied["json"]), "Missing JSON files in temp/"

    # Check image files exist in temp/
    assert all((TEMP_DIR / name).exists() for name in copied["images"]), "Missing images in temp/"
