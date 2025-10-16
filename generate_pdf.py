# DEPENDENCIES
# pillow, reportlab, icecream

# Import Functions
from PIL import Image
import json
from PyPDF2 import PdfReader
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import stringWidth
import math
import sys
import os
from icecream import ic


# Resize image based on max height and/or width
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


# Error message
def print_error(error_message: str):
    red_color = "\033[91m"
    white_color = "\033[0m"
    print(f"{red_color}{error_message}{white_color}")


# Success message
def print_success(success_message: str):
    green_color = "\033[92m"
    white_color = "\033[0m"
    print(f"{green_color}{success_message}{white_color}")


# Load json/data
def load_data(data_file_name: str):
    try:
        with open(data_file_name, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        print_error(f"Error: File '{data_file_name}' not found.")
        return None
    except json.JSONDecodeError:
        print_error(f"Error: Invalid JSON format in '{data_file_name}'.")
        return None
    except Exception as e:
        print_error(f"Could not load json file: {e}")
        return None


# Get number of pages
def page_count(pdf_path):
    try:
        reader = PdfReader(pdf_path)
        return len(reader.pages)
    except Exception as e:
        print_error(f"Error reading PDF file: {e}")
        return 0


# Processes text for placement on PDF
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


# Splits text into lines
def split_text(input_text: str, line_length: int, max_lines: int):
    return process_text(input_text, line_length, max_lines, return_lines=True)


# Returns number of lines
def num_lines(input_text: str, line_length: int, max_lines: int):
    return process_text(input_text, line_length, max_lines, return_lines=False)


# Checks the length of a string and truncates it
def check_length(text: str, max_length: int, add_ellipsis: bool = False):
    if len(text) > max_length:
        return text[:max_length] + " ..." if add_ellipsis else text[:max_length]
    return text


# Set Default
def set_default():
    pdf.setFont(DEFAULT_FONT, DEFAULT_FONT_SIZE)
    pdf.setLineWidth(DEFAULT_LINE_WIDTH)
    pdf.setFillColorRGB(DEFAULT_COLOR[0], DEFAULT_COLOR[1], DEFAULT_COLOR[2])


# Check asset files exists
def check_assets():
    asset_files = [
        'includes/CardinalLogo.png',
        'includes/LockTag.png',
        'includes/Red.png',
        'includes/ImageNotFound.jpg',
        'includes/DMSerifDisplay_Regular.ttf',
        'includes/Inter_Regular.ttf',
        'includes/times.ttf',
        'includes/Pacifico.ttf'
    ]

    for file in asset_files:
        if not os.path.exists(file):
            print_error(f"Image file '{file}' does not exist.")
            return False
    return True


# Global variables for page setup and defaults

# Page dimensions (in points, 1 pt = 1/72 inch)
PAGE_HEIGHT = 792  # 11 inches
PAGE_WIDTH = 612  # 8.5 inches
PAGE_SIZE = (PAGE_WIDTH, PAGE_HEIGHT)
PAGE_MARGIN = 36  # 0.50in
PAGE_LEFT_MARGIN = PAGE_MARGIN
PAGE_RIGHT_MARGIN = PAGE_WIDTH - PAGE_MARGIN
USABLE_WIDTH = PAGE_RIGHT_MARGIN - PAGE_LEFT_MARGIN
PAGE_WIDTH_MIDDLE = PAGE_WIDTH / 2
PAGE_HEIGHT_MIDDLE = PAGE_HEIGHT / 2

SOURCE_TITLE_BLOCK_HEIGHT = 25

# Default
DEFAULT_LINE_WIDTH = 0.25  # This was arbitrary but looks like what it was
DEFAULT_COLOR = [0, 0, 0]  # Black
DEFAULT_FONT = 'Inter'
DEFAULT_FONT_SIZE = 10
DEFAULT_ROW_SPACING = 14
DEFAULT_IMAGE = "includes/ImageNotFound.jpg"



def get_json_filename():
    """Get JSON filename from command line arguments or user input"""
    if len(sys.argv) > 1:
        # Use command line argument
        json_filename = sys.argv[1]
    else:
        # Ask user for input
        json_filename = input("Enter the JSON filename (without .json extension): ").strip()
        if not json_filename.endswith('.json'):
            json_filename += '.json'

    # Validate file exists
    if not os.path.exists(json_filename):
        print_error(f"File '{json_filename}' does not exist.")
        return None

    return json_filename


def initialize_pdf_generator(data_file):
    """Initialize the PDF generator with the given data file"""
    global data, pdf, file_name

    # Load data
    data = load_data(data_file)
    if data is None:
        return False

    # Creating PDF and setting document title
    file_name = os.path.splitext(data_file)[0]  # Remove .json extension
    pdf = canvas.Canvas(file_name + ".pdf", PAGE_SIZE)
    pdf.setTitle(file_name)

    # Registering Fonts
    try:
        pdfmetrics.registerFont(TTFont('DM Serif Display', 'includes/DMSerifDisplay_Regular.ttf'))
        pdfmetrics.registerFont(TTFont('Inter', 'includes/Inter_Regular.ttf'))
        pdfmetrics.registerFont(TTFont('Times', 'includes/times.ttf'))
        pdfmetrics.registerFont(TTFont('Signature', 'includes/Pacifico.ttf'))
    except Exception as e:
        print_error(f"Error loading fonts: {e}")
        return False

    return True


# Adds First Page
def first_page() -> float:
    bottom = add_header()
    bottom = add_machine_info(bottom)
    bottom = add_shutdown_sequence(bottom)

    return bottom


# Adds new Page (Including Source Titles)
def new_page_title() -> float:
    pdf.showPage()
    bottom = add_header()
    bottom = add_source_titles(bottom)

    return bottom


# Adds new Page (Excluding Source Titles)
def new_page() -> float:
    pdf.showPage()
    bottom = add_header()

    return bottom


# Adds Header to current page
def add_header() -> float:
    # Sets default parameters for a clean slate
    set_default()

    # Page Title
    page_title_font_size = 18
    page_title_font = 'DM Serif Display'
    page_title_line_spacing = 20
    page_title_y = PAGE_HEIGHT - 54  # 0.75in

    # Header Image
    image_name = 'includes/CardinalLogo.png'
    image_width = 144  # 2in
    image_height = 72
    image_height, image_width = resize_image(image_name, image_height, image_width)
    image_x = PAGE_LEFT_MARGIN
    image_y = page_title_y - image_height + page_title_line_spacing

    # Header Field Options
    row_spacing = 14
    title_font = 'Times'
    title_font_size = 10
    body_font = 'Inter'
    body_font_size = 9
    body_line_spacing = 12

    # Header Address Block
    address = ['Cardinal Compliance Consultants', '5353 Secor Rd.', 'Toledo, OH 43623', 'P: 419-882-9224']
    address_font = 'Times'
    address_font_size = 9
    address_line_spacing = 12
    address_width = image_width

    # Header Description
    description_line_length = 78
    description_line_limit = 5
    description_height = num_lines(data.get('description', ''), description_line_length,
                                   description_line_limit)

    # Header Procedure Number
    procedure_number_line_length = 16

    # Header Facility
    facility_line_length = 26
    facility_line_limit = 5
    facility_height = num_lines(data.get('facility', ''), facility_line_length,
                                facility_line_limit)

    # Header Location
    location_line_length = 26
    location_line_limit = 5
    location_height = num_lines(data.get('location', ''), location_line_length,
                                location_line_limit)

    # Header Revision
    revision_line_length = 6
    revision_width = 60

    # Row Offset for Dynamic Data Entry
    row1_height = (len(address) * address_line_spacing + 2)  # Address Block
    row2_height = (description_height * body_line_spacing) + 2  # Description Row
    row3_height = max(facility_height,
                      location_height) * body_line_spacing + 2  # Facility Row

    # Horizontal Lines (1 = top, 5 = bottom)
    h_line1 = page_title_y + page_title_line_spacing
    h_line2 = h_line1 - row_spacing
    h_line3 = h_line2 - row1_height
    h_line4 = h_line3 - row2_height
    h_line5 = h_line4 - row3_height

    # Vertical Lines (1 = left, 6 = Right)
    v_line1 = PAGE_LEFT_MARGIN
    v_line2 = PAGE_LEFT_MARGIN + ((USABLE_WIDTH - address_width) / 2) - (
            revision_width / 2)
    v_line3 = PAGE_RIGHT_MARGIN - address_width - revision_width
    v_line4 = PAGE_RIGHT_MARGIN - address_width
    v_line5 = PAGE_RIGHT_MARGIN - (address_width * (2 / 5))
    v_line6 = PAGE_RIGHT_MARGIN

    # Text Locations - Rows
    row1_text = h_line1 - title_font_size
    row2_text = h_line3 - title_font_size
    row3_text = h_line4 - title_font_size

    # Text Locations - Columns
    horizonal_spacing = 3
    column1_text = v_line1 + horizonal_spacing
    column2_text = v_line2 + horizonal_spacing
    column3_text = v_line3 + horizonal_spacing
    column4_text = v_line4 + horizonal_spacing
    column5_text = v_line4 + (address_width / 2)
    column6_text = v_line5 + horizonal_spacing

    # Header - Address Block Locations
    address_block_x = column4_text
    address_block_y = h_line2 - body_font_size

    # Header - Description Location
    description_x = column1_text + 53

    # Header - Procedure Number Location
    procedure_number_x = column4_text + 53

    # Header - Facility Location
    facility_x = column1_text + 37

    # Header - Location
    location_x = column2_text + 42

    # Header - Revision Location
    revision_x = column3_text + 20

    # Header - Date Location
    date_x = column4_text + 23

    # Header - Origin Location
    origin_x = column6_text + 30

    # Creating Header Title
    pdf.setFont(page_title_font, page_title_font_size)
    pdf.drawCentredString(PAGE_WIDTH_MIDDLE, page_title_y, "LOCKOUT-TAGOUT")
    pdf.drawCentredString(PAGE_WIDTH_MIDDLE, page_title_y - page_title_line_spacing, "PROCEDURE")
    pdf.drawImage(image_name, image_x, image_y, image_width, image_height)

    # Creating Header Field Outlines
    pdf.setLineWidth(DEFAULT_LINE_WIDTH)

    # Horizontal Outline Lines
    pdf.line(v_line4, h_line1, v_line6, h_line1)
    pdf.line(v_line4, h_line2, v_line6, h_line2)
    pdf.line(v_line1, h_line3, v_line6, h_line3)
    pdf.line(v_line1, h_line4, v_line6, h_line4)
    pdf.line(v_line1, h_line5, v_line6, h_line5)
    # Vertical Outline lines
    pdf.line(v_line1, h_line3, v_line1, h_line5)
    pdf.line(v_line4, h_line1, v_line4, h_line5)
    pdf.line(v_line6, h_line1, v_line6, h_line5)
    # Vertical Divider Lines
    pdf.line(v_line2, h_line4, v_line2, h_line5)
    pdf.line(v_line3, h_line4, v_line3, h_line5)
    pdf.line(v_line5, h_line4, v_line5, h_line5)

    # Creating Header Fields Titles
    pdf.setFont(title_font, title_font_size)
    pdf.drawCentredString(column5_text, row1_text, 'Developed By:')
    pdf.drawString(column1_text, row2_text, 'Description:')
    pdf.drawString(column1_text, row3_text, 'Facility:')
    pdf.drawString(column2_text, row3_text, 'Location:')
    pdf.drawString(column3_text, row3_text, 'Rev:')
    pdf.drawString(column4_text, row2_text, 'Procedure #:')
    pdf.drawString(column4_text, row3_text, 'Date:')
    pdf.drawString(column6_text, row3_text, 'Origin:')

    # Creating Header Field Text
    pdf.setFont(body_font, body_font_size)
    for line in range(description_height):
        pdf.drawString(description_x, row2_text - (line * body_line_spacing),
                       split_text(data.get('description', ''), description_line_length,
                                  description_line_limit)[line])
    pdf.drawString(procedure_number_x, row2_text,
                   check_length(data.get('procedure_number', ''), procedure_number_line_length, False))
    for line in range(facility_height):
        pdf.drawString(facility_x, row3_text - (line * body_line_spacing),
                       split_text(data.get('facility', ''), facility_line_length, facility_line_limit)[
                           line])
    for line in range(location_height):
        pdf.drawString(location_x, row3_text - (line * body_line_spacing),
                       split_text(data.get('location', ''), location_line_length, location_line_limit)[
                           line])
    pdf.drawString(revision_x, row3_text, data.get('revision', '')[0:revision_line_length])
    pdf.setFont("Inter", 9)
    pdf.drawString(date_x, row3_text, data.get('date', ''))
    pdf.drawString(origin_x, row3_text, data.get('origin', ''))

    # Creating the Address Block
    pdf.setFont(address_font, address_font_size)
    for line in range(len(address)):
        pdf.drawString(address_block_x,
                       address_block_y - (line * address_line_spacing),
                       address[line])
        if line > 3:
            row1_height += address_font_size

    # Return the bottom of this section for use as start of next
    ic('Adding Header')
    return h_line5


# Adds Machine Info
def add_machine_info(import_bottom: float = PAGE_MARGIN) -> float:
    # Sets default parameters for a clean slate
    set_default()

    # Machine Info Formatting Options
    row_spacing = 14
    title_font = 'DM Serif Display'
    title_font_size = 10
    sub_title_font = 'Times'
    sub_title_font_size = 10
    body_font = 'Inter'
    body_font_size = 9
    body_line_spacing = 12

    # Square Formatting Options
    square_height = 40
    square_width = square_height

    # Isolation Points Formatting Options
    isolation_point_title_font = 'DM Serif Display'
    isolation_point_title_font_size = 16
    isolation_points_font = 'Inter'

    isolation_points = data.get('isolation_points', '0')
    if len(isolation_points) == 1:
        isolation_points_font_size = 36
    elif len(isolation_points) == 2:
        isolation_points_font_size = 28
    elif len(isolation_points) >= 3:
        isolation_points_font_size = 20
        isolation_points = isolation_points[:3]

    # Lock Tag Formatting Options
    lock_image_file = 'includes/LockTag.png'
    lock_image_height = 40
    lock_image_width = lock_image_height
    lock_image_height, lock_image_width = resize_image(lock_image_file, lock_image_height, lock_image_width)

    # Notes Formatting Options
    notes_line_length = 60
    notes_line_limit = 5
    notes_height = num_lines(data.get('notes', ''), notes_line_length, notes_line_limit)

    # Notes Block Height
    if (notes_height * body_line_spacing + 2) > (row_spacing * 3):
        row1_height = (notes_height * body_line_spacing + 2)
    else:
        row1_height = (row_spacing * 3)

    # Machine Image Formatting Options
    machine_image_file = data.get('machine_image', DEFAULT_IMAGE)
    if not os.path.isfile(machine_image_file):
        machine_image_file = DEFAULT_IMAGE

    h_line1 = import_bottom - DEFAULT_ROW_SPACING
    h_line2 = h_line1 - row_spacing
    h_line3 = h_line2 - (3.5 * row_spacing)
    h_line4 = h_line3 - row_spacing
    h_line5 = h_line4 - row1_height

    v_line1 = PAGE_LEFT_MARGIN
    v_line2 = PAGE_WIDTH_MIDDLE
    v_line3 = PAGE_RIGHT_MARGIN

    vertical_text_spacing = 3
    row1_text = h_line1 - title_font_size
    row2_text = (h_line1 - ((h_line1 - h_line3) / 2)) + (isolation_point_title_font_size / 2) - vertical_text_spacing
    row3_text = (h_line1 - ((h_line1 - h_line3) / 2)) - (isolation_points_font_size / 3)
    row4_text = (h_line1 - ((h_line1 - h_line3) / 2)) - (isolation_point_title_font_size) + vertical_text_spacing
    row5_text = h_line3 - title_font_size
    row6_text = h_line4 - title_font_size

    horizontal_text_spacing = 3
    horizontal_image_spacing = 10
    column1_text = (v_line1 + ((v_line2 - v_line1) / 2))
    column2_text = v_line2 + horizontal_text_spacing
    column3_text = v_line2 + horizontal_image_spacing + (lock_image_width / 2)
    column4_text = v_line2 + lock_image_width + square_width + (3 * horizontal_image_spacing)
    column5_text = (v_line2 + ((v_line3 - v_line2) / 2))

    # Horizontal Lines
    pdf.line(v_line1, h_line1, v_line3, h_line1)
    pdf.line(v_line1, h_line2, v_line2, h_line2)
    pdf.line(v_line2, h_line3, v_line3, h_line3)
    pdf.line(v_line2, h_line4, v_line3, h_line4)
    pdf.line(v_line1, h_line5, v_line3, h_line5)

    # Vertical Lines
    pdf.line(v_line1, h_line1, v_line1, h_line5)
    pdf.line(v_line2, h_line1, v_line2, h_line5)
    pdf.line(v_line3, h_line1, v_line3, h_line5)

    # Titles
    pdf.setFont(title_font, title_font_size)
    pdf.drawCentredString(column1_text, row1_text, 'Machine to be Locked Out')
    pdf.setFont(sub_title_font, sub_title_font_size)
    pdf.drawCentredString(column5_text, row5_text, 'Notes:')
    pdf.setFont(isolation_point_title_font, isolation_point_title_font_size)
    pdf.drawString(column4_text, row2_text, 'Isolation Points to be')
    pdf.drawString(column4_text, row4_text, 'Locked and Tagged')

    # Square
    square_left = v_line2 + horizontal_image_spacing
    square_right = square_left + square_width
    square_top = (h_line1 - ((h_line1 - h_line3) / 2)) + (square_height / 2)
    square_bottom = square_top - square_height
    pdf.line(square_left, square_top, square_right, square_top)
    pdf.line(square_right, square_top, square_right, square_bottom)
    pdf.line(square_right, square_bottom, square_left, square_bottom)
    pdf.line(square_left, square_bottom, square_left, square_top)

    # Lock Tag Image
    pdf.drawImage(lock_image_file, square_right + horizontal_image_spacing,
                  (h_line1 - ((h_line1 - h_line3) / 2)) - (lock_image_height / 2), lock_image_width, lock_image_height)

    # Isolation Points
    pdf.setFont(isolation_points_font, isolation_points_font_size)
    pdf.drawCentredString(column3_text, row3_text, isolation_points)

    # Notes Text
    pdf.setFont(body_font, body_font_size)
    notes = split_text(data.get('notes', ''), notes_line_length, notes_line_limit)
    for line in range(len(notes)):
        pdf.drawString(column2_text, row6_text - (line * body_line_spacing), notes[line])

    # Machine Image
    machine_image_max_height = h_line2 - h_line5 - row_spacing
    machine_image_max_width = v_line2 - v_line1 - row_spacing
    machine_image_height, machine_image_width = resize_image(machine_image_file, machine_image_max_height,
                                                             machine_image_max_width)
    pdf.drawImage(machine_image_file, (v_line1 + ((v_line2 - v_line1) / 2)) - (machine_image_width / 2),
                  (h_line2 - ((h_line2 - h_line5) / 2)) - (machine_image_height / 2), machine_image_width,
                  machine_image_height)

    ic('Adding Machine Info')
    return h_line5


# Add Shutdown Sequence
def add_shutdown_sequence(import_bottom: float = PAGE_MARGIN) -> float:
    # Sets default parameters for a clean slate
    set_default()

    title_font = 'DM Serif Display'
    title_font_size = 10
    title_line_spacing = 14
    title_font_color = [255, 255, 255]

    row_spacing = 14

    body_font = 'Inter'
    body_font_size = 8
    body_line_spacing = 10
    body_line_length = 135
    body_line_limit = 5
    body_background = 'includes/Red.png'

    shutdown_sequence = "1. Notify affected personnel. 2. Properly shut down machine. 3. Isolate all energy sources. 4. Apply LOTO devices. 5. Verify total de-energization of all sources."

    body_num_lines = num_lines(shutdown_sequence, body_line_length, body_line_limit)
    body_lines = split_text(shutdown_sequence, body_line_length, body_line_limit)

    total_height = title_line_spacing + body_num_lines * (body_line_spacing + 2)

    # Checking if new page is needed
    if import_bottom - total_height - DEFAULT_ROW_SPACING <= PAGE_MARGIN:
        import_bottom = new_page()

    h_line1 = import_bottom - DEFAULT_ROW_SPACING
    h_line2 = h_line1 - title_line_spacing
    h_line3 = h_line2 - body_num_lines * (body_line_spacing + 2)

    v_line1 = PAGE_LEFT_MARGIN
    v_line2 = PAGE_RIGHT_MARGIN

    # Horizontal Lines
    pdf.line(v_line1, h_line1, v_line2, h_line1)
    pdf.line(v_line1, h_line2, v_line2, h_line2)
    pdf.line(v_line1, h_line3, v_line2, h_line3)

    # Vertical Lines
    pdf.line(v_line1, h_line1, v_line1, h_line3)
    pdf.line(v_line2, h_line1, v_line2, h_line3)

    # Background color
    pdf.drawImage(body_background, v_line1, h_line2, USABLE_WIDTH, title_line_spacing)

    # Text
    column1_text = PAGE_WIDTH_MIDDLE

    row1_text = h_line1 - title_font_size
    row2_text = h_line2 - body_font_size

    # Title Text
    pdf.setFillColorRGB(title_font_color[0], title_font_color[1], title_font_color[2])
    pdf.setFont(title_font, title_font_size)
    pdf.drawCentredString(column1_text, row1_text, 'SHUTDOWN SEQUENCE')

    # Body Text
    pdf.setFillColorRGB(DEFAULT_COLOR[0], DEFAULT_COLOR[1], DEFAULT_COLOR[2])
    pdf.setFont(body_font, body_font_size)
    for line in range(body_num_lines):
        pdf.drawCentredString(column1_text, row2_text - (line * body_line_spacing), body_lines[line])

    ic('Adding Shutdown Sequence')
    return h_line3


# Add Source Title Block
def add_source_titles(import_bottom: float) -> float:
    # Sets default parameters for a clean slate
    set_default()

    title_font = 'Times'
    title_font_size = 10
    title_line_spacing = 12
    title_row_spacing = SOURCE_TITLE_BLOCK_HEIGHT

    text_block_width = (PAGE_RIGHT_MARGIN - PAGE_LEFT_MARGIN) * (2 / 14)
    image_block_width = (PAGE_RIGHT_MARGIN - PAGE_LEFT_MARGIN) * (3 / 14)

    h_line1 = import_bottom - DEFAULT_ROW_SPACING
    h_line2 = h_line1 - title_row_spacing

    v_line1 = PAGE_LEFT_MARGIN
    v_line2 = PAGE_LEFT_MARGIN + text_block_width
    v_line3 = v_line2 + text_block_width
    v_line4 = PAGE_WIDTH_MIDDLE
    v_line5 = PAGE_WIDTH_MIDDLE + text_block_width
    v_line6 = v_line5 + text_block_width
    v_line7 = PAGE_RIGHT_MARGIN

    row1_text = h_line1 - ((h_line1 - h_line2) / 2) + 2
    row2_text = h_line1 - ((h_line1 - h_line2) / 2) - 3
    row3_text = h_line1 - ((h_line1 - h_line2) / 2) - 7

    column1_text = v_line1 + (text_block_width / 2)
    column2_text = v_line2 + (text_block_width / 2)
    column3_text = v_line3 + (image_block_width / 2)
    column4_text = v_line4 + (text_block_width / 2)
    column5_text = v_line5 + (text_block_width / 2)
    column6_text = v_line6 + (image_block_width / 2)

    # Horizontal Lines
    pdf.line(v_line1, h_line1, v_line7, h_line1)
    pdf.line(v_line1, h_line2, v_line7, h_line2)

    # Vertical lines
    pdf.line(v_line1, h_line1, v_line1, h_line2)
    pdf.line(v_line2, h_line1, v_line2, h_line2)
    pdf.line(v_line3, h_line1, v_line3, h_line2)
    pdf.line(v_line4, h_line1, v_line4, h_line2)
    pdf.line(v_line5, h_line1, v_line5, h_line2)
    pdf.line(v_line6, h_line1, v_line6, h_line2)
    pdf.line(v_line7, h_line1, v_line7, h_line2)

    pdf.setFont(title_font, title_font_size)
    pdf.drawCentredString(column1_text, row2_text, 'Energy Source')
    pdf.drawCentredString(column2_text, row2_text, 'Device')
    pdf.drawCentredString(column3_text, row2_text, 'Isolation Point')
    pdf.drawCentredString(column4_text, row2_text, 'Isolation Method')
    pdf.drawCentredString(column5_text, row1_text, 'Verification')
    pdf.drawCentredString(column5_text, row3_text, 'Method')
    pdf.drawCentredString(column6_text, row2_text, 'Verification Device')

    ic('Adding Source Titles')
    return h_line2


# Add Source
def add_source(source: dict, import_bottom: float, import_height: float) -> float:
    # Sets default parameters for a clean slate
    set_default()

    # Sources Blocks
    row_spacing = 16
    body_font = "Inter"
    body_font_size = 10
    energy_source_line_spacing = 16
    device_line_spacing = 11
    isolation_method_line_spacing = 11
    verification_method_line_spacing = 11
    default_image = "includes/ImageNotFound.jpg"

    text_block_width = (PAGE_RIGHT_MARGIN - PAGE_LEFT_MARGIN) * (2 / 14)
    image_block_width = (PAGE_RIGHT_MARGIN - PAGE_LEFT_MARGIN) * (3 / 14)

    h_line1 = import_bottom
    h_line2 = h_line1 - import_height

    v_line1 = PAGE_LEFT_MARGIN
    v_line2 = PAGE_LEFT_MARGIN + text_block_width
    v_line3 = v_line2 + text_block_width
    v_line4 = PAGE_WIDTH_MIDDLE
    v_line5 = PAGE_WIDTH_MIDDLE + text_block_width
    v_line6 = v_line5 + text_block_width
    v_line7 = PAGE_RIGHT_MARGIN

    column1_text = v_line1 + (text_block_width / 2)
    column2_text = v_line2 + (text_block_width / 2)
    column3_image = v_line3 + (
            image_block_width / 2)  # Still need to subtract half the image width but that needs to happen after resizing
    column4_text = v_line4 + (text_block_width / 2)
    column5_text = v_line5 + (text_block_width / 2)
    column6_image = v_line6 + (
            image_block_width / 2)  # Still need to subtract half the image width but that needs to happen after resizing

    text_block_middle_width = h_line1 - (import_height / 2)
    image_block_middle_width = h_line1 - (import_height / 2)

    isolation_point_max_height = import_height - row_spacing
    isolation_point_max_width = (v_line4 - v_line3) - row_spacing

    verification_device_max_height = import_height - row_spacing
    verification_device_max_width = (v_line7 - v_line6) - row_spacing

    blank_text = "_____________"
    blank_text_v = "___________"
    blank_text_psi = "_________"
    blank_text_lbs = "_________"
    blank_text_temp = "________"
    blank_text_tag = "______"

    line_length = 14
    device_line_limit = 10
    description_line_limit = 10
    isolation_method_line_limit = 10
    verification_method_line_limit = 10

    # Horizontal Lines
    pdf.line(v_line1, h_line1, v_line7, h_line1)
    pdf.line(v_line1, h_line2, v_line7, h_line2)
    # Vertical Lines
    pdf.line(v_line1, h_line1, v_line1, h_line2)
    pdf.line(v_line2, h_line1, v_line2, h_line2)
    pdf.line(v_line3, h_line1, v_line3, h_line2)
    pdf.line(v_line4, h_line1, v_line4, h_line2)
    pdf.line(v_line5, h_line1, v_line5, h_line2)
    pdf.line(v_line6, h_line1, v_line6, h_line2)
    pdf.line(v_line7, h_line1, v_line7, h_line2)

    # Add Energy Source
    pdf.setFont(body_font, body_font_size)
    match source.get('energy_source', 'Other'):
        case 'Electric':
            pdf.drawCentredString(column1_text, text_block_middle_width + (energy_source_line_spacing / 2),
                                  source.get('energy_source', blank_text))
            pdf.drawCentredString(column1_text, text_block_middle_width - (energy_source_line_spacing / 2),
                                  source.get('volt', blank_text_v))
        case 'Natural Gas' | 'Steam' | 'Hydraulic' | 'Refrigerant':
            pdf.drawCentredString(column1_text, text_block_middle_width + (energy_source_line_spacing / 2),
                                  source.get('energy_source', blank_text))
            pdf.drawCentredString(column1_text, text_block_middle_width - (energy_source_line_spacing / 2),
                                  source.get('psi', blank_text_psi))
        case 'Chemical':
            pdf.drawCentredString(column1_text, text_block_middle_width + energy_source_line_spacing,
                                  source.get('energy_source', blank_text))
            pdf.drawCentredString(column1_text, text_block_middle_width, source.get('chemical_name', blank_text))
            pdf.drawCentredString(column1_text, text_block_middle_width - energy_source_line_spacing,
                                  source.get('psi', blank_text_psi))
        case 'Gravity':
            pdf.drawCentredString(column1_text, text_block_middle_width + (energy_source_line_spacing / 2),
                                  source.get('energy_source', blank_text))
            pdf.drawCentredString(column1_text, text_block_middle_width - (energy_source_line_spacing / 2),
                                  source.get('lbs', blank_text_lbs))
        case 'Thermal':
            pdf.drawCentredString(column1_text, text_block_middle_width + (energy_source_line_spacing / 2),
                                  source.get('energy_source', blank_text))
            pdf.drawCentredString(column1_text, text_block_middle_width - (energy_source_line_spacing / 2),
                                  source.get('temp', blank_text_temp))
        case 'Other':
            pdf.drawCentredString(column1_text, text_block_middle_width + (energy_source_line_spacing / 2), blank_text)
            pdf.drawCentredString(column1_text, text_block_middle_width - (energy_source_line_spacing / 2), blank_text)

    # Add Device
    pdf.setFont(body_font, body_font_size)

    device = []

    if 'device' in source:
        device_lines = split_text(source.get('device', blank_text), line_length, device_line_limit)
        for line in range(len(device_lines)):
            device.append(device_lines[line])
    else:
        device.append(blank_text)

    if "tag" in source:
        device.append('')
        device.append('Tag: #' + source.get('tag', blank_text_tag))
        device.append('')
    else:
        device.append('')
        device.append('Tag: #______')
        device.append('')

    if "source_description" in source:
        description_lines = split_text(
            source.get('source_description', blank_text),
            line_length,
            description_line_limit,
        )
        for line in range(len(description_lines)):
            device.append(description_lines[line])
    else:
        device.append(blank_text)

    if len(device) % 2 == 1:
        for line in range(len(device)):
            pdf.drawCentredString(column2_text,
                                  text_block_middle_width + (math.floor(len(device) / 2) * device_line_spacing) - (
                                          device_line_spacing * line), device[line])
    else:
        for line in range(len(device)):
            pdf.drawCentredString(column2_text, text_block_middle_width + (
                    ((math.floor(len(device) / 2) - 1) * device_line_spacing) + 5) - (device_line_spacing * line),
                                  device[line])

    # Isolation Method
    pdf.setFont(body_font, body_font_size)

    if "isolation_method" in source:
        isolation_method_num_lines = num_lines(source.get("isolation_method", ""), line_length,
                                               isolation_method_line_limit)
        isolation_method_lines = split_text(source.get("isolation_method", ""), line_length, isolation_method_line_limit)
        if isolation_method_num_lines % 2 == 1:
            for line in range(isolation_method_num_lines):
                pdf.drawCentredString(column4_text, text_block_middle_width + (
                        math.floor(isolation_method_num_lines / 2) * isolation_method_line_spacing) - (
                                              isolation_method_line_spacing * line), isolation_method_lines[line])
        else:
            for line in range(isolation_method_num_lines):
                pdf.drawCentredString(column4_text, text_block_middle_width + (
                        ((math.floor(isolation_method_num_lines / 2) - 1) * isolation_method_line_spacing) + 5) - (
                                              isolation_method_line_spacing * line), isolation_method_lines[line])
    else:
        pdf.drawCentredString(column4_text, text_block_middle_width, blank_text)

    # Verification Method
    pdf.setFont(body_font, body_font_size)

    if "verification_method" in source:
        verification_method_num_lines = num_lines(source.get("verification_method", ""), line_length,
                                                  verification_method_line_limit)
        verification_method_lines = split_text(source.get("verification_method", ""), line_length,
                                               verification_method_line_limit)
        if verification_method_num_lines % 2 == 1:
            for line in range(verification_method_num_lines):
                pdf.drawCentredString(column5_text, text_block_middle_width + (
                        math.floor(verification_method_num_lines / 2) * verification_method_line_spacing) - (
                                              verification_method_line_spacing * line),
                                      verification_method_lines[line])
        else:
            for line in range(verification_method_num_lines):
                pdf.drawCentredString(column5_text, text_block_middle_width + (((math.floor(
                    verification_method_num_lines / 2) - 1) * verification_method_line_spacing) + 5) - (
                                              verification_method_line_spacing * line),
                                      verification_method_lines[line], )
    else:
        pdf.drawCentredString(column5_text, text_block_middle_width, blank_text)

    # Isolation Point File
    isolation_point_file = source.get('isolation_point', DEFAULT_IMAGE)
    if not os.path.isfile(isolation_point_file):
        isolation_point_file = DEFAULT_IMAGE

    # Isolation Point
    isolation_point_height, isolation_point_width = resize_image(isolation_point_file,
                                                                 isolation_point_max_height, isolation_point_max_width)
    pdf.drawImage(isolation_point_file, column3_image - (isolation_point_width / 2),
                  image_block_middle_width - (isolation_point_height / 2), isolation_point_width,
                  isolation_point_height)

    # Verification Device File
    verification_device_file = source.get('verification_device', DEFAULT_IMAGE)
    if not os.path.isfile(verification_device_file):
        verification_device_file = DEFAULT_IMAGE

    # Verification Device
    verification_device_height, verification_device_width = resize_image(
        verification_device_file, verification_device_max_height, verification_device_max_width)
    pdf.drawImage(verification_device_file, column6_image - (verification_device_width / 2),
                  image_block_middle_width - (verification_device_height / 2), verification_device_width,
                  verification_device_height)

    ic('Adding Source: ' + source.get('energy_source', '') + ' : ' + source.get('tag', ''))
    return h_line2


# Adds all sources
def add_sources(import_bottom: float = PAGE_MARGIN) -> float:
    # Sets default parameters for a clean slate
    set_default()

    line_length = 14
    device_line_limit = 10
    description_line_limit = 10
    isolation_method_line_limit = 10
    verification_method_line_limit = 10

    sources = data['sources']

    for source_num in range(len(sources)):

        source = sources[source_num]

        device_height = num_lines(source.get('device', ''), line_length, device_line_limit) + 3 + num_lines(
            source.get('source_description', ''), line_length, description_line_limit)
        isolation_method_height = num_lines(source.get('isolation_method', ''), line_length, isolation_method_line_limit)
        verification_method_height = num_lines(source.get('verification_method', ''), line_length,
                                               verification_method_line_limit)

        minHeight = 110
        height = (max(device_height, isolation_method_height, verification_method_height) * 11) + 16

        if height < minHeight:
            height = minHeight

        if source_num == 0:
            if import_bottom - DEFAULT_ROW_SPACING - SOURCE_TITLE_BLOCK_HEIGHT - height <= PAGE_MARGIN:
                bottom = new_page_title()
            else:
                bottom = add_source_titles(import_bottom)
        else:
            if bottom - height <= PAGE_MARGIN:
                bottom = new_page_title()

        bottom = add_source(source, bottom, height)

    return bottom


# Add Restart Sequence
def add_restart_sequence(import_bottom: float = PAGE_MARGIN) -> float:
    # Sets default parameters for a clean slate
    set_default()

    title_font = 'DM Serif Display'
    title_font_size = 10
    title_line_spacing = 14
    title_font_color = [255, 255, 255]

    row_spacing = 14

    body_font = 'Inter'
    body_font_size = 8
    body_line_spacing = 10
    body_line_length = 135
    body_line_limit = 5
    body_background = 'includes/Green.png'

    restart_sequence = "1. Ensure all tools and items have been removed. 2. Confirm that all employees are safely located. 3. Verify that controls are in neutral. 4. Remove LOTO devices and reenergize machine. 5. Notify affected employees that servicing is complete."

    body_num_lines = num_lines(restart_sequence, body_line_length, body_line_limit)
    body_lines = split_text(restart_sequence, body_line_length, body_line_limit)

    total_height = title_line_spacing + body_num_lines * (body_line_spacing + 2)

    # Checking if new page is needed
    if import_bottom - total_height - DEFAULT_ROW_SPACING <= PAGE_MARGIN:
        import_bottom = new_page()

    h_line1 = import_bottom - DEFAULT_ROW_SPACING
    h_line2 = h_line1 - title_line_spacing
    h_line3 = h_line2 - body_num_lines * (body_line_spacing + 2)

    v_line1 = PAGE_LEFT_MARGIN
    v_line2 = PAGE_RIGHT_MARGIN

    # Horizontal Lines
    pdf.line(v_line1, h_line1, v_line2, h_line1)
    pdf.line(v_line1, h_line2, v_line2, h_line2)
    pdf.line(v_line1, h_line3, v_line2, h_line3)

    # Vertical Lines
    pdf.line(v_line1, h_line1, v_line1, h_line3)
    pdf.line(v_line2, h_line1, v_line2, h_line3)

    # Background color
    pdf.drawImage(body_background, v_line1, h_line2, USABLE_WIDTH, title_line_spacing)

    # Text
    column1_text = PAGE_WIDTH_MIDDLE

    row1_text = h_line1 - title_font_size
    row2_text = h_line2 - body_font_size

    # Title Text
    pdf.setFillColorRGB(title_font_color[0], title_font_color[1], title_font_color[2])
    pdf.setFont(title_font, title_font_size)
    pdf.drawCentredString(column1_text, row1_text, 'RESTART SEQUENCE')

    # Body Text
    pdf.setFillColorRGB(DEFAULT_COLOR[0], DEFAULT_COLOR[1], DEFAULT_COLOR[2])
    pdf.setFont(body_font, body_font_size)
    for line in range(body_num_lines):
        pdf.drawCentredString(column1_text, row2_text - (line * body_line_spacing), body_lines[line])

    ic('Adding Restart Sequence')
    return h_line3


# Add Signatures on Bottom
def add_signatures(import_bottom: float = PAGE_MARGIN) -> float:
    # Sets default parameters for a clean slate
    set_default()

    title_font = 'DM Serif Display'
    title_font_size = 10
    title_font_spacing = 12

    sub_title_font = 'Times'
    sub_title_font_size = 10
    sub_title_spacing = 12

    body_font = 'Inter'
    body_font_size = 10
    body_line_spacing = 12
    body_line_length = 108
    body_line_limit = 5

    company_line_length = 23
    company_line_limit = 4

    signature_font = 'Signature'
    signature_font_size_max = 20
    signature_font_size_min = 10
    signature_color = [0, 0, 0]
    signature_opacity = 1.0
    signature_line_length = 15

    bold_line_weight = 0.75

    description = 'The signatures below indicate that the lockout procedure covered on this sheet has been prepared by Cardinal Compliance and approved by ' + data.get(
        'approved_by', '') + '.'
    description_num_lines = num_lines(description, body_line_length, body_line_limit)
    description_lines = split_text(description, body_line_length, body_line_limit)
    description_height = (description_num_lines * body_line_spacing) + 2

    prepared_by_company = 'Cardinal Compliance Consultants, LLC'
    prepared_by_num_lines = num_lines(prepared_by_company, company_line_length, company_line_limit)
    prepared_by_lines = split_text(prepared_by_company, company_line_length, company_line_limit)
    approved_by_num_lines = num_lines(data.get('approved_by_company', ''), company_line_length, company_line_limit)
    approved_by_lines = split_text(data.get('approved_by_company', ''), company_line_length, company_line_limit)
    company_height = (max(approved_by_num_lines, prepared_by_num_lines) * body_line_spacing) + 2

    total_height = description_height + company_height + (5.5 * DEFAULT_ROW_SPACING) + (title_font_size / 2)

    # New Page Logic
    if import_bottom - total_height <= PAGE_MARGIN:
        import_bottom = new_page()

    column1_text = PAGE_LEFT_MARGIN
    column3_text = PAGE_LEFT_MARGIN + (USABLE_WIDTH * (2 / 5))
    column5_text = PAGE_LEFT_MARGIN + (USABLE_WIDTH * (4 / 5))

    row1_text = import_bottom - DEFAULT_ROW_SPACING - (title_font_size / 2)
    row2_text = row1_text - DEFAULT_ROW_SPACING
    row3_text = row2_text - description_height - DEFAULT_ROW_SPACING
    row4_text = row3_text - DEFAULT_ROW_SPACING * 1.25
    row5_text = row4_text - DEFAULT_ROW_SPACING * 1.25

    v_line1 = column1_text + 58
    v_line2 = column3_text - 10
    v_line3 = column3_text + 58
    v_line4 = column5_text - 10

    h_line1 = row3_text - 1.5
    h_line2 = row5_text - company_height

    column2_text = v_line1
    column4_text = v_line3

    # Adding Title
    pdf.setFont(title_font, title_font_size)
    pdf.drawString(column1_text, row1_text, 'Lockout Procedure Approval Data')

    # Adding Description
    pdf.setFont(body_font, body_font_size)
    for line in range(description_num_lines):
        pdf.drawString(column1_text, row2_text - (line * body_line_spacing), description_lines[line])

    # Adding Prepared By Title
    pdf.setFont(sub_title_font, sub_title_font_size)
    pdf.drawString(column1_text, row3_text, 'Prepared by: ')

    # Adding Approved By Title
    pdf.setFont(sub_title_font, sub_title_font_size)
    pdf.drawString(column3_text, row3_text, 'Approved by: ')

    # Adding Date
    pdf.setFont(sub_title_font, sub_title_font_size)
    pdf.drawString(column5_text, row3_text, 'Date: ')

    pdf.setFont(body_font, body_font_size)
    pdf.drawString(column5_text + 30, row3_text, data.get('completed_date', ''))

    # Adding Signature Lines
    pdf.setLineWidth(bold_line_weight)
    pdf.line(v_line1, h_line1, v_line2, h_line1)
    pdf.line(v_line3, h_line1, v_line4, h_line1)

    # Adding Printed Names
    pdf.setFont(body_font, body_font_size)
    if len(data.get('prepared_by', '')) > 30:
        raise Exception('Prepared By name is too long')
    else:
        pdf.drawString(column2_text, row4_text, data.get('prepared_by', ''))
    if len(data.get('approved_by', '')) > 30:
        raise Exception('Approved By name is too long')
    else:
        pdf.drawString(column4_text, row4_text, data.get('approved_by', ''))

    # Adding Company Information
    pdf.setFont(body_font, body_font_size)
    for line in range(prepared_by_num_lines):
        pdf.drawString(column2_text, row5_text - (line * body_line_spacing), prepared_by_lines[line])
    for line in range(approved_by_num_lines):
        pdf.drawString(column4_text, row5_text - (line * body_line_spacing), approved_by_lines[line])

    # Prepared By Signature
    signature_max_text_width = v_line2 - v_line1
    signature_font_size = signature_font_size_max
    while signature_font_size >= signature_font_size_min:
        text_width = stringWidth(data.get('prepared_by', ''), signature_font, signature_font_size)
        if text_width <= signature_max_text_width:
            break
        signature_font_size -= 0.5

    pdf.setFont(signature_font, signature_font_size)
    pdf.setFillColorRGB(signature_color[0], signature_color[1], signature_color[2])
    pdf.setFillAlpha(signature_opacity)
    pdf.drawString(column2_text, row3_text, data.get('prepared_by', ''))

    # Approved By Signature
    signature_max_text_width = v_line2 - v_line1
    signature_font_size = signature_font_size_max
    while signature_font_size >= signature_font_size_min:
        text_width = stringWidth(data.get('approved_by', ''), signature_font, signature_font_size)
        if text_width <= signature_max_text_width:
            break
        signature_font_size -= 0.5

    pdf.setFont(signature_font, signature_font_size)
    pdf.setFillColorRGB(signature_color[0], signature_color[1], signature_color[2])
    pdf.setFillAlpha(signature_opacity)
    pdf.drawString(column4_text, row3_text, data.get('approved_by', ''))

    ic('Adding Signatures')
    return h_line2


# Generate the PDF
def generate_pdf():
    bottom = first_page()
    bottom = add_sources(bottom)
    bottom = add_restart_sequence(bottom)
    bottom = add_signatures(bottom)

    pdf.save()


# Generate PDF from JSON data
def generate_pdf_from_json(json_data: dict, output_path: str) -> bool:
    global data, pdf, file_name
    data = json_data
    file_name = os.path.splitext(output_path)[0]
    pdf = canvas.Canvas(output_path, PAGE_SIZE)
    pdf.setTitle(file_name)

    # Register fonts
    pdfmetrics.registerFont(TTFont('DM Serif Display', 'includes/DMSerifDisplay_Regular.ttf'))
    pdfmetrics.registerFont(TTFont('Inter', 'includes/Inter_Regular.ttf'))
    pdfmetrics.registerFont(TTFont('Times', 'includes/times.ttf'))
    pdfmetrics.registerFont(TTFont('Signature', 'includes/Pacifico.ttf'))

    generate_pdf()
    return True


# Main function to run the PDF generation
def main():
    json_filename = get_json_filename()
    if not json_filename:
        sys.exit(1)

    if not initialize_pdf_generator(json_filename):
        sys.exit(1)

    generate_pdf_from_json(load_data(json_filename), json_filename.replace('.json', '.pdf'))


if __name__ == "__main__":
    main()
