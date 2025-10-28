import os
import sys
import shutil
import subprocess
import contextlib
from pathlib import Path
from typing import Dict, Optional, Callable, Literal, List
import pytest
from pdf2image import convert_from_path
from PIL import ImageChops

# === Resolve project paths ===
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))  # if your scripts import local modules

BASE_DIR = PROJECT_ROOT
GENERATE_PDF_SCRIPT = PROJECT_ROOT / "src" / "pdf" / "generate_pdf.py"
AUTOMATE_PDF_SCRIPT = PROJECT_ROOT / "src" / "pdf" / "automate_pdf.py"
INCLUDES_DIR = PROJECT_ROOT / "includes"
TEST_DIR = PROJECT_ROOT / "src" / "tests"
TEMP_DIR = PROJECT_ROOT / "temp"
REFERENCE_DIR = TEST_DIR / "comparison"

TEMP_DIR.mkdir(parents=True, exist_ok=True)


# === Utilities ===
def clear_dir(
        directory: Path = TEMP_DIR,
        excluded_files: Optional[List[str]] = None,
        pattern: Optional[str] = None,
) -> None:
    """
    Remove files and folders in a directory.

    Args:
        directory (Path): Directory to clean.
        excluded_files (List[str], optional): Filenames or stems to skip.
        pattern (str, optional): Glob pattern to match specific files to delete.
            Example:
                "*.pdf" → only delete PDFs
                "!*.pdf" → delete everything except PDFs
    """

    if not directory.exists():
        directory.mkdir(parents=True, exist_ok=True)
        print(f"🗂️ Created directory {directory} (nothing to clear)")
        return

    excluded = {x.lower() for x in (excluded_files or [])}
    invert_pattern = False

    if pattern:
        pattern = pattern.strip()
        if pattern.startswith("!"):
            invert_pattern = True
            pattern = pattern[1:]

        files_to_consider = list(directory.glob("**/*" if pattern == "*" else pattern))
    else:
        files_to_consider = list(directory.iterdir())

    for item in files_to_consider:
        # Skip excluded names
        if item.name.lower() in excluded or item.stem.lower() in excluded:
            continue

        # If we're using inverted logic (!pattern), skip matching files
        if invert_pattern and item.match(pattern):
            continue

        if item.is_file() or item.is_symlink():
            item.unlink()
        elif item.is_dir():
            shutil.rmtree(item)

    desc = f"{'excluding' if invert_pattern else 'matching'} {pattern}" if pattern else "everything"
    print(f"🗑️  Cleared {directory} ({desc})")


def _infer_ext_from_pattern(pattern: str) -> Optional[str]:
    """
    Infer a single file extension (without dot) from a glob pattern.
    Handles '*.jpg', 'test_*.jpg', '**/*.json', 'images/*_raw.PNG'.
    Returns None if no extension can be inferred.
    """
    tail = pattern.split("/")[-1]
    if "." not in tail:
        return None
    ext = tail.rsplit(".", 1)[1].lower()
    for ch in "*?[]{}":
        ext = ext.replace(ch, "")
    ext = ext.strip()
    return ext or None


def transfer_files(
        source_dir: Path,
        dest_dir: Path,
        pattern: str = "*",
        method: Literal["copy", "move"] = "copy",
) -> Dict[str, int]:
    """
    Copy or move files matching `pattern` from `source_dir` to `dest_dir`.
    Returns { extension_without_dot: count_transferred }.
    Always prints a summary line for implied extension even if zero matched.
    """
    print("")
    summary: Dict[str, int] = {}
    dest_dir.mkdir(parents=True, exist_ok=True)

    for file in source_dir.glob(pattern):
        dest = dest_dir / file.name
        if dest.exists():
            print(f"⚠️ Skipped (already exists): {file.name}")
            continue

        if method == "move":
            shutil.move(str(file), str(dest))
            action = "Moved"
        else:
            shutil.copy(str(file), str(dest))
            action = "Copied"

        ext = file.suffix.lower().lstrip(".") or "no_ext"
        summary[ext] = summary.get(ext, 0) + 1
        print(f"✅ {action} {file.name} → {dest_dir}")

    verb = "moved" if method == "move" else "copied"
    print(f"📦 Summary of {verb} files:")

    # include any actually-seen extensions for the pattern
    all_exts = {p.suffix.lower().lstrip(".") or "no_ext" for p in source_dir.glob(pattern)}
    # include implied extension for complex patterns, even if none matched
    implied_ext = _infer_ext_from_pattern(pattern)
    if implied_ext:
        all_exts.add(implied_ext)
    if not all_exts:
        all_exts = {"no_ext"}  # explicit when nothing can be inferred

    for ext in sorted(all_exts):
        print(f"   • {ext}: {summary.get(ext, 0)}")

    return summary


def copy_files(source_dir: Path, dest_dir: Path, pattern: str = "*") -> Dict[str, int]:
    return transfer_files(source_dir, dest_dir, pattern, method="copy")


