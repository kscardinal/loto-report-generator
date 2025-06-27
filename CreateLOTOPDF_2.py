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
    # Header Title
    header_title_font_size = 18
    header_title_font = 'DM Serif Display'
    header_title_line_spacing = 20
    header_title_y = PAGE_HEIGHT - 54  # 0.75in

    # Header Image
    header_image_name = 'CardinalLogo.png'
    header_image_width = 144  # 2in
    header_image_height = 72
    header_image_height, header_image_width = resize_image(header_image_name, header_image_height, header_image_width)
    header_image_x = PAGE_LEFT_MARGIN
    header_image_y = header_title_y - header_image_height + header_title_line_spacing

    # Header Field Options
    header_field_row_spacing = 14
    header_field_title_font = 'Times'
    header_field_title_font_size = 10
    header_field_body_font = 'Inter'
    header_field_body_font_size = 9
    header_field_body_line_spacing = 12

    # Header Address Block
    header_field_address = ['Cardinal Compliance Consultants', '5353 Secor Rd.', 'Toledo, OH 43623', 'P: 419-882-9224']
    header_field_address_font = 'Times'
    header_field_address_font_size = 9
    header_field_address_line_spacing = 12
    header_field_address_width = header_image_width

    # Header Description
    header_field_description_line_length = 78
    header_field_description_line_limit = 5
    header_field_description_height = num_lines(data['Description'], header_field_description_line_length,
                                                header_field_description_line_limit)

    # Header Procedure Number
    header_field_procedure_number_line_length = 16

    # Header Facility
    header_field_facility_line_length = 26
    header_field_facility_line_limit = 5
    header_field_facility_height = num_lines(data['Facility'], header_field_facility_line_length,
                                             header_field_facility_line_limit)

    # Header Location
    header_field_location_line_length = 26
    header_field_location_line_limit = 5
    header_field_location_height = num_lines(data['Location'], header_field_location_line_length,
                                             header_field_location_line_limit)

    # Header Revision
    header_field_revision_line_length = 6
    header_field_revision_width = 60

    # Row Offset for Dynamic Data Entry
    header_field_row1_offset = (len(header_field_address) * header_field_address_line_spacing + 2)  # Address Block
    header_field_row2_offset = (header_field_description_height * header_field_body_line_spacing) + 2  # Description Row
    header_field_row3_offset = max(header_field_facility_height,
                                   header_field_location_height) * header_field_body_line_spacing + 2  # Facility Row

    # Horizontal Lines (1 = top, 5 = bottom)
    header_field_h_line1 = header_title_y + header_title_line_spacing
    header_field_h_line2 = header_field_h_line1 - header_field_row_spacing
    header_field_h_line3 = header_field_h_line2 - header_field_row1_offset
    header_field_h_line4 = header_field_h_line3 - header_field_row2_offset
    header_field_h_line5 = header_field_h_line4 - header_field_row3_offset

    # Vertical Lines (1 = left, 6 = Right)
    header_field_v_line1 = PAGE_LEFT_MARGIN
    header_field_v_line2 = PAGE_LEFT_MARGIN + ((USABLE_WIDTH - header_field_address_width) / 2) - (
                header_field_revision_width / 2)
    header_field_v_line3 = PAGE_RIGHT_MARGIN - header_field_address_width - header_field_revision_width
    header_field_v_line4 = PAGE_RIGHT_MARGIN - header_field_address_width
    header_field_v_line5 = PAGE_RIGHT_MARGIN - (header_field_address_width * (2 / 5))
    header_field_v_line6 = PAGE_RIGHT_MARGIN

    # Text Locations - Rows
    header_field_row1_text = header_field_h_line1 - header_field_title_font_size
    header_field_row2_text = header_field_h_line3 - header_field_title_font_size
    header_field_row3_text = header_field_h_line4 - header_field_title_font_size

    # Text Locations - Columns
    header_field_horizonal_spacing = 3
    header_field_column1_text = header_field_v_line1 + header_field_horizonal_spacing
    header_field_column2_text = header_field_v_line2 + header_field_horizonal_spacing
    header_field_column3_text = header_field_v_line3 + header_field_horizonal_spacing
    header_field_column4_text = header_field_v_line4 + header_field_horizonal_spacing
    header_field_column5_text = header_field_v_line4 + (header_field_address_width / 2)
    header_field_column6_text = header_field_v_line5 + header_field_horizonal_spacing

    # Header - Address Block Locations
    header_field_address_block_x = header_field_column4_text
    header_field_address_block_y = header_field_h_line2 - header_field_body_font_size

    # Header - Description Location
    header_field_description_x = header_field_column1_text + 53

    # Header - Procedure Number Location
    header_field_procedure_number_x = header_field_column4_text + 53

    # Header - Facility Location
    header_field_facility_x = header_field_column1_text + 37

    # Header - Location
    header_field_location_x = header_field_column2_text + 42

    # Header - Revision Location
    header_field_revision_x = header_field_column3_text + 20

    # Header - Date Location
    header_field_date_x = header_field_column4_text + 23

    # Header - Origin Location
    header_field_origin_x = header_field_column6_text + 30

    # Creating Header Title
    pdf.setFont(header_title_font, header_title_font_size)
    pdf.drawCentredString(PAGE_WIDTH_MIDDLE, header_title_y, "LOCKOUT-TAGOUT")
    pdf.drawCentredString(PAGE_WIDTH_MIDDLE, header_title_y - header_title_line_spacing, "PROCEDURE")
    pdf.drawImage('CardinalLogo.png', header_image_x, header_image_y, header_image_width, header_image_height)

    # Creating Header Field Outlines
    pdf.setLineWidth(DEFAULT_LINE_WIDTH)

    # Horizontal Outline Lines
    pdf.line(header_field_v_line4, header_field_h_line1, header_field_v_line6, header_field_h_line1)
    pdf.line(header_field_v_line4, header_field_h_line2, header_field_v_line6, header_field_h_line2)
    pdf.line(header_field_v_line1, header_field_h_line3, header_field_v_line6, header_field_h_line3)
    pdf.line(header_field_v_line1, header_field_h_line4, header_field_v_line6, header_field_h_line4)
    pdf.line(header_field_v_line1, header_field_h_line5, header_field_v_line6, header_field_h_line5)
    # Vertical Outline lines
    pdf.line(header_field_v_line1, header_field_h_line3, header_field_v_line1, header_field_h_line5)
    pdf.line(header_field_v_line4, header_field_h_line1, header_field_v_line4, header_field_h_line5)
    pdf.line(header_field_v_line6, header_field_h_line1, header_field_v_line6, header_field_h_line5)
    # Vertical Divider Lines
    pdf.line(header_field_v_line2, header_field_h_line4, header_field_v_line2, header_field_h_line5)
    pdf.line(header_field_v_line3, header_field_h_line4, header_field_v_line3, header_field_h_line5)
    pdf.line(header_field_v_line5, header_field_h_line4, header_field_v_line5, header_field_h_line5)

    # Creating Header Fields Titles
    pdf.setFont(header_field_title_font, header_field_title_font_size)
    pdf.drawCentredString(header_field_column5_text, header_field_row1_text, 'Developed By:')
    pdf.drawString(header_field_column1_text, header_field_row2_text, 'Description:')
    pdf.drawString(header_field_column1_text, header_field_row3_text, 'Facility:')
    pdf.drawString(header_field_column2_text, header_field_row3_text, 'Location:')
    pdf.drawString(header_field_column3_text, header_field_row3_text, 'Rev:')
    pdf.drawString(header_field_column4_text, header_field_row2_text, 'Procedure #:')
    pdf.drawString(header_field_column4_text, header_field_row3_text, 'Date:')
    pdf.drawString(header_field_column6_text, header_field_row3_text, 'Origin:')

    # Creating Header Field Text
    pdf.setFont(header_field_body_font, header_field_body_font_size)
    for line in range(header_field_description_height):
        pdf.drawString(header_field_description_x, header_field_row2_text - (line * header_field_body_line_spacing),
                       split_text(data['Description'], header_field_description_line_length,
                                  header_field_description_line_limit)[line])
    pdf.drawString(header_field_procedure_number_x, header_field_row2_text,
                   check_length(data['ProcedureNumber'], header_field_procedure_number_line_length, False))
    for line in range(header_field_facility_height):
        pdf.drawString(header_field_facility_x, header_field_row3_text - (line * header_field_body_line_spacing),
                       split_text(data['Facility'], header_field_facility_line_length, header_field_facility_line_limit)[
                           line])
    for line in range(header_field_location_height):
        pdf.drawString(header_field_location_x, header_field_row3_text - (line * header_field_body_line_spacing),
                       split_text(data['Location'], header_field_location_line_length, header_field_location_line_limit)[
                           line])
    pdf.drawString(header_field_revision_x, header_field_row3_text, data['Revision'][0:header_field_revision_line_length])
    pdf.setFont("Inter", 9)
    pdf.drawString(header_field_date_x, header_field_row3_text, data['Date'])
    pdf.drawString(header_field_origin_x, header_field_row3_text, data['Origin'])

    # Creating the Address Block
    pdf.setFont(header_field_address_font, header_field_address_font_size)
    for line in range(len(header_field_address)):
        pdf.drawString(header_field_address_block_x,
                       header_field_address_block_y - (line * header_field_address_line_spacing),
                       header_field_address[line])
        if line > 3:
            header_field_row1_offset += header_field_address_font_size

    # Return the bottom of this section for use as start of next
    ic(data)
    return header_field_h_line5


add_header()
pdf.save()
