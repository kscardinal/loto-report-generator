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
headerImage_X = page_LeftMargin
headerImage_Y = headerTitle_Y - headerImage_Height + headerTitle_LineSpacing

# Header Fields
headerField_RowSpacing = 14
headerField_Title_Font = 'Times'
headerField_Title_FontSize =10
headerField_Description_Font = 'Inter'
headerField_Description_FontSize = 10
headerField_Description_LineSpacing = 12

headerField_Address = ['Cardinal Compliance Consultants', '5353 Secor Rd.', 'Toledo, OH 43623', 'P: 419-882-9224']
headerField_AddressBlock_Font = 'Times'
headerField_AddressBlock_FontSize = 9
headerField_AddressBlock_LineSpacing = 12

headerField_Row1_Offset = 0          # Address Block
headerField_Row2_Offset = 0         # Description Row
headerField_Row3_Offset = 0         # Facility Row

headerField_Width = page_RightMargin - page_LeftMargin
headerField_TallSectoin_Width = headerImage_Width
headerField_Rev_Width = 60

headerField_H_Line1 = headerTitle_Y + headerTitle_LineSpacing
headerField_H_Line2 = headerField_H_Line1 - headerField_RowSpacing
headerField_H_Line3 = headerField_H_Line2 - (len(headerField_Address) * headerField_AddressBlock_LineSpacing + 2) - headerField_Row1_Offset
headerField_H_Line4 = headerField_H_Line3 - headerField_RowSpacing - headerField_Row2_Offset
headerField_H_Line5 = headerField_H_Line4 - headerField_RowSpacing - headerField_Row3_Offset

headerField_V_Line1 = page_LeftMargin
headerField_V_Line2 = page_LeftMargin + ((headerField_Width - headerField_TallSectoin_Width) / 2) - (headerField_Rev_Width / 2)
headerField_V_Line3 = page_RightMargin - headerField_TallSectoin_Width - headerField_Rev_Width
headerField_V_Line4 = page_RightMargin - headerField_TallSectoin_Width
headerField_V_Line5 = page_RightMargin - (headerField_TallSectoin_Width * (9/16))
headerField_V_Line6 = page_RightMargin

headerField_Row1_Text = headerField_H_Line1 - headerField_Title_FontSize
headerField_Row2_Text = headerField_H_Line3 - headerField_Title_FontSize
headerField_Row3_Text = headerField_H_Line4 - headerField_Title_FontSize

headerField_HorizonalSpacing = 5
headerField_Column1_Text = headerField_V_Line1 + headerField_HorizonalSpacing
headerField_Column2_Text = headerField_V_Line2 + headerField_HorizonalSpacing
headerField_Column3_Text = headerField_V_Line3 + headerField_HorizonalSpacing
headerField_Column4_Text = headerField_V_Line4 + headerField_HorizonalSpacing
headerField_Column5_Text = headerField_V_Line4 + (headerField_TallSectoin_Width / 2)
headerField_Column6_Text = headerField_V_Line5 + headerField_HorizonalSpacing

headerField_AddressBlock_X = headerField_Column4_Text
headerField_AddressBlock_Y = headerField_H_Line2 - headerField_Description_FontSize



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
pdf.drawImage('CardinalLogo.png', headerImage_X, headerImage_Y, headerImage_Width, headerImage_Height )

# Creating Header Field Outlines
pdf.setLineWidth(0.25)

# Horizontal Outline Lines
pdf.line(headerField_V_Line4, headerField_H_Line1, headerField_V_Line6, headerField_H_Line1)
pdf.line(headerField_V_Line4, headerField_H_Line2, headerField_V_Line6, headerField_H_Line2)
pdf.line(headerField_V_Line1, headerField_H_Line3, headerField_V_Line6, headerField_H_Line3)
pdf.line(headerField_V_Line1, headerField_H_Line4, headerField_V_Line6, headerField_H_Line4)
pdf.line(headerField_V_Line1, headerField_H_Line5, headerField_V_Line6, headerField_H_Line5)
# Vertical Outline lines
pdf.line(headerField_V_Line1, headerField_H_Line3, headerField_V_Line1, headerField_H_Line5)
pdf.line(headerField_V_Line4, headerField_H_Line1, headerField_V_Line4, headerField_H_Line5)
pdf.line(headerField_V_Line6, headerField_H_Line1, headerField_V_Line6, headerField_H_Line5)
# Vertical Divider Lines
pdf.line(headerField_V_Line2,headerField_H_Line4, headerField_V_Line2, headerField_H_Line5)
pdf.line(headerField_V_Line3,headerField_H_Line4, headerField_V_Line3, headerField_H_Line5)
pdf.line(headerField_V_Line5,headerField_H_Line4, headerField_V_Line5, headerField_H_Line5)

# Creating Header Fields Titles
pdf.setFont(headerField_Title_Font, headerField_Title_FontSize)
pdf.drawCentredString(headerField_Column5_Text, headerField_Row1_Text, 'Developed By:')
pdf.drawString(headerField_Column1_Text, headerField_Row2_Text, 'Description:')
pdf.drawString(headerField_Column1_Text, headerField_Row3_Text, 'Facility:')
pdf.drawString(headerField_Column2_Text, headerField_Row3_Text, 'Location:')
pdf.drawString(headerField_Column3_Text, headerField_Row3_Text, 'Rev:')
pdf.drawString(headerField_Column4_Text, headerField_Row2_Text, 'Procedure #:')
pdf.drawString(headerField_Column4_Text, headerField_Row3_Text, 'Date:')
pdf.drawString(headerField_Column6_Text, headerField_Row3_Text, 'Origin:')

# Creating the Address Block
pdf.setFont(headerField_AddressBlock_Font, headerField_AddressBlock_FontSize)
for line in range(0,len(headerField_Address)):
    pdf.drawString(headerField_AddressBlock_X, headerField_AddressBlock_Y - (line * headerField_AddressBlock_LineSpacing), headerField_Address[line])
    if line > 3:
        headerField_Row1_Offset += headerField_AddressBlock_LineSpacing




pdf.save()