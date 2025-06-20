# pip install pillow
# pip install reportlab

# Import Functions
from PIL import Image
import json
from PyPDF2 import PdfReader
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

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

# Default
defaultLineWidth = 0.25
defaultColor = [0, 0, 0]

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

headerField_Row1_Offset = (len(headerField_Address) * headerField_AddressBlock_LineSpacing + 2)          # Address Block
headerField_Row2_Offset = 0         # Description Row
headerField_Row3_Offset = 0         # Facility Row

headerField_Width = page_RightMargin - page_LeftMargin
headerField_TallSectoin_Width = headerImage_Width
headerField_Rev_Width = 60

headerField_H_Line1 = headerTitle_Y + headerTitle_LineSpacing
headerField_H_Line2 = headerField_H_Line1 - headerField_RowSpacing
headerField_H_Line3 = headerField_H_Line2 - headerField_Row1_Offset
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


# Machine Information Fields
machineField_RowSpacing = 14
machineField_Title_Font = 'DM Serif Display'
machineField_Title_FontSize = 10
machineField_Title_LineSpacing = 12

machineField_LargeText_Font = 'DM Serif Display'
machineField_LargeText_FontSize = 16
machineField_LargeText_LineSpacing = 20

machineField_LockImage = 'LockTag.png'

machineField_Row1_Offset = 0        # Notes Field

machineField_Width = page_RightMargin - page_LeftMargin

machineField_H_Line1 = headerField_H_Line5 - machineField_RowSpacing
machineField_H_Line2 = machineField_H_Line1 - machineField_RowSpacing
machineField_H_Line3 = machineField_H_Line2 - (2 * machineField_Title_LineSpacing) - (2 * machineField_LargeText_FontSize)
machineField_H_Line4 = machineField_H_Line3 - machineField_RowSpacing
machineField_H_Line5 = machineField_H_Line4 - (machineField_Title_FontSize * 4) - machineField_Row1_Offset

machineField_V_Line1 = page_LeftMargin
machineField_V_Line2 = pageWidth_Middle
machineField_V_Line3 = page_RightMargin

machineField_Row1_Text = machineField_H_Line1 - machineField_Title_FontSize
machineField_Row2_Text = machineField_H_Line2 - machineField_RowSpacing
machineField_Row3_Text = machineField_Row2_Text - machineField_LargeText_LineSpacing
machineField_Row4_Text = machineField_H_Line3 - machineField_Title_FontSize

machineField_HorizontalSpacing = 10

machineField_SquareSize = 40
machineField_Square_Top = machineField_H_Line1 - ((machineField_H_Line1 - machineField_H_Line3) / 2) + (machineField_SquareSize / 2)
machineField_Square_Bottom = machineField_H_Line1 - ((machineField_H_Line1 - machineField_H_Line3) / 2) - (machineField_SquareSize / 2)
machineField_Square_Left = machineField_V_Line2 + machineField_HorizontalSpacing
machineField_Square_Right = machineField_Square_Left + machineField_SquareSize

machineField_LockImage_Height = 40
machineField_LockImage_Width = machineField_LockImage_Height
machineField_LockImage_X = machineField_Square_Right + machineField_HorizontalSpacing
machineField_LockImage_Y = machineField_H_Line1 - ((machineField_H_Line1 - machineField_H_Line3) / 2) - (machineField_LockImage_Height / 2)

machineField_Column1_Text = page_LeftMargin + ((machineField_Width / 2) / 2)
machineField_Column2_Text = machineField_LockImage_X + machineField_LockImage_Width + machineField_HorizontalSpacing
machineField_Column3_Text = page_RightMargin - ((machineField_Width / 2) / 2)


# Shutdown Fields
shutdownField_RowSpacing = 14
shutdownField_Title_Font = 'DM Serif Display'
shutdownField_Title_FontSize = 10
shutdownField_Title_LineSpacing = 12
shutdownField_Title_Color = [255, 255, 255]

