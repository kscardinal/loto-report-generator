# DEPENDECIES
# pillow, reportlab, ice cream

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
def resize_image(filename, max_height=None, max_width=None):

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
def printError(errorMessage):
    redColor = "\033[91m"
    whiteColor = "\033[0m"
    print(f"{redColor}{errorMessage}{whiteColor}")

# Success message
def printSuccess(successMessage):
    greenColor = "\033[92m"
    whiteColor = "\033[0m"
    print(f"{greenColor}{successMessage}{whiteColor}")

# Load json/data
def loadData(fileName):
    try:
        with open(fileName, "r") as file:
            return json.load(file)
    except  Exception as e:
        printError(f"Could not load json file: {e}")

# Get data from json json
def getData(data, entryName):
    if entryName in data:
        return data[entryName]
    
# Get number of pages
def pageCount(pdf_path):
    try:
        reader = PdfReader(pdf_path)
        return len(reader.pages)
    except Exception as e:
        printError(f"Error reading PDF file: {e}")
        return 0

# Processes text for placement on PDF
def processText(input_text, line_length, max_lines, return_lines=False):
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
def splitText(input_text, line_length, max_lines):
    return processText(input_text, line_length, max_lines, return_lines=True)

# Returns number of lines
def numLines(input_text, line_length, max_lines):
    return processText(input_text, line_length, max_lines, return_lines=False)

# Check to see if variable exists
def checkExists(fields, field_name):
    if fields.get(field_name):
        return True
    else:
        return False
    
# Checks the length of a string and truncates it
def checkLength(text, max_length, add_ellipsis=False):
    if len(text) > max_length:
        return text[:max_length] + " ..." if add_ellipsis else text[:max_length]
    return text

# GLOBAL VARIABLES
# Page Setup
pageHeight = 792                                                # 11in (1pt = 1/72 inch)
pageWidth = 612                                                  # 8.5in
pageSize = pageWidth, pageHeight
pageWidth_Middle = pageWidth / 2
pageHeight_Middle = pageHeight / 2
pageMargin = 36                                                 # 0.50in
page_LeftMargin = pageMargin
page_RightMargin = pageWidth - pageMargin
page_MarginWidth = page_RightMargin - page_LeftMargin

# Data
dataFileName = 'data_4.json'
data = loadData(dataFileName)


# Creating PDF and setting document title
fileName = dataFileName[:-5]
pdf = canvas.Canvas(fileName + "_WIP_2.pdf", pageSize)
pdf.setTitle(fileName)


# Registering Fonts
pdfmetrics.registerFont(TTFont('DM Serif Display', 'DMSerifDisplay_Regular.ttf'))
pdfmetrics.registerFont(TTFont('Inter', 'Inter_Regular.ttf'))
pdfmetrics.registerFont(TTFont('Times', 'times.ttf'))


# Default
defaultLineWidth = 0.25
defaultColor = [0, 0, 0]                                 # Black

