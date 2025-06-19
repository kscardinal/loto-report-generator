# pip install fillpdf
# pip install pillow
# pip install reportlab

# IMPORT FUNCTIONS
from PIL import Image
import json
import shutil
import os
from PyPDF2 import PdfReader
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
import math

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
    
def checkLength(text, max_length, add_ellipsis=False):
    if len(text) > max_length:
        return text[:max_length] + " ..." if add_ellipsis else text[:max_length]
    return text


# MAGIC Variables

# Page Setup
# 1pt = 1/72 inch
pageHeight = 792                                                # 11in
pageWidth = 612                                                  # 8.5in
pageSize = pageWidth, pageHeight
pageWidth_Middle = pageWidth / 2
pageHeight_Middle = pageHeight / 2
pageMargin = 36                                                 # 0.50in
page_LeftMargin = pageMargin
page_RightMargin = pageWidth - pageMargin

# Line Widths
defaultLineWidth = 0.25

# Header
# Header Title
headerTitle_FontSize = 18
headerTitle_Font = 'DM Serif Display'
headerTitle_LineSpacing = 20
headerTitle_Y = pageHeight - 54             # 0.75in

# Header Image
headerImage_Name = 'CardinalLogo.png'
headerImage_Width = 144                               # 2in
headerImage_Height = 72
headerImage_Height, headerImage_Width = resize_image(headerImage_Name, headerImage_Height, headerImage_Width)

# Header Fields
headerField_RowSpacing = 14
headerField_Title_Font = 'Times'
headerField_Title_FontSize =10
headerField_Description_Font = 'Inter'
headerField_Description_FontSize = 9
headerField_Description_LineSpacing = 12

headerField_Start = headerTitle_Y - (2.5 * headerTitle_LineSpacing)
headerField_Width = page_RightMargin - page_LeftMargin
headerField_TallSection_X = page_RightMargin - headerImage_Width
headerField_TallSection_Y = headerTitle_Y + headerTitle_LineSpacing
headerField_TallSection_Row2 = headerField_TallSection_Y - headerField_RowSpacing
headerField_Row2Upper = headerField_Start - headerField_RowSpacing
headerField_Row2Lower = headerField_Row2Upper - headerField_RowSpacing
headerField_RevDivider_Width = 60
headerField_RevDivider = headerField_TallSection_X - headerField_RevDivider_Width
headerField_LocationDivider = page_LeftMargin + ((headerField_Width - headerImage_Width) / 2) - (headerField_RevDivider_Width / 2)
headerField_DateDivider = page_RightMargin - (headerImage_Width / 2)

headerField_DevelopedBy_Text_Y = headerField_TallSection_Y - headerField_Title_FontSize
headerField_Row1_Text_Y = headerField_Start - headerField_Title_FontSize
headerField_Row2_Text_Y = headerField_Row2Upper - headerField_Title_FontSize
headerField_Text_Spacing = 5
headerField_Description_Text_X = page_LeftMargin + headerField_Text_Spacing
headerField_Facility_Text_X = headerField_Description_Text_X
headerField_Location_Text_X = headerField_LocationDivider + headerField_Text_Spacing
headerField_Rev_Text_X = headerField_RevDivider + headerField_Text_Spacing
headerField_Date_Text_X = headerField_TallSection_X + headerField_Text_Spacing
headerField_Origin_Text_X = headerField_DateDivider + headerField_Text_Spacing
headerField_ProcedureNumber_Text_X = headerField_TallSection_X + headerField_Text_Spacing



# Get Data
data = loadData("data_2.json")

# Creating PDF and setting document title
fileName = list(data.keys())[0]
pdf = canvas.Canvas(fileName + "_WIP.pdf", pageSize)
pdf.setTitle(list(data.keys())[0])

# Registering Fonts
pdfmetrics.registerFont(TTFont('DM Serif Display', 'DMSerifDisplay_Regular.ttf'))
pdfmetrics.registerFont(TTFont('Inter', 'Inter_Regular.ttf'))
pdfmetrics.registerFont(TTFont('Times', 'times.ttf'))

# Creating Header Title
pdf.setFont(headerTitle_Font, headerTitle_FontSize)
pdf.drawCentredString(pageWidth_Middle, headerTitle_Y, "LOCKOUT-TAGOUT")
pdf.drawCentredString(pageWidth_Middle, headerTitle_Y - headerTitle_LineSpacing, "PROCEDURE")
pdf.drawImage('CardinalLogo.png', pageMargin, headerTitle_Y - headerImage_Height + headerTitle_LineSpacing, headerImage_Width, headerImage_Height )

# Creating Header Field Outlines
pdf.setLineWidth(0.25)

# Horizontal Outline Lines
pdf.line(page_LeftMargin, headerField_Start, page_RightMargin, headerField_Start)
pdf.line(page_LeftMargin, headerField_Row2Upper, page_RightMargin, headerField_Row2Upper)
pdf.line(page_LeftMargin, headerField_Row2Lower, page_RightMargin, headerField_Row2Lower)
pdf.line(page_RightMargin, headerField_TallSection_Y, headerField_TallSection_X, headerField_TallSection_Y)
pdf.line(page_RightMargin, headerField_TallSection_Row2, headerField_TallSection_X, headerField_TallSection_Row2)
# Vertical Outline lines
pdf.line(page_LeftMargin, headerField_Start, page_LeftMargin, headerField_Row2Lower)
pdf.line(page_RightMargin, headerField_Row2Lower, page_RightMargin, headerField_TallSection_Y)
pdf.line(headerField_TallSection_X, headerField_Row2Lower, headerField_TallSection_X, headerField_TallSection_Y)
# Vertical Divider Lines
pdf.line(headerField_LocationDivider, headerField_Row2Upper, headerField_LocationDivider, headerField_Row2Lower)
pdf.line(headerField_RevDivider, headerField_Row2Upper, headerField_RevDivider, headerField_Row2Lower)
pdf.line(headerField_DateDivider, headerField_Row2Upper, headerField_DateDivider, headerField_Row2Lower)

# Creating Header Fields Titles
pdf.setFont(headerField_Title_Font, headerField_Title_FontSize)
pdf.drawCentredString(headerField_TallSection_X + (headerImage_Width / 2), headerField_DevelopedBy_Text_Y, 'Developed by:')
pdf.drawString(headerField_Description_Text_X, headerField_Row1_Text_Y, 'Description:')
pdf.drawString(headerField_Facility_Text_X, headerField_Row2_Text_Y, 'Facility:')
pdf.drawString(headerField_Location_Text_X, headerField_Row2_Text_Y, 'Location:')
pdf.drawString(headerField_Rev_Text_X, headerField_Row2_Text_Y, 'Rev:')
pdf.drawString(headerField_ProcedureNumber_Text_X, headerField_Row1_Text_Y,'Procedure #:')
pdf.drawString(headerField_Date_Text_X, headerField_Row2_Text_Y, 'Date:')
pdf.drawString(headerField_Origin_Text_X, headerField_Row2_Text_Y,'Origin:')






pdf.save()