shutdownField_Description_Font = 'Inter'
shutdownField_Description_FontSize = 8
shutdownField_Description_LineSpacing = 10
shutdownField_Description_LineLength = 135
shutdownField_Description_MaxLines = 5
shutdownField_Description = "1. Notify affecte personnel. 2. Properly shut down machine. 3. Isolate all energy sources. 4. Apply LOTO devices. 5. Verify total de-enrgization of all sources."

shutdownField_Row1_Offset = (numLines(shutdownField_Description, shutdownField_Description_LineLength, shutdownField_Description_MaxLines) * shutdownField_Description_LineSpacing + 2)           # Shutdown Sequence Instrutions

shutdownField_Background = 'Red.png'

shutdownField_Width = page_RightMargin - page_LeftMargin

shutdownField_H_Line1 = machineField_H_Line5 - shutdownField_RowSpacing
shutdownField_H_Line2 = shutdownField_H_Line1 - shutdownField_RowSpacing
shutdownField_H_Line3 = shutdownField_H_Line2 - shutdownField_Row1_Offset

shutdownField_V_Line1 = page_LeftMargin
shutdownField_V_Line2 = page_RightMargin

shutdownField_Row1_Text = shutdownField_H_Line1 - shutdownField_Title_FontSize
shutdownField_Row2_Text = shutdownField_H_Line2 - shutdownField_Description_FontSize

shutdownField_Column1_Text = pageWidth_Middle



# Sources Title Block
sourceTitleField_RowSpacing = 25
sourceTitleField_Title_Font = 'Times'
sourceTitleField_Title_FontSize = 10
sourceTitleField_Title_LineSpacing = 12

sourceTitleField_TextBlock = (page_RightMargin - page_LeftMargin) * (2 / 14)
sourceTitleField_ImageBlock = (page_RightMargin - page_LeftMargin) * (3 / 14)

sourceTitleField_H_Line1 = shutdownField_H_Line3 - shutdownField_RowSpacing
sourceTitleField_H_Line2 = sourceTitleField_H_Line1 - sourceTitleField_RowSpacing

sourceTitleField_V_Line1 = page_LeftMargin
sourceTitleField_V_Line2 = page_LeftMargin + sourceTitleField_TextBlock
sourceTitleField_V_Line3 = sourceTitleField_V_Line2 + sourceTitleField_TextBlock
sourceTitleField_V_Line4 = pageWidth_Middle
sourceTitleField_V_Line5 = pageWidth_Middle + sourceTitleField_TextBlock
sourceTitleField_V_Line6 = sourceTitleField_V_Line5 + sourceTitleField_TextBlock
sourceTitleField_V_Line7 = page_RightMargin

sourceTitleField_Row1_Text = sourceTitleField_H_Line1 - ((sourceTitleField_H_Line1 - sourceTitleField_H_Line2) / 2) + 2
sourceTitleField_Row2_Text = sourceTitleField_H_Line1 - ((sourceTitleField_H_Line1 - sourceTitleField_H_Line2) / 2) - 3
sourceTitleField_Row3_Text = sourceTitleField_H_Line1 - ((sourceTitleField_H_Line1 - sourceTitleField_H_Line2) / 2) - 7

sourceTitleField_Column1_Text = sourceTitleField_V_Line1 + (sourceTitleField_TextBlock / 2)
sourceTitleField_Column2_Text = sourceTitleField_V_Line2 + (sourceTitleField_TextBlock / 2)
sourceTitleField_Column3_Text = sourceTitleField_V_Line3 + (sourceTitleField_ImageBlock / 2)
sourceTitleField_Column4_Text = sourceTitleField_V_Line4 + (sourceTitleField_TextBlock / 2)
sourceTitleField_Column5_Text = sourceTitleField_V_Line5 + (sourceTitleField_TextBlock / 2)
sourceTitleField_Column6_Text = sourceTitleField_V_Line6 + (sourceTitleField_ImageBlock / 2)




