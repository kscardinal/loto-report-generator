import json

from PIL import Image
from PyPDF2 import PdfReader


def resize_image(filename: str, max_height: float = None, max_width: float = None):
    original_width, original_height = Image.open(filename).size

    if max_height and max_width:
        width_ratio = original_width / max_width
        height_ratio = original_height / max_height

        limiting_ratio = max(width_ratio, height_ratio)

    elif max_height:
        limiting_ratio = original_height / max_height

    elif max_width:
        limiting_ratio = original_width / max_width

    else:
        return original_height, original_width

    new_width = original_width / limiting_ratio
    new_height = original_height / limiting_ratio

    return new_height, new_width


def print_error(error_message: str):
    red_color = "\033[91m"
    white_color = "\033[0m"
    print(f"{red_color}{error_message}{white_color}")


def print_success(success_message: str):
    green_color = "\033[92m"
    white_color = "\033[0m"
    print(f"{green_color}{success_message}{white_color}")


def load_data(data_file_name: str):
    try:
        with open(data_file_name, "r") as file:
            return json.load(file)
    except Exception as e:
        print_error(f"Could not load json file: {e}")


def page_count(pdf_path):
    try:
        reader = PdfReader(pdf_path)
        return len(reader.pages)
    except Exception as e:
        print_error(f"Error reading PDF file: {e}")
        return 0


def process_text(input_text: str, line_length: int, max_lines: int, return_lines: bool = False):
    words = input_text.split()
    lines = []
    current_line = []

    for word in words:
        if len(' '.join(current_line + [word])) <= line_length:
            current_line.append(word)
        else:
            lines.append(' '.join(current_line).strip())
            current_line = [word]
            if len(lines) == max_lines:
                break  # Stop if max_lines is reached

    if current_line and len(lines) < max_lines:
        lines.append(' '.join(current_line).strip())

    return lines if return_lines else len(lines)


def split_text(input_text: str, line_length: int, max_lines: int):
    return process_text(input_text, line_length, max_lines, return_lines=True)


def num_lines(input_text: str, line_length: int, max_lines: int):
    return process_text(input_text, line_length, max_lines, return_lines=False)


def check_length(text: str, max_length: int, add_ellipsis: bool = False):
    if len(text) > max_length:
        return text[:max_length] + " ..." if add_ellipsis else text[:max_length]
    return text

