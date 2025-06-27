# DEPENDENCIES
# pillow, reportlab, icecream

# Import Functions
from PIL import Image
import json
from PyPDF2 import PdfReader
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import math
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
    except Exception as e:
        print_error(f"Could not load json file: {e}")


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

# Default
DEFAULT_LINE_WIDTH = 0.25  # This was arbitrary but looks like what it was
DEFAULT_COLOR = [0, 0, 0]  # Black
DEFAULT_FONT = 'Inter'
DEFAULT_FONT_SIZE = 10
DEFAULT_ROW_SPACING = 14

# Data
data_file = 'data_4.json'
data = load_data(data_file)

# Creating PDF and setting document title
file_name = data_file[:-5]  # Gets data file name and strips the '.json' so we have the name of the machine
pdf = canvas.Canvas(file_name + "_WIP_2.pdf",
                    PAGE_SIZE)  # Makes the PDF with the filename from the line above and adds extension '.pdf'
pdf.setTitle(file_name)  # Sets document title. Appears only in document properties

# Registering Fonts
pdfmetrics.registerFont(TTFont('DM Serif Display', 'DMSerifDisplay_Regular.ttf'))
pdfmetrics.registerFont(TTFont('Inter', 'Inter_Regular.ttf'))
pdfmetrics.registerFont(TTFont('Times', 'times.ttf'))


# Adds Header to current page
def add_header():
    # Sets default parameters for a clean slate
    set_default()
    
    # Page Title
    page_title_font_size = 18
    page_title_font = 'DM Serif Display'
    page_title_line_spacing = 20
    page_title_y = PAGE_HEIGHT - 54  # 0.75in

    # Header Image
    image_name = 'CardinalLogo.png'
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
    description_height = num_lines(data['Description'], description_line_length,
                                                description_line_limit)

    # Header Procedure Number
    procedure_number_line_length = 16

    # Header Facility
    facility_line_length = 26
    facility_line_limit = 5
    facility_height = num_lines(data['Facility'], facility_line_length,
                                             facility_line_limit)

    # Header Location
    location_line_length = 26
    location_line_limit = 5
    location_height = num_lines(data['Location'], location_line_length,
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
    pdf.drawImage('CardinalLogo.png', image_x, image_y, image_width, image_height)

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
                       split_text(data['Description'], description_line_length,
                                  description_line_limit)[line])
    pdf.drawString(procedure_number_x, row2_text,
                   check_length(data['ProcedureNumber'], procedure_number_line_length, False))
    for line in range(facility_height):
        pdf.drawString(facility_x, row3_text - (line * body_line_spacing),
                       split_text(data['Facility'], facility_line_length, facility_line_limit)[
                           line])
    for line in range(location_height):
        pdf.drawString(location_x, row3_text - (line * body_line_spacing),
                       split_text(data['Location'], location_line_length, location_line_limit)[
                           line])
    pdf.drawString(revision_x, row3_text, data['Revision'][0:revision_line_length])
    pdf.setFont("Inter", 9)
    pdf.drawString(date_x, row3_text, data['Date'])
    pdf.drawString(origin_x, row3_text, data['Origin'])

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


def add_machine_info(import_bottom: float = PAGE_MARGIN):
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
    
    isolation_points = data.get('IsolationPoints', '0')
    if len(isolation_points) == 1:
        isolation_points_font_size = 36
    elif len(isolation_points) == 2:
        isolation_points_font_size = 28
    elif len(isolation_points) >= 3:
        isolation_points_font_size = 20
        isolation_points = isolation_points[:3]

    # Lock Tag Foratting Options
    lock_image_file = 'LockTag.png'
    lock_image_height = 40
    lock_image_width = lock_image_height
    lock_image_height, lock_image_width = resize_image(lock_image_file, lock_image_height, lock_image_width)

    # Notes Formatting Options
    notes_line_length = 60
    notes_line_limit = 5
    notes_height = num_lines(data.get('Notes', ''), notes_line_length, notes_line_limit)

    # Notes Block Height
    if (notes_height * body_line_spacing + 2) > (row_spacing * 3):
        row1_height = (notes_height * body_line_spacing + 2)  
    else:
        row1_height = (row_spacing * 3)

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
    pdf.drawImage(lock_image_file, square_right + horizontal_image_spacing, (h_line1 - ((h_line1 - h_line3) / 2)) - (lock_image_height / 2), lock_image_width, lock_image_height)

    # Isolation Points
    pdf.setFont(isolation_points_font, isolation_points_font_size)
    pdf.drawCentredString(column3_text, row3_text, isolation_points)

    # Notes Text
    pdf.setFont(body_font, body_font_size)
    notes = split_text(data.get('Notes', ''), notes_line_length, notes_line_limit)
    for line in range(len(notes)):
        pdf.drawString(column2_text, row6_text - (line * body_line_spacing), notes[line])


    ic('Adding Machine Info')
    return h_line5




bottom = add_header()
bottom = add_machine_info(bottom)
pdf.save()