# Adds Header to current page
def addHeader():
    # Creating Header Title
    pdf.setFont(headerTitle_Font, headerTitle_FontSize)
    pdf.drawCentredString(pageWidth_Middle, headerTitle_Y, "LOCKOUT-TAGOUT")
    pdf.drawCentredString(pageWidth_Middle, headerTitle_Y - headerTitle_LineSpacing, "PROCEDURE")
    pdf.drawImage('CardinalLogo.png', headerImage_X, headerImage_Y, headerImage_Width, headerImage_Height )

    # Creating Header Field Outlines
    pdf.setLineWidth(defaultLineWidth)

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
            headerField_Row1_Offset += headerField_AddressBlock_FontSize

# Adds Machine Information to current page
def addMachineInfo():
    # Create Machine Field Outlintes
    pdf.setLineWidth(defaultLineWidth)

    # Horizontal Lines
    pdf.line(machineField_V_Line1, machineField_H_Line1, machineField_V_Line3, machineField_H_Line1)
    pdf.line(machineField_V_Line1, machineField_H_Line2, machineField_V_Line2, machineField_H_Line2)
    pdf.line(machineField_V_Line2, machineField_H_Line3, machineField_V_Line3, machineField_H_Line3)
    pdf.line(machineField_V_Line2, machineField_H_Line4, machineField_V_Line3, machineField_H_Line4)
    pdf.line(machineField_V_Line1, machineField_H_Line5, machineField_V_Line3, machineField_H_Line5)
    # Vertical Lines
    pdf.line(machineField_V_Line1, machineField_H_Line1, machineField_V_Line1, machineField_H_Line5)
    pdf.line(machineField_V_Line2, machineField_H_Line1, machineField_V_Line2, machineField_H_Line5)
    pdf.line(machineField_V_Line3, machineField_H_Line1, machineField_V_Line3, machineField_H_Line5)

    # Creating Machine Fields Titles
    pdf.setFont(machineField_Title_Font, machineField_Title_FontSize)
    pdf.drawCentredString(machineField_Column1_Text, machineField_Row1_Text, 'Machine to be Locked Out')
    pdf.drawCentredString(machineField_Column3_Text, machineField_Row4_Text, 'Notes:')

    pdf.setFont(machineField_LargeText_Font, machineField_LargeText_FontSize)
    pdf.drawString(machineField_Column2_Text, machineField_Row2_Text, 'Isolation Points to be')
    pdf.drawString(machineField_Column2_Text, machineField_Row3_Text, 'Locked and Tagged')

    # Place Lock Tag Image
    pdf.drawImage(machineField_LockImage, machineField_LockImage_X, machineField_LockImage_Y, machineField_LockImage_Width, machineField_LockImage_Height)

    # Place Square
    pdf.line(machineField_Square_Left, machineField_Square_Top, machineField_Square_Right, machineField_Square_Top)
    pdf.line(machineField_Square_Left, machineField_Square_Bottom, machineField_Square_Right, machineField_Square_Bottom)
    pdf.line(machineField_Square_Left, machineField_Square_Top, machineField_Square_Left, machineField_Square_Bottom)
    pdf.line(machineField_Square_Right, machineField_Square_Top, machineField_Square_Right, machineField_Square_Bottom)