def move_files(source_dir: Path, dest_dir: Path, pattern: str = "*") -> Dict[str, int]:
    return transfer_files(source_dir, dest_dir, pattern, method="move")


def _names_in(dir_path: Path, pattern: str) -> List[str]:
    return sorted(p.name for p in dir_path.glob(pattern))


def reseed_assets() -> None:
    """
    Re-add all assets (JSON, JPG) into TEMP_DIR.
    Intended to be called before each automate_pdf.py run because it clears TEMP_DIR.
    """
    copy_files(TEST_DIR, TEMP_DIR, pattern="*.json")
    # adjust pattern as needed for your image assets
    copy_files(INCLUDES_DIR, TEMP_DIR, pattern="test_*.jpg")


def archive_pdfs(src_dir: Path, dest_subdir_name: str) -> None:
    """
    Move all PDFs from src_dir to TEST_DIR/<dest_subdir_name>.
    """
    dest_dir = TEST_DIR / dest_subdir_name
    dest_dir.mkdir(parents=True, exist_ok=True)
    for pdf in src_dir.glob("*.pdf"):
        target = dest_dir / pdf.name
        # overwrite if needed to keep runs deterministic
        if target.exists():
            target.unlink()
        shutil.move(str(pdf), str(target))


def _run_pdf_batch(
        script_path: Path,
        output_dir: Path,
        *,
        json_glob: str = "*.json",
        label: str = "Processing",
        pre_all: Optional[Callable[[], None]] = None,
        pre_each: Optional[Callable[[], None]] = None,
        archive_subdir: Optional[str] = None,
) -> None:
    """
    Run `script_path` for each JSON in TEMP_DIR and assert the PDF appears in `output_dir`.
    """
    if pre_all:
        pre_all()

    json_files = list(TEMP_DIR.glob(json_glob))
    print("")

    for json_file in json_files:
        output_pdf = output_dir / f"{json_file.stem}.pdf"
        print(f"🤖 {label} {json_file.name}")

        if pre_each:
            pre_each()

        # suppress stdout, capture stderr for debugging
        with open(os.devnull, "w") as fnull, contextlib.redirect_stdout(fnull):
            result = subprocess.run(
                ["python", str(script_path), str(json_file)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
            )

        print(f"✅ Processed {json_file.name}\n")

        assert result.returncode == 0, f"❌ PDF generation failed for {json_file.name}\n{result.stderr}"
        assert output_pdf.exists(), f"❌ PDF not created for {json_file.name}"

    # After the batch completes, optionally archive PDFs from the output directory
    if archive_subdir:
        archive_pdfs(output_dir, archive_subdir)


# === PDF Layout Comparison Utilities ===
def pdfs_layout_equal(pdf1: Path, pdf2: Path, dpi: int = 200, verbose: bool = False) -> bool:
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
                print(f"❌ Difference on page {i + 1}")
            return False
        elif verbose:
            print(f"✅ Page {i + 1} matches")

    return True


def _assert_pdf_batch_matches(actual_dir: Path, reference_dir: Path, *, verbose: bool = True) -> None:
    """
    Compare all PDFs in actual_dir to PDFs with the same filenames in reference_dir.
    Fails with a helpful summary if any are missing or mismatched.
    """
    actual_pdfs = sorted(actual_dir.glob("*.pdf"))
    print(f"\n📁 Comparing PDFs from: {actual_dir.name} →  Reference: {reference_dir.name}")
    assert actual_pdfs, f"❌ No PDFs found to compare in {actual_dir}"

    failed: list[str] = []
    missing: list[str] = []

    for pdf in actual_pdfs:
        ref = reference_dir / pdf.name
        if not ref.exists():
            print(f"⚠️  Reference PDF missing: {ref}")
            missing.append(pdf.name)
            continue

        print(f"\n🔍 Comparing: {pdf.name}")
        try:
            equal = pdfs_layout_equal(pdf, ref, verbose=verbose)
            if equal:
                print("✅ Layout matches reference.")
            else:
                print("❌ Layout differs!")
                failed.append(pdf.name)
        except Exception as e:
            print(f"❌ Error comparing PDFs: {e}")
            failed.append(pdf.name)

    if missing or failed:
        if missing:
            print("\nMissing reference PDFs:")
            for name in missing:
                print(f" - {name}")
        if failed:
            print("\nPDFs with layout differences or errors:")
            for name in failed:
                print(f" - {name}")
        total = len(missing) + len(failed)
        names = ", ".join(missing + failed)
        pytest.fail(f"❌ {total} PDF(s) failed comparison: {names}", pytrace=False)
    else:
        print("\n✅ All PDFs match their references!")


# === Tests ===
@pytest.mark.order(1)
def test_transfer_first_run_copy_json_and_images():
    """
    First run should copy all matching assets into TEMP_DIR, and they should exist there afterward.
    """
    print("\n")
    clear_dir(TEMP_DIR)
    clear_dir(directory=TEST_DIR / "generated_pdfs")
    clear_dir(directory=TEST_DIR / "automated_pdfs")


# Count expectations
    expected_json = len(list(TEST_DIR.glob("*.json")))
    expected_jpg = len(list(INCLUDES_DIR.glob("test_*.jpg")))
    assert (expected_json + expected_jpg) > 0, "Need at least one JSON or JPG asset to test."

    # Copy (non-destructive for sources)
    json_summary = copy_files(TEST_DIR, TEMP_DIR, pattern="*.json")
    jpg_summary = copy_files(INCLUDES_DIR, TEMP_DIR, pattern="test_*.jpg")

    # Counts match source
    assert json_summary.get("json", 0) == expected_json, (
        f"Expected to copy {expected_json} JSON files, copied {json_summary.get('json', 0)}."
    )
    assert jpg_summary.get("jpg", 0) == expected_jpg, (
        f"Expected to copy {expected_jpg} JPG files, copied {jpg_summary.get('jpg', 0)}."
    )

    # Files exist in TEMP_DIR
    assert len(_names_in(TEMP_DIR, "*.json")) == expected_json, "❌ Missing JSON files in temp/"
    assert len(_names_in(TEMP_DIR, "test_*.jpg")) == expected_jpg, "❌ Missing JPG files in temp/"

    print("")


@pytest.mark.order(2)
def test_transfer_second_run_is_idempotent_for_copy():
    """
    Second copy run should copy nothing new because files already exist in TEMP_DIR.
    """
    print("")
    json_summary = copy_files(TEST_DIR, TEMP_DIR, pattern="*.json")
    jpg_summary = copy_files(INCLUDES_DIR, TEMP_DIR, pattern="test_*.jpg")

    assert sum(json_summary.values()) == 0, f"❌ Expected 0 JSON copied on second run, got {json_summary}."
    assert sum(jpg_summary.values()) == 0, f"❌ Expected 0 JPG copied on second run, got {jpg_summary}."

    print("")


@pytest.mark.order(3)
def test_generate_pdfs_batch():
    """
    Run generate_pdf.py for each JSON in TEMP_DIR. PDFs are expected in TEMP_DIR.
    """

    def _pre_all():
        # Before the automated batch, ensure TEMP_DIR starts empty, then seed initial assets
        # If no server configured in CI, skip this comparison entirely
        if not os.getenv("SERVER"):
            pytest.skip("Skipping automated comparison: SERVER not configured in CI.")
        print("")

    _run_pdf_batch(
        script_path=GENERATE_PDF_SCRIPT,
        output_dir=TEMP_DIR,
        label="Generating",
        pre_all=_pre_all,
        archive_subdir="generated_pdfs",
    )


@pytest.mark.order(4)
def test_automate_pdfs_batch():
    """
    Run automate_pdf.py for each JSON in TEMP_DIR. PDFs are expected in BASE_DIR.
    Mirrors your original pre-steps.
    """

    def _pre_all():
        # Before the automated batch, ensure TEMP_DIR starts empty, then seed initial assets
        # If no server configured in CI, skip this comparison entirely
        if not os.getenv("SERVER"):
            pytest.skip("Skipping automated comparison: SERVER not configured in CI.")
        print("\n")
        clear_dir(TEMP_DIR)
        clear_dir(BASE_DIR, pattern="!*.pdf")
        reseed_assets()

    _run_pdf_batch(
        script_path=AUTOMATE_PDF_SCRIPT,
        output_dir=BASE_DIR,
        label="Automating",
        pre_all=_pre_all,
        pre_each=reseed_assets,
        archive_subdir="automated_pdfs",
    )


@pytest.mark.order(5)
def test_generated_pdfs_match_reference():
    """
    Compare PDFs created by generate_pdf.py (tests/generated_pdfs) against reference PDFs in tests/comparison (shared).
    """
    print("")
    # If no server configured in CI, skip this comparison entirely
    if not os.getenv("SERVER"):
        pytest.skip("Skipping automated comparison: SERVER not configured in CI.")
    actual_dir = TEST_DIR / "generated_pdfs"
    reference_dir = REFERENCE_DIR
    _assert_pdf_batch_matches(actual_dir, reference_dir, verbose=True)


@pytest.mark.order(6)
def test_automated_pdfs_match_reference():
    """
    Compare PDFs created by automate_pdf.py (tests/automated_pdfs) against reference PDFs in tests/comparison (shared).
    """
    print("")
    # If no server configured in CI, skip this comparison entirely
    if not os.getenv("SERVER"):
        pytest.skip("Skipping automated comparison: SERVER not configured in CI.")
    actual_dir = TEST_DIR / "automated_pdfs"
    reference_dir = REFERENCE_DIR
    _assert_pdf_batch_matches(actual_dir, reference_dir, verbose=True)
