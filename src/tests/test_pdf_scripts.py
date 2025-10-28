import os
import sys
import shutil
import subprocess
import contextlib
from pathlib import Path
from typing import Dict, Optional, Callable, Literal, List
import pytest

# === Resolve project paths ===
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))  # if your scripts import local modules

BASE_DIR = PROJECT_ROOT
GENERATE_PDF_SCRIPT = PROJECT_ROOT / "src" / "pdf" / "generate_pdf.py"
AUTOMATE_PDF_SCRIPT = PROJECT_ROOT / "src" / "pdf" / "automate_pdf.py"
INCLUDES_DIR = PROJECT_ROOT / "includes"
TEST_DIR = PROJECT_ROOT / "src" / "tests"
TEMP_DIR = PROJECT_ROOT / "temp"

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
    print(f"🗑️  Cleared {directory} ({desc})\n")


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
    print("")
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
    print("\n")

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


# === Tests ===
@pytest.mark.order(1)
def test_transfer_first_run_copy_json_and_images():
    """
    First run should copy all matching assets into TEMP_DIR, and they should exist there afterward.
    """
    print("\n")
    clear_dir(TEMP_DIR)

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


@pytest.mark.order(2)
def test_transfer_second_run_is_idempotent_for_copy():
    """
    Second copy run should copy nothing new because files already exist in TEMP_DIR.
    """
    print("\n")
    json_summary = copy_files(TEST_DIR, TEMP_DIR, pattern="*.json")
    jpg_summary = copy_files(INCLUDES_DIR, TEMP_DIR, pattern="test_*.jpg")

    assert sum(json_summary.values()) == 0, f"❌ Expected 0 JSON copied on second run, got {json_summary}."
    assert sum(jpg_summary.values()) == 0, f"❌ Expected 0 JPG copied on second run, got {jpg_summary}."


@pytest.mark.order(3)
def test_generate_pdfs_batch():
    """
    Run generate_pdf.py for each JSON in TEMP_DIR. PDFs are expected in TEMP_DIR.
    """
    _run_pdf_batch(
        script_path=GENERATE_PDF_SCRIPT,
        output_dir=TEMP_DIR,
        label="Generating",
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