# Add Shutdown Information to current page
def addShutdownInfo():
    # Creating the Shutdown Fields
    pdf.setLineWidth(defaultLineWidth)

    # Horizontal Lines
    pdf.line(shutdownField_V_Line1, shutdownField_H_Line1, shutdownField_V_Line2, shutdownField_H_Line1)
    pdf.line(shutdownField_V_Line1, shutdownField_H_Line2, shutdownField_V_Line2, shutdownField_H_Line2)
    pdf.line(shutdownField_V_Line1, shutdownField_H_Line3, shutdownField_V_Line2, shutdownField_H_Line3)
    # Vertical Lines
    pdf.line(shutdownField_V_Line1, shutdownField_H_Line1, shutdownField_V_Line1, shutdownField_H_Line3)
    pdf.line(shutdownField_V_Line2, shutdownField_H_Line1, shutdownField_V_Line2, shutdownField_H_Line3)

    # Add Red
    pdf.drawImage(shutdownField_Background, shutdownField_V_Line1, shutdownField_H_Line2, shutdownField_Width, shutdownField_RowSpacing)

    # Add Shutdown Field Titles / Descriptions
    pdf.setFillColorRGB(shutdownField_Title_Color[0], shutdownField_Title_Color[1], shutdownField_Title_Color[2])
    pdf.setFont(shutdownField_Title_Font, shutdownField_Title_FontSize)
    pdf.drawCentredString(shutdownField_Column1_Text, shutdownField_Row1_Text, 'SHUTDOWN SEQUENCE')

    pdf.setFillColorRGB(defaultColor[0], defaultColor[1], defaultColor[2])
    pdf.setFont(shutdownField_Description_Font, shutdownField_Description_FontSize)
    for line in range(0, numLines(shutdownField_Description, 135, 5)):
        pdf.drawCentredString(shutdownField_Column1_Text, shutdownField_Row2_Text - (line * shutdownField_Description_LineSpacing), splitText(shutdownField_Description, 135, 5)[line])
        if line > 1:
            shutdownField_Row1_Offset += shutdownField_Description_FontSize

# Add Soruce Titles to current page
def addSourceTitles(newStartingYPos=sourceTitleField_H_Line1):
    # Creating Source Title Row
    pdf.setLineWidth(defaultLineWidth)

    sourceTitleField_H_Line1 = newStartingYPos
    sourceTitleField_H_Line2 = sourceTitleField_H_Line1 - sourceTitleField_RowSpacing
    sourceTitleField_Row1_Text = sourceTitleField_H_Line1 - ((sourceTitleField_H_Line1 - sourceTitleField_H_Line2) / 2) + 2
    sourceTitleField_Row2_Text = sourceTitleField_H_Line1 - ((sourceTitleField_H_Line1 - sourceTitleField_H_Line2) / 2) - 3
    sourceTitleField_Row3_Text = sourceTitleField_H_Line1 - ((sourceTitleField_H_Line1 - sourceTitleField_H_Line2) / 2) - 7

    # Horizontal Lines
    pdf.line(sourceTitleField_V_Line1, sourceTitleField_H_Line1, sourceTitleField_V_Line7, sourceTitleField_H_Line1)
    pdf.line(sourceTitleField_V_Line1, sourceTitleField_H_Line2, sourceTitleField_V_Line7, sourceTitleField_H_Line2)
    # Vertical Lines
    pdf.line(sourceTitleField_V_Line1, sourceTitleField_H_Line1, sourceTitleField_V_Line1, sourceTitleField_H_Line2)
    pdf.line(sourceTitleField_V_Line7, sourceTitleField_H_Line1, sourceTitleField_V_Line7, sourceTitleField_H_Line2)
    # Vertical Dividers
    pdf.line(sourceTitleField_V_Line2, sourceTitleField_H_Line1, sourceTitleField_V_Line2, sourceTitleField_H_Line2)
    pdf.line(sourceTitleField_V_Line3, sourceTitleField_H_Line1, sourceTitleField_V_Line3, sourceTitleField_H_Line2)
    pdf.line(sourceTitleField_V_Line4, sourceTitleField_H_Line1, sourceTitleField_V_Line4, sourceTitleField_H_Line2)
    pdf.line(sourceTitleField_V_Line5, sourceTitleField_H_Line1, sourceTitleField_V_Line5, sourceTitleField_H_Line2)
    pdf.line(sourceTitleField_V_Line6, sourceTitleField_H_Line1, sourceTitleField_V_Line6, sourceTitleField_H_Line2)

    # Add Source Title Fields
    pdf.setFont(sourceTitleField_Title_Font, sourceTitleField_Title_FontSize)

    pdf.drawCentredString(sourceTitleField_Column1_Text, sourceTitleField_Row2_Text, 'Energy Source')
    pdf.drawCentredString(sourceTitleField_Column2_Text, sourceTitleField_Row2_Text, 'Device')
    pdf.drawCentredString(sourceTitleField_Column3_Text, sourceTitleField_Row2_Text, 'Isolation Point')
    pdf.drawCentredString(sourceTitleField_Column4_Text, sourceTitleField_Row2_Text, 'Isolation Method')
    pdf.drawCentredString(sourceTitleField_Column5_Text, sourceTitleField_Row1_Text, 'Verification')
    pdf.drawCentredString(sourceTitleField_Column5_Text, sourceTitleField_Row3_Text, 'Method')
    pdf.drawCentredString(sourceTitleField_Column6_Text, sourceTitleField_Row2_Text, 'Verification Device')

    return sourceTitleField_H_Line2