# Adds Header to current page
def addHeader():
    # Header Title
    header_Title_FontSize = 18
    header_Title_Font = 'DM Serif Display'
    header_Title_LineSpacing = 20
    header_Title_Y = pageHeight - 54             # 0.75in

    # Header Image
    header_Image_Name = 'CardinalLogo.png'
    header_Image_Width = 144                               # 2in
    header_Image_Height = 72
    header_Image_Height, header_Image_Width = resize_image(header_Image_Name, header_Image_Height, header_Image_Width)
    header_Image_X = page_LeftMargin
    header_Image_Y = header_Title_Y - header_Image_Height + header_Title_LineSpacing

    # Header Field Options
    header_Field_RowSpacing = 14
    header_Field_Title_Font = 'Times'
    header_Field_Title_FontSize =10
    header_Field_Body_Font = 'Inter'
    header_Field_Body_FontSize = 9
    header_Field_Body_LineSpacing = 12

    # Header Address Block
    header_Field_Address = ['Cardinal Compliance Consultants', '5353 Secor Rd.', 'Toledo, OH 43623', 'P: 419-882-9224']
    header_Field_Address_Font = 'Times'
    header_Field_Address_FontSize = 9
    header_Field_Address_LineSpacing = 12
    header_Field_Address_Width = header_Image_Width

    # Header Description
    header_Field_Description_LineLength = 78
    header_Field_Description_LineLimit = 5
    header_Field_Description_Height = numLines(data['Description'], header_Field_Description_LineLength, header_Field_Description_LineLimit)
    
    # Header Procedure Number
    header_Field_ProcedureNumber_LineLength = 16
    
    # Header Facility
    header_Field_Facility_LineLength = 26
    header_Field_Facility_LineLimit = 5
    header_Field_Facility_Height = numLines(data['Facility'], header_Field_Facility_LineLength, header_Field_Facility_LineLimit)

    # Header Location
    header_Field_Location_LineLength = 26
    header_Field_Location_LineLimit = 5
    header_Field_Location_Height = numLines(data['Location'], header_Field_Location_LineLength, header_Field_Location_LineLimit)
    
    # Header Revision
    header_Field_Revision_LineLength = 6
    header_Field_Revision_Width = 60

    # Row Offset for Dynamic Data Entry
    header_Field_Row1_Offset = (len(header_Field_Address) * header_Field_Address_LineSpacing + 2)          # Address Block
    header_Field_Row2_Offset = (header_Field_Description_Height * header_Field_Body_LineSpacing) + 2        # Description Row
    header_Field_Row3_Offset = max(header_Field_Facility_Height, header_Field_Location_Height) * header_Field_Body_LineSpacing + 2         # Facility Row

    # Horizontal Lines (1 = top, 5 = bottom)
    header_Field_H_Line1 = header_Title_Y + header_Title_LineSpacing
    header_Field_H_Line2 = header_Field_H_Line1 - header_Field_RowSpacing
    header_Field_H_Line3 = header_Field_H_Line2 - header_Field_Row1_Offset
    header_Field_H_Line4 = header_Field_H_Line3 - header_Field_Row2_Offset
    header_Field_H_Line5 = header_Field_H_Line4 - header_Field_Row3_Offset

    # Vertical Lines (1 = left, 6 = Right)
    header_Field_V_Line1 = page_LeftMargin
    header_Field_V_Line2 = page_LeftMargin + ((page_MarginWidth - header_Field_Address_Width) / 2) - (header_Field_Revision_Width / 2)
    header_Field_V_Line3 = page_RightMargin - header_Field_Address_Width - header_Field_Revision_Width
    header_Field_V_Line4 = page_RightMargin - header_Field_Address_Width
    header_Field_V_Line5 = page_RightMargin - (header_Field_Address_Width * (2 / 5))
    header_Field_V_Line6 = page_RightMargin

    # Text Locations - Rows
    header_Field_Row1_Text = header_Field_H_Line1 - header_Field_Title_FontSize
    header_Field_Row2_Text = header_Field_H_Line3 - header_Field_Title_FontSize
    header_Field_Row3_Text = header_Field_H_Line4 - header_Field_Title_FontSize

    # Text Locations - Columns
    header_Field_HorizonalSpacing = 3
    header_Field_Column1_Text = header_Field_V_Line1 + header_Field_HorizonalSpacing
    header_Field_Column2_Text = header_Field_V_Line2 + header_Field_HorizonalSpacing
    header_Field_Column3_Text = header_Field_V_Line3 + header_Field_HorizonalSpacing
    header_Field_Column4_Text = header_Field_V_Line4 + header_Field_HorizonalSpacing
    header_Field_Column5_Text = header_Field_V_Line4 + (header_Field_Address_Width / 2)
    header_Field_Column6_Text = header_Field_V_Line5 + header_Field_HorizonalSpacing

    # Header - Address Block Locations
    header_Field_AddressBlock_X = header_Field_Column4_Text
    header_Field_AddressBlock_Y = header_Field_H_Line2 - header_Field_Body_FontSize

    # Header - Description Location
    headerField_Description_X = header_Field_Column1_Text + 53

    # Header - Procedure Number Location
    headerField_ProcedureNumber_X = header_Field_Column4_Text + 53

    # Header - Facility Location
    headerField_Facility_X = header_Field_Column1_Text + 37

    # Header - Location Location
    headerField_Location_X = header_Field_Column2_Text + 42

    # Header - Revision Location
    headerField_Revision_X = header_Field_Column3_Text + 20

    # Header - Date Location
    headerField_Date_X = header_Field_Column4_Text + 23

    # Header - Origin Location
    headerField_Origin_X = header_Field_Column6_Text + 30

    # Creating Header Title
    pdf.setFont(header_Title_Font, header_Title_FontSize)
    pdf.drawCentredString(pageWidth_Middle, header_Title_Y, "LOCKOUT-TAGOUT")
    pdf.drawCentredString(pageWidth_Middle, header_Title_Y - header_Title_LineSpacing, "PROCEDURE")
    pdf.drawImage('CardinalLogo.png', header_Image_X, header_Image_Y, header_Image_Width, header_Image_Height )

    # Creating Header Field Outlines
    pdf.setLineWidth(defaultLineWidth)

    # Horizontal Outline Lines
    pdf.line(header_Field_V_Line4, header_Field_H_Line1, header_Field_V_Line6, header_Field_H_Line1)
    pdf.line(header_Field_V_Line4, header_Field_H_Line2, header_Field_V_Line6, header_Field_H_Line2)
    pdf.line(header_Field_V_Line1, header_Field_H_Line3, header_Field_V_Line6, header_Field_H_Line3)
    pdf.line(header_Field_V_Line1, header_Field_H_Line4, header_Field_V_Line6, header_Field_H_Line4)
    pdf.line(header_Field_V_Line1, header_Field_H_Line5, header_Field_V_Line6, header_Field_H_Line5)
    # Vertical Outline lines
    pdf.line(header_Field_V_Line1, header_Field_H_Line3, header_Field_V_Line1, header_Field_H_Line5)
    pdf.line(header_Field_V_Line4, header_Field_H_Line1, header_Field_V_Line4, header_Field_H_Line5)
    pdf.line(header_Field_V_Line6, header_Field_H_Line1, header_Field_V_Line6, header_Field_H_Line5)
    # Vertical Divider Lines
    pdf.line(header_Field_V_Line2,header_Field_H_Line4, header_Field_V_Line2, header_Field_H_Line5)
    pdf.line(header_Field_V_Line3,header_Field_H_Line4, header_Field_V_Line3, header_Field_H_Line5)
    pdf.line(header_Field_V_Line5,header_Field_H_Line4, header_Field_V_Line5, header_Field_H_Line5)

    # Creating Header Fields Titles
    pdf.setFont(header_Field_Title_Font, header_Field_Title_FontSize)
    pdf.drawCentredString(header_Field_Column5_Text, header_Field_Row1_Text, 'Developed By:')
    pdf.drawString(header_Field_Column1_Text, header_Field_Row2_Text, 'Description:')
    pdf.drawString(header_Field_Column1_Text, header_Field_Row3_Text, 'Facility:')
    pdf.drawString(header_Field_Column2_Text, header_Field_Row3_Text, 'Location:')
    pdf.drawString(header_Field_Column3_Text, header_Field_Row3_Text, 'Rev:')
    pdf.drawString(header_Field_Column4_Text, header_Field_Row2_Text, 'Procedure #:')
    pdf.drawString(header_Field_Column4_Text, header_Field_Row3_Text, 'Date:')
    pdf.drawString(header_Field_Column6_Text, header_Field_Row3_Text, 'Origin:')

    # Creating Header Field Text
    pdf.setFont(header_Field_Body_Font, header_Field_Body_FontSize)
    for line in range(header_Field_Description_Height):
        pdf.drawString(headerField_Description_X, header_Field_Row2_Text - (line * header_Field_Body_LineSpacing), splitText(data['Description'], header_Field_Description_LineLength, header_Field_Description_LineLimit)[line])
    pdf.drawString(headerField_ProcedureNumber_X, header_Field_Row2_Text, checkLength(data['ProcedureNumber'], header_Field_ProcedureNumber_LineLength, False))
    for line in range(header_Field_Facility_Height):
        pdf.drawString(headerField_Facility_X, header_Field_Row3_Text - (line * header_Field_Body_LineSpacing), splitText(data['Facility'], header_Field_Facility_LineLength, header_Field_Facility_LineLimit)[line])
    for line in range(header_Field_Location_Height):
        pdf.drawString(headerField_Location_X, header_Field_Row3_Text - (line * header_Field_Body_LineSpacing), splitText(data['Location'], header_Field_Location_LineLength, header_Field_Location_LineLimit)[line])
    pdf.drawString(headerField_Revision_X, header_Field_Row3_Text, data['Revision'][0:header_Field_Revision_LineLength])
    pdf.setFont("Inter", 9)
    pdf.drawString(headerField_Date_X, header_Field_Row3_Text, data['Date'])
    pdf.drawString(headerField_Origin_X, header_Field_Row3_Text, data['Origin'])

    # Creating the Address Block
    pdf.setFont(header_Field_Address_Font, header_Field_Address_FontSize)
    for line in range(len(header_Field_Address)):
        pdf.drawString(header_Field_AddressBlock_X, header_Field_AddressBlock_Y - (line * header_Field_Address_LineSpacing), header_Field_Address[line])
        if line > 3:
            header_Field_Row1_Offset += header_Field_Address_FontSize

    # Return the bottom of this section for use as start of next
    ic(data)
    return header_Field_H_Line5







addHeader()
pdf.save()