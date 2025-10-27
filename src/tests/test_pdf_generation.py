import pytest
from pathlib import Path
import shutil
import sys
import subprocess
import os
import contextlib
from pdf2image import convert_from_path
from PIL import ImageChops


# Add project root to path
sys.path.append(str(Path(__file__).resolve().parents[2]))


# === Directories ===
BASE_DIR = Path(__file__).resolve().parents[2]
GENERATE_PDF_SCRIPT = Path(__file__).resolve().parents[2] / "src" / "pdf" / "generate_pdf.py"
AUTOMATE_PDF_SCRIPT = Path(__file__).resolve().parents[2] / "src" / "pdf" / "automate_pdf.py"
INCLUDES_DIR = BASE_DIR / "includes"
TEST_DIR = BASE_DIR / "src" / "tests"
TEMP_DIR = BASE_DIR / "temp"
REFERENCE_DIR  = TEST_DIR / "comparison"

# === Create TEMP_DIR if it doesn't arleady exist ===
TEMP_DIR.mkdir(parents=True, exist_ok=True)


# === Utility: Clears TEMP_DIR before the test ===
def clear_temp_dir():
    """Remove all files and folders in TEMP_DIR."""
    for item in TEMP_DIR.iterdir():
        if item.is_file() or item.is_symlink():
            item.unlink()
        elif item.is_dir():
            shutil.rmtree(item)
    print("\n")
    print(f"🗑️  Cleared TEMP_DIR")


# === Utility: Copy matching files ===
def copy_files_from(source: Path, pattern: str):
    copied = []
    for file in source.glob(pattern):
        dest = TEMP_DIR / file.name
        if dest.exists():
            print(f"⚠️ Skipped (already exists): {file.name}")
            continue
        shutil.copy(file, dest)
        copied.append(file.name)
        print(f"📁 Copied {file.name}")
    return copied


# === Utility: Removes all files at the end except for the PDFs ===
def cleanup_temp_keep_pdfs():
    """Remove everything in TEMP_DIR except PDF files."""
    for item in TEMP_DIR.iterdir():
        if item.is_file() and item.suffix.lower() != ".pdf":
            item.unlink()
        elif item.is_dir():
            shutil.rmtree(item)
    print(f"\n\n🗑️  Cleaned TEMP_DIR but kept PDFs")


# === Fixture: Copy everything needed for tests ===
@pytest.fixture(scope="session")
def setup_test_files():
    clear_temp_dir()
    print("\nCopying test files...")
    copied_json = copy_files_from(TEST_DIR, "*.json")
    copied_images = copy_files_from(INCLUDES_DIR, "test_*.jpg")
    print(f"\n✅ Copied {len(copied_json)} JSON files and {len(copied_images)} images.\n")
    return {"json": copied_json, "images": copied_images}


# === Utility: Copies JSON without clearing TEMP_DIR ===
def copy_without_clear():
    print("\nCopying test files...")
    copied_json = copy_files_from(TEST_DIR, "*.json")
    copied_images = copy_files_from(INCLUDES_DIR, "test_*.jpg")
    print(f"\n✅ Copied {len(copied_json)} JSON files and {len(copied_images)} images.\n")
    return {"json": copied_json, "images": copied_images}


# === Test: Loop over all JSON and JPG file and transfer them to TEMP_DIR ===
def test_files_copied(setup_test_files):
    """Verify test assets were copied into temp/."""
    copied = setup_test_files

    # Check JSON files exist in temp/
    assert all((TEMP_DIR / name).exists() for name in copied["json"]), "❌ Missing JSON files in temp/"

    # Check image files exist in temp/
    assert all((TEMP_DIR / name).exists() for name in copied["images"]), "❌ Missing images in temp/"


# === Test: Loop over all JSON files and run generate_pdf.py ===
def test_generate_pdfs(setup_test_files):
    """Run generate_pdf.py for every JSON file in TEMP_DIR."""
    json_files = list(TEMP_DIR.glob("*.json"))

    print("\n")

    for json_file in json_files:
        output_pdf = TEMP_DIR / f"{json_file.stem}.pdf"

        print(f"🤖 Generating {json_file.name}")

        # Suppress stdout for generate_pdf.py only
        with open(os.devnull, "w") as fnull, contextlib.redirect_stdout(fnull):
            result = subprocess.run(
                ["python", str(GENERATE_PDF_SCRIPT), str(json_file)],
                stdout=subprocess.DEVNULL,  # hide all stdout (icecream prints)
                stderr=subprocess.PIPE,      # still capture errors
                text=True
            )

        # Print your helper/diagnostic statements as usual
        print(f"✅ Processed {json_file.name}\n")
        #if result.stderr:
        #    print(result.stderr)

        # Assertions
        assert result.returncode == 0, f"❌ PDF generation failed for {json_file.name}"
        assert output_pdf.exists(), f"❌ PDF not created for {json_file.name}"


# === Utility: Compare PDFs===
def pdfs_layout_equal(pdf1, pdf2, dpi=200, verbose=False):
    images1 = convert_from_path(str(pdf1), dpi=dpi)
    images2 = convert_from_path(str(pdf2), dpi=dpi)
    
    if len(images1) != len(images2):
        if verbose:
            print(f"❌ Page count mismatch: {len(images1)} vs {len(images2)}")
        return False

    for i, (img1, img2) in enumerate(zip(images1, images2)):
        diff = ImageChops.difference(img1, img2)
        bbox = diff.getbbox()
        if bbox is not None:
            if verbose:
                print(f"❌ Difference on page {i+1}")
            return False
        elif verbose:
            print(f"✅ Page {i+1} matches")

    return True


# === Test: Compare PDF layouts verbosely and continue on errors ===
def test_pdf_layouts():
    cleanup_temp_keep_pdfs()
    pdf_files = list(TEMP_DIR.glob("*.pdf"))
    assert pdf_files, "❌ No PDFs found in TEMP_DIR to test."

    failed_pdfs = []

    for pdf_file in pdf_files:
        reference_pdf = REFERENCE_DIR / pdf_file.name

        if not reference_pdf.exists():
            print(f"⚠️  Reference PDF missing: {reference_pdf}")
            failed_pdfs.append(pdf_file.name)
            continue

        print(f"\n🔍 Comparing: {pdf_file.name}")
        try:
            # pdfs_layout_equal should be your function comparing the PDFs
            equal = pdfs_layout_equal(pdf_file, reference_pdf, verbose=True)  # you can modify your function to accept a verbose flag
            if equal:
                print(f"✅ Layout matches reference.")
            else:
                print(f"❌ Layout differs!")
                failed_pdfs.append(pdf_file.name)

        except Exception as e:
            print(f"❌ Error comparing PDFs: {e}")
            failed_pdfs.append(pdf_file.name)

    if failed_pdfs:
        print("\nSummary of PDFs with layout differences or errors:")
        for f in failed_pdfs:
            print(f" - {f}")
        # Fail the test if any PDFs didn't match
        pytest.fail(f"❌ {len(failed_pdfs)} PDF(s) failed visual inspection: {', '.join(failed_pdfs)}", pytrace=False)
    else:
        print("\n✅ All PDFs match their references!")




def cleanup_root_pdfs():
    """Remove all PDFs in the root directory before running tests."""
    for pdf_file in BASE_DIR.glob("*.pdf"):
        pdf_file.unlink()

def test_automate_pdfs():
    """Run generate_pdf.py for every JSON file in TEMP_DIR."""

    cleanup_root_pdfs()
    print("\n\n🗑️  Removed all PDFs from the root directory\n")
    copy_without_clear()
    print(f"📁 Copied files to TEMP_DIR")

    json_files = list(TEMP_DIR.glob("*.json"))

    for json_file in json_files:
        output_pdf = BASE_DIR / f"{json_file.stem}.pdf"

        print(f"🤖 Automating {json_file.name}")
        copy_without_clear()

        # Suppress stdout for generate_pdf.py only
        with open(os.devnull, "w") as fnull, contextlib.redirect_stdout(fnull):
            result = subprocess.run(
                ["python", str(AUTOMATE_PDF_SCRIPT), str(json_file)],
                stdout=subprocess.DEVNULL,  # hide all stdout (icecream prints)
                stderr=subprocess.PIPE,      # still capture errors
                text=True
            )

        # Print your helper/diagnostic statements as usual
        print(f"✅ Processed {json_file.name}\n")
        #if result.stderr:
        #    print(result.stderr)

        # Assertions
        assert result.returncode == 0, f"❌ PDF generation failed for {json_file.name}"
        assert output_pdf.exists(), f"❌ PDF not created for {json_file.name}"