def addSource(import_bottom, import_height):
    # Sources Blocks
    sourceField_RowSpacing = 14
    sourceField_Description_Font = 'Inter'
    sourceField_Description_FontSize = 10
    sourceField_Description_FontSpacing = 16

    sourceField_TextBlock_Width = sourceTitleField_TextBlock
    sourceField_ImageBlock_Width = sourceTitleField_ImageBlock

    sourceField_H_Line1 = import_bottom
    sourceField_H_Line2 = sourceField_H_Line1 - import_height

    sourceField_V_Line1 = sourceTitleField_V_Line1
    sourceField_V_Line2 = sourceTitleField_V_Line2
    sourceField_V_Line3 = sourceTitleField_V_Line3
    sourceField_V_Line4 = sourceTitleField_V_Line4
    sourceField_V_Line5 = sourceTitleField_V_Line5
    sourceField_V_Line6 = sourceTitleField_V_Line6
    sourceField_V_Line7 = sourceTitleField_V_Line7

    sourceField_Middle_Text = sourceField_H_Line1 - (import_height / 2)

    sourceField_Column1_Text = sourceTitleField_Column1_Text
    sourceField_Column2_Text = sourceTitleField_Column2_Text
    sourceField_Column3_Text = sourceTitleField_Column3_Text
    sourceField_Column4_Text = sourceTitleField_Column4_Text
    sourceField_Column5_Text = sourceTitleField_Column5_Text
    sourceField_Column6_Text = sourceTitleField_Column6_Text


    # Horizontal Lines
    pdf.line(sourceField_V_Line1, sourceField_H_Line2, sourceField_V_Line7, sourceField_H_Line2)
    # Vertical Lines
    pdf.line(sourceField_V_Line1, sourceField_H_Line1, sourceField_V_Line1, sourceField_H_Line2)
    pdf.line(sourceField_V_Line7, sourceField_H_Line1, sourceField_V_Line7, sourceField_H_Line2)
    # Vertical Divider Lines
    pdf.line(sourceField_V_Line2, sourceField_H_Line1, sourceField_V_Line2, sourceField_H_Line2)
    pdf.line(sourceField_V_Line3, sourceField_H_Line1, sourceField_V_Line3, sourceField_H_Line2)
    pdf.line(sourceField_V_Line4, sourceField_H_Line1, sourceField_V_Line4, sourceField_H_Line2)
    pdf.line(sourceField_V_Line5, sourceField_H_Line1, sourceField_V_Line5, sourceField_H_Line2)
    pdf.line(sourceField_V_Line6, sourceField_H_Line1, sourceField_V_Line6, sourceField_H_Line2)

    # Energy Source
    pdf.setFont(sourceField_Description_Font, sourceField_Description_FontSize)
    match source_value.get("EnergySource"):
        case "Electric":
            pdf.drawCentredString(sourceField_Column1_Text,  sourceField_Middle_Text + (sourceField_Description_FontSpacing / 2),  source_value.get("EnergySource"))
            pdf.drawCentredString(sourceField_Column1_Text, sourceField_Middle_Text - (sourceField_Description_FontSpacing / 2), source_value.get("VOLTS") + " V")
        case "Natural Gas" | "Steam" | "Hydraulic" | "Regrigerant":
            pdf.drawCentredString(sourceField_Column1_Text,  sourceField_Middle_Text + (sourceField_Description_FontSpacing / 2),  source_value.get("EnergySource"))
            pdf.drawCentredString(sourceField_Column1_Text, sourceField_Middle_Text - (sourceField_Description_FontSpacing / 2), source_value.get("S1_PSI") + " PSI")
        case "Chemical":
            pdf.drawCentredString(sourceField_Column1_Text,  sourceField_Middle_Text + sourceField_Description_FontSpacing,  source_value.get("EnergySource"))
            pdf.drawCentredString(sourceField_Column1_Text, sourceField_Middle_Text, source_value.get("ChemicalName"))
            pdf.drawCentredString(sourceField_Column1_Text, sourceField_Middle_Text - sourceField_Description_FontSpacing, source_value.get("PSI") + " PSI")
        case "Gravity":
            pdf.drawCentredString(sourceField_Column1_Text,  sourceField_Middle_Text + (sourceField_Description_FontSpacing / 2),  source_value.get("EnergySource"))
            pdf.drawCentredString(sourceField_Column1_Text, sourceField_Middle_Text - (sourceField_Description_FontSpacing / 2), source_value.get("LBS") + " lbs")
        case "Thermal":
            pdf.drawCentredString(sourceField_Column1_Text,  sourceField_Middle_Text + (sourceField_Description_FontSpacing / 2),  source_value.get("EnergySource"))
            pdf.drawCentredString(sourceField_Column1_Text, sourceField_Middle_Text - (sourceField_Description_FontSpacing / 2), source_value.get("TEMP") + " F")







    return sourceField_H_Line2

