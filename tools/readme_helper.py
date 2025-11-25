import os
from icecream import ic

# --- CONFIG ---
ROOT_DIR = "."  # Root directory to start from
EXCLUDE = {".git", "__pycache__", ".DS_Store", ".pytest_cache", ".venv", "node_modules",
           "__init__.py", ".pdf_cache", "automated_pdfs", "generated_pdfs", "package-lock.json", "package.json", "pyproject.toml", "uv.lock", "README.md", "LICENSE.md", ".python-version", ".gitignore", "mongo", ".idea", "comparison"}  # Files/folders to exclude
EXCLUDE_EXT = {".jpg", ".png", ".exe", ".ini", ".ttf", ".svg", ".log", ".1", ".2", ".3", ".4", ".5"}  # file extensions to exclude
OUTPUT_FILE = "readme_directory_structure.md"

# --- FUNCTION TO FIND LAST ITEM ---
def find_true_last(path):
    # Get sorted list of items, excluding unwanted files/folders
    items = sorted([item for item in os.listdir(path) if item not in EXCLUDE])
    if not items:
        return os.path.basename(path)  # empty folder

    last_item = items[-1]
    full_path = os.path.join(path, last_item)

    if os.path.isdir(full_path):
        return find_true_last(full_path)  # go deeper
    else:
        return os.path.basename(full_path)  # just the file name

TRUE_LAST = find_true_last(ROOT_DIR)

# --- FUNCTION TO GENERATE MARKDOWN TREE ---
def generate_markdown_tree(path, level=0):
    items = sorted(os.listdir(path))
    markdown_lines = []

    # Filter out excluded files/folders AND extensions
    items = [
        item for item in items
        if item not in EXCLUDE and not os.path.splitext(item)[1].lower() in EXCLUDE_EXT
    ]

    for i, item in enumerate(items):
        if item in EXCLUDE:
            continue

        full_path = os.path.join(path, item)
        is_dir = os.path.isdir(full_path)
        link_path = os.path.relpath(full_path, ROOT_DIR).replace("\\", "/")

        # Build the prefix: start with "- ├─" and add "──" for each deeper level

        if item == TRUE_LAST:
            prefix = "- └─" + "──" * level
        else:
            prefix = "- ├─" + "──" * level

        if is_dir:
            markdown_lines.append(f"{prefix} [`{item}/`]({link_path}) #")
            # Recurse into directory, increase level by 1
            markdown_lines.extend(generate_markdown_tree(full_path, level + 1))
        else:
            markdown_lines.append(f"{prefix} [`{item}`]({link_path}) #")

    return markdown_lines

# --- MAIN ---
if __name__ == "__main__":
    root_name = os.path.basename(os.path.abspath(ROOT_DIR))
    tree_lines = [f"- ├─[`{root_name}/`]({ROOT_DIR}) #"]
    tree_lines.extend(generate_markdown_tree(ROOT_DIR))

    # Write to file
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(tree_lines))

    ic(f"Markdown directory tree saved to {OUTPUT_FILE}")
    if EXCLUDE or EXCLUDE_EXT:
        ic(EXCLUDE)
        ic(EXCLUDE_EXT)
