import pytest
from pathlib import Path
import shutil
import sys
import subprocess
import os
import contextlib
from pdf2image import convert_from_path
from PIL import ImageChops
from typing import List, Optional, Dict, Literal

# === Add project root to the path ===
sys.path.append(str(Path(__file__).resolve().parents[2]))

# === Directories ===
BASE_DIR = Path(__file__).resolve().parents[2]
GENERATE_PDF_SCRIPT = Path(__file__).resolve().parents[2] / "src" / "pdf" / "generate_pdf.py"
AUTOMATE_PDF_SCRIPT = Path(__file__).resolve().parents[2] / "src" / "pdf" / "automate_pdf.py"
INCLUDES_DIR = BASE_DIR / "includes"
TEST_DIR = BASE_DIR / "src" / "tests"
TEMP_DIR = BASE_DIR / "temp"
REFERENCE_DIR = TEST_DIR / "comparison"

# === Create TEMP_DIR if it doesn't already exist ===
TEMP_DIR.mkdir(parents=True, exist_ok=True)


# === Utility: Clear Directory ===
def clear_dir(directory: Path = TEMP_DIR, excluded_files: Optional[List[str]] = None):
    excluded_files = set(f.lower() for f in excluded_files or [])

    for item in directory.iterdir():
        # Check if the file name (or stem) is excluded
        if item.name.lower() in excluded_files or item.stem.lower() in excluded_files:
            continue

        if item.is_file() or item.is_symlink():
            item.unlink()
        elif item.is_dir():
            shutil.rmtree(item)

    print(f"🗑️  Cleared {directory} (excluded: {', '.join(excluded_files) or 'none'})\n")


# === Utility: Infer Extension from Pattern ===
def _infer_ext_from_pattern(pattern: str) -> Optional[str]:
    """
    Try to infer a single file extension (without a dot) from an arbitrary glob pattern.
    Handles patterns like '*.jpg', 'test_*.jpg', '**/*.json', 'images/*_raw.PNG'.
    Returns None if an extension cannot be inferred.
    """
    # Work with the basename portion of the pattern
    tail = pattern.split("/")[-1]
    if "." not in tail:
        return None
    # Use the last '.' to identify the extension segment
    ext = tail.rsplit(".", 1)[1].lower()
    # Strip common glob characters from the extension
    for ch in "*?[]{}":
        ext = ext.replace(ch, "")
    ext = ext.strip()
    return ext or None


# === Utility: Copy or Move Files ===
def transfer_files(source_dir: Path, dest_dir: Path, pattern: str = "*", method: Literal["copy", "move"] = "copy") -> Dict[str, int]:
    """
    Copy or move files matching a pattern from source_dir to dest_dir.
    Returns a dict of file extensions (without a dot) and how many were transferred.

    Args:
        source_dir (Path): Directory to copy/move files from
        dest_dir (Path): Directory to copy/move files to
        pattern (str): Glob pattern for files to transfer (e.g. '*.pdf')
        method (Literal["copy", "move"]): Whether to 'copy' or 'move' files

    Returns:
        Dict[str, int]: Mapping of file extension (without a dot) → number transferred
    """
    summary: Dict[str, int] = {}

    if not dest_dir.exists():
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
    # Build a complete list of relevant extensions that appeared in the source_dir for this pattern
    all_exts = {p.suffix.lower().lstrip(".") or "no_ext" for p in source_dir.glob(pattern)}
    # Ensure we include the extension implied by a complex pattern like 'test_*.jpg' even if none matched
    implied_ext = _infer_ext_from_pattern(pattern)
    if implied_ext:
        all_exts.add(implied_ext)
    # If nothing at all matched, and we couldn't infer, show 'no_ext' explicitly
    if not all_exts:
        all_exts = {"no_ext"}
    for ext in sorted(all_exts):
        count = summary.get(ext, 0)
        print(f"   • {ext}: {count}")
    print("")
    return summary


# === Utility: List names in a directory matching pattern ===
def _names_in(dir_path: Path, pattern: str):
    return sorted(p.name for p in dir_path.glob(pattern))


def test_move_files_first_time_moves_all():
    """
    Verify that on a clean TEMP_DIR the first run moves all matching files from TEST_DIR to TEMP_DIR.
    Also verifies the moved files physically exist in TEMP_DIR afterward.
    """
    # New Line
    print("\n")

    # Start clean
    clear_dir(TEMP_DIR)

    # Count how many source files we expect to move
    expected_json = len(list(TEST_DIR.glob("*.json")))
    expected_jpg = len(list(INCLUDES_DIR.glob("test_*.jpg")))

    # Sanity: if there are no assets, fail fast, so the test is meaningful
    assert (expected_json + expected_jpg) > 0, "No *.json or *.jpg files present in TEST_DIR to move."

    # Perform moves (pattern-specific to collect per-ext summaries)
    json_summary = transfer_files(source_dir=TEST_DIR, dest_dir=TEMP_DIR, pattern="*.json", method="copy")
    jpg_summary = transfer_files(source_dir=INCLUDES_DIR, dest_dir=TEMP_DIR, pattern="test_*.jpg", method="copy")

    # Verify counts match what existed in TEST_DIR at the start
    assert json_summary.get("json",
                            0) == expected_json, f"❌ Expected to move {expected_json} JSON files, moved {json_summary.get('json', 0)}."
    assert jpg_summary.get("jpg",
                           0) == expected_jpg, f"❌ Expected to move {expected_jpg} JPG files, moved {jpg_summary.get('jpg', 0)}."

    # Verify files now exist in TEMP_DIR
    moved_json_names = _names_in(TEMP_DIR, "*.json")
    moved_jpg_names = _names_in(TEMP_DIR, "test_*.jpg")

    assert len(moved_json_names) == expected_json, "❌ Missing JSON files in temp/"
    assert len(moved_jpg_names) == expected_jpg, "❌ Missing JPG files in temp/"


def test_move_files_second_run_skips_existing():
    """
    Verify that running the move again skips files (nothing moved because they already exist in TEMP_DIR).
    """
    # New Line
    print("\n")

    # Run again without clearing; since files are already in TEMP_DIR, nothing should move
    json_summary = transfer_files(source_dir=TEST_DIR, dest_dir=TEMP_DIR, pattern="*.json", method="copy")
    jpg_summary = transfer_files(source_dir=INCLUDES_DIR, dest_dir=TEMP_DIR, pattern="test_*.jpg", method="copy")

    assert sum(json_summary.values()) == 0, f"❌ Expected 0 JSON moved on second run, got {json_summary}."
    assert sum(jpg_summary.values()) == 0, f"❌ Expected 0 JPG moved on second run, got {jpg_summary}."