# Creates the template on the first page
def firstPage():
    addHeader()
    addMachineInfo()
    addShutdownInfo()
    bottom = addSourceTitles()
    return bottom

# Creates the template for a new page
def newPage():
    pdf.showPage()
    addHeader()
    bottom = addSourceTitles(headerField_H_Line5 - headerField_RowSpacing)
    return bottom

# Get Data
data = loadData("data_3.json")

# Creating PDF and setting document title
fileName = list(data.keys())[0]
pdf = canvas.Canvas(fileName + "_WIP.pdf", pageSize)
pdf.setTitle(list(data.keys())[0])

# Registering Fonts
pdfmetrics.registerFont(TTFont('DM Serif Display', 'DMSerifDisplay_Regular.ttf'))
pdfmetrics.registerFont(TTFont('Inter', 'Inter_Regular.ttf'))
pdfmetrics.registerFont(TTFont('Times', 'times.ttf'))

bottom = firstPage()

# Iterate through all top-level keys and their values
for device_name, device_data in data.items():
    if "Sources" in device_data:  # Check if the "Sources" key exists
        print(f"Device Name: {device_name}")
        sources = device_data["Sources"]

        # Iterate through the sources
        for source_name, source_value in sources.items():
            print(f"Source Name: {source_name}")
            
            charactersPerLine = 14

            deviceHeight = numLines(source_value.get("Device"), charactersPerLine, 10) + 3 + numLines(source_value.get("Description"), charactersPerLine, 10)
            IsolationMethodHeight = numLines(source_value.get("IsolationMethod"), charactersPerLine, 10)
            verificationMethodHeight = numLines(source_value.get("VerificationMethod"), charactersPerLine, 10)

            minHeight = 110
            height = (max(deviceHeight, IsolationMethodHeight, verificationMethodHeight) * 11) + 16

            if height < minHeight:
                height = minHeight

            spaceRemaining =  bottom - pageMargin
            if spaceRemaining <= 0:
                print(f'New Page: {bottom}')
                bottom = newPage()
                bottom = addSource(bottom, height)
            else: 
                print(f"Same Page: {bottom}")
                bottom = addSource(bottom, height)











pdf.save()