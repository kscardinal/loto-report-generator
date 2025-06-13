# pip install fillpdf
# pip install pillow
# pip install reportlab

# IMPORT FUNCTIONS
from fillpdf import fillpdfs
from PIL import Image
import json
import shutil
import os
from PyPDF2 import PdfReader
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib import colors
import math

# RESIZE IMAGE WITH MAX HEIGHT
def resize_height(filename, max_height):
    width, height = Image.open(filename).size
    ratio = height / max_height
    return height / ratio, width / ratio

# RESIZE IMAGE WITH MAX WIDTH
def resize_width(filename, max_width):
    width, height = Image.open(filename).size
    ratio = width / max_width
    return height / ratio, width / ratio

# COMBINES BOTH TO RESIZE WITH MAX HEIGHT AND WIDTH
def resize_to_fit(filename, max_height, max_width):
    original_width, original_height = Image.open(filename).size

    # Calculate width and height ratios
    width_ratio = original_width / max_width
    height_ratio = original_height / max_height

    # Use the larger ratio to determine the limiting factor
    limiting_ratio = max(width_ratio, height_ratio)

    # Calculate new dimensions
    new_width = original_width / limiting_ratio
    new_height = original_height / limiting_ratio

    return new_height, new_width

# ADD SPACE TO CERTAIN COMPONENTS
def max_offset(offset, max_offset):
    if offset > max_offset:
        print("Offset too large")
        return max_offset
    else:
        return offset

# ERROR MESSAGE FUNCTION
def printError(errorMessage):
    redColor = "\033[91m"
    whiteColor = "\033[0m"
    print(f"{redColor}{errorMessage}{whiteColor}")

#SUCCESS MESSAGE FUNCTION
def printSuccess(successMessage):
    greenColor = "\033[92m"
    whiteColor = "\033[0m"
    print(f"{greenColor}{successMessage}{whiteColor}")

# LOAD json/data
def loadData(fileName):
    try:
        with open(fileName, "r") as file:
            return json.load(file)
    except  Exception as e:
        printError(f"Could not load json file: {e}")

# GET DATA FROM json
def getData(fileName, entryName):
    data = loadData(fileName)
    if entryName in data:
        return data[entryName]
    
# GET PAGES
def pageCount(pdf_path):
    try:
        reader = PdfReader(pdf_path)
        return len(reader.pages)
    except Exception as e:
        print(f"Error reading PDF file: {e}")
        return 0

# SPLITS TEXT IF NEEDED
def splitText(input_text, line_length, max_lines):
    words = input_text.split()
    lines = []
    current_line = []

    for word in words:
        # Check if adding the word exceeds the maximum line length
        if len(' '.join(current_line + [word])) <= line_length:
            current_line.append(word)
        else:
            # Finalize the current line and start a new one
            lines.append(' '.join(current_line).strip())
            current_line = [word]
            if len(lines) == max_lines:
                break  # Stop if max_lines is reached

    # Add any remaining words to the last line (if space is available)
    if current_line and len(lines) < max_lines:
        lines.append(' '.join(current_line).strip())

    return lines

# RETURNS NUMBER OF LINES
def numLines(input_text, line_length, max_lines):
    words = input_text.split()
    lines = []
    current_line = []

    for word in words:
        # Check if adding the word exceeds the maximum line length
        if len(' '.join(current_line + [word])) <= line_length:
            current_line.append(word)
        else:
            # Finalize the current line and start a new one
            lines.append(' '.join(current_line).strip())
            current_line = [word]
            if len(lines) == max_lines:
                break  # Stop if max_lines is reached

    # Add any remaining words to the last line (if space is available)
    if current_line and len(lines) < max_lines:
        lines.append(' '.join(current_line).strip())

    return len(lines)

# CHECK IF FIELD HAS A VALUE
def checkExists(fields, field_name):
    if fields.get(field_name):
        return True
    else:
        return False
    
# MASK THE LENGTH OF VALUES    
def checkLength_E(text, max_length):
    return text[:max_length] + " ..." if len(text) > max_length else text

# CUT THE LENGTH OF VALUES
def checkLength_C(text, max_length):
        return text[:max_length] if len(text) > max_length else text

# GET DATA
data = loadData("data_2.json")

# CREATING PDF
fileName = list(data.keys())[0]
pdf = canvas.Canvas(fileName + ".pdf")

# SETTING DOCUMENT TITLE
pdf.setTitle("Create Test")

# REGIsTERING FONTS
pdfmetrics.registerFont(TTFont('DM Serif Display', 'DMSerifDisplay_Regular.ttf'))
pdfmetrics.registerFont(TTFont('Inter', 'Inter_Regular.ttf'))
pdfmetrics.registerFont(TTFont('Times', 'times.ttf'))

# CREATING HEADER TEMPLATE
pdf.setFont('DM Serif Display', 18)
pdf.drawCentredString(300, 790, "LOCKOUT-TAGOUT")
pdf.drawCentredString(300, 770, "PROCEDURE")

pdf.setLineWidth(0.25)

pdf.line(30, 750, 550, 750)
pdf.line(30, 730, 550, 730)
pdf.line(30, 710, 550, 710)
pdf.line(30, 750, 30, 710)
pdf.line(550, 820, 550, 710)
pdf.line(400, 820, 400, 710)
pdf.line(400, 820, 550, 820)
pdf.line(400, 800, 550, 800)
pdf.line(472, 730, 472, 710)
pdf.line(215, 730, 215, 710)
pdf.line(350, 730, 350, 710)

pdf.setFont('Times', 12)
pdf.drawString(440, 806, "Developed By:")

pdf.setFont('Times', 9)
pdf.drawString(405, 790, "Cardinal Compliance Consultants")
pdf.drawString(405, 778, "5353 Secor Rd.")
pdf.drawString(405, 766, "Toledo, OH 43623")
pdf.drawString(405, 754, "P: 419-882-9224")

pdf.setFont('Times', 10)
pdf.drawString(33, 736, "Description:")
pdf.drawString(33, 715, "Facility:")
pdf.drawString(219, 715, "Location:")
pdf.drawString(353, 715, "Rev:")
pdf.drawString(403, 736, "Procedure #:")
pdf.drawString(403, 715, "Date: ")
pdf.drawString(474, 715, "Origin:")

pdf.drawImage("CardinalLogo.png", 30, 760, 150, 50)

# CREATING MACHINE LOCKOUT SUMMARY

additionalNotesOffset = 0

pdf.setFont('Inter', 10)
for form, fields in data.items():
    print(f"{form}")

    if checkExists(fields, "Description"):
        pdf.drawString(85, 736, checkLength_E(fields.get("Description"), 60))
    
    if checkExists(fields, "ProcedureNumber"):
        pdf.drawString(455, 736, checkLength_E(fields.get("ProcedureNumber"), 12))

    if checkExists(fields, "Facility"):
        pdf.drawString(68, 715, checkLength_E(fields.get("Facility"), 29))

    if checkExists(fields, "Location"):
        pdf.drawString(260, 715, checkLength_E(fields.get("Location"), 17))

    if checkExists(fields, "Revision"):
        pdf.drawString(373, 715, checkLength_C(fields.get("Revision"), 4))

    if checkExists(fields, "Date"):
        pdf.drawString(425, 715, checkLength_C(fields.get("Date"), 8))

    if checkExists(fields, "Origin"):
        pdf.drawString(504, 715, checkLength_C(fields.get("Origin"), 8))

    if checkExists(fields, "IsolationPoints"):
        pdf.setFont('Inter', 20)
        pdf.drawString(296, 657, checkLength_C(fields.get("IsolationPoints"), 3))
        pdf.setFont('Inter', 10)

    if checkExists(fields, "Notes"):
        max_lines = 10
        lines = splitText(fields.get("Notes"), 50, max_lines)
        for int in range(len(lines)):
            pdf.drawString(294, 609 - (11 * int), lines[int])
            if int > 5:
                additionalNotesOffset = (int - 5) * 11
    
    if checkExists(fields, "MachineImage"):
        new_height, new_width = resize_to_fit(fields.get("MachineImage"), (100 + additionalNotesOffset), 180)
        pdf.drawImage(fields.get("MachineImage"), (160 - (new_width / 2)), 560 - additionalNotesOffset, new_width, new_height)


pdf.line(30, 690, 550, 690)
pdf.line(30, 670, 290, 670)
pdf.line(30, 550 - additionalNotesOffset, 550, 550 - additionalNotesOffset)
pdf.line(30, 690, 30, 550 - additionalNotesOffset)
pdf.line(290, 690, 290, 550 - additionalNotesOffset)
pdf.line(290, 640, 550, 640)
pdf.line(290, 620, 550, 620)
pdf.line(550, 690, 550, 550 - additionalNotesOffset)

pdf.setFont('DM Serif Display', 12)
pdf.drawString(90, 676, "Machine to be Locked Out")
pdf.drawString(400, 626, "Notes:")

pdf.line(295, 685, 335, 685)
pdf.line(295, 645, 335, 645)
pdf.line(295, 685, 295, 645)
pdf.line(335, 685, 335, 645)

pdf.setFont('DM Serif Display', 16)
pdf.drawString(390, 670, 'Isolation Points to be')
pdf.drawString(390, 650, "Locked and Tagged")

pdf.drawImage("LockTag.png", 345, 650, 30, 30)

pdf.line(30, 530 - additionalNotesOffset, 550, 530 - additionalNotesOffset)
pdf.line(30, 530 - additionalNotesOffset, 30, 550 - additionalNotesOffset)
pdf.line(550, 530 - additionalNotesOffset, 550, 550 - additionalNotesOffset)

pdf.drawImage('Red.png', 30, 530 - additionalNotesOffset, 520, 20)

pdf.setFillColorRGB(255, 255, 255)
pdf.setFont('DM Serif Display', 12)
pdf.drawString(225, 535 - additionalNotesOffset, "SHUTDOWN SEQUENCE")

pdf.line(30, 505 - additionalNotesOffset, 550, 505 - additionalNotesOffset)
pdf.line(30, 530 - additionalNotesOffset, 30, 505 - additionalNotesOffset)
pdf.line(550, 530 - additionalNotesOffset, 550, 505 - additionalNotesOffset)

pdf.setFillColorRGB(0, 0, 0)
pdf.setFont('Inter', 8)
pdf.drawString(40, 520 - additionalNotesOffset, "1. Notify affected personanel. 2. Properly shut down machine. 3. Isolate all energy sources. 4. Apply LOTO Devices. 5. Verify total")
pdf.drawString(225, 510 - additionalNotesOffset, "de-energizing of all sources.")


# CREATING LOCKOUT POINT HEADER

startInstructionLine = 505 - additionalNotesOffset
endInstructionLine = startInstructionLine - 30 

pdf.line(30, endInstructionLine, 550, endInstructionLine)
pdf.line(30, startInstructionLine, 30, endInstructionLine)
pdf.line(550, startInstructionLine, 550, endInstructionLine)
pdf.line(105, startInstructionLine, 105, endInstructionLine)
pdf.line(180, startInstructionLine, 180, endInstructionLine)
pdf.line(290, startInstructionLine, 290, endInstructionLine)
pdf.line(365, startInstructionLine, 365, endInstructionLine)
pdf.line(440, startInstructionLine, 440, endInstructionLine)



pdf.setFont('Times', 10)
pdf.drawString(38, startInstructionLine - 18, "Energy Source")
pdf.drawString(128, startInstructionLine - 18, "Device")
pdf.drawString(208, startInstructionLine - 18, "Isolation Point")
pdf.drawString(298, startInstructionLine - 18, "Isolation Point")
pdf.drawString(378, startInstructionLine - 12, "Verification")
pdf.drawString(388, startInstructionLine - 22, "Method")
pdf.drawString(452, startInstructionLine - 18, "Verification Device")


# CREATING LOCKOUT POINTS

source1 = False
source2 = False
source3 = False
source4 = False
source5 = False
source6 = False
source7 = False
source8 = False

for key in fields.keys():
    if  "S1" in key:
        source1 = True
    if "S2" in key:
        source = True
    if "S3" in key:
        source = True
    if "S4" in key:
        source = True
    if "S5" in key:
        source = True
    if "S6" in key:
        source = True
    if "S7" in key:
        source = True
    if "S8" in key:
        source = True


if source1:

    charactersPerLine = 14

    deviceHeight = numLines(fields.get("S1_Device"), charactersPerLine, 10) + 3 + numLines(fields.get("S1_Description"), charactersPerLine, 10)
    IsolationMethodHeight = numLines(fields.get("S1_IsolationMethod"), charactersPerLine, 10)
    verificationMethodHeight = numLines(fields.get("S1_VerificationMethod"), charactersPerLine, 10)

    minHeight = 110
    height = (max(deviceHeight, IsolationMethodHeight, verificationMethodHeight) * 11) + 16

    if height < minHeight:
        height = minHeight

    source1Start = endInstructionLine
    source1End = source1Start - height
    source1Middle = source1Start - (height / 2)

    pdf.line(30, source1End, 550, source1End)
    pdf.line(30, endInstructionLine, 30, source1End)
    pdf.line(550, endInstructionLine, 550, source1End)
    pdf.line(105, endInstructionLine, 105, source1End)
    pdf.line(180, endInstructionLine, 180, source1End)
    pdf.line(290, endInstructionLine, 290, source1End)
    pdf.line(365, endInstructionLine, 365, source1End)
    pdf.line(440, endInstructionLine, 440, source1End)

    match fields.get("S1_EnergySource"):
        case "Electric":
            pdf.drawCentredString(67,  source1Middle + 6,  fields.get("S1_EnergySource"))
            pdf.drawCentredString(67, source1Middle - 6, fields.get("S1_VOLTS") + " V")
        case "Natural Gas" | "Steam" | "Hydraulic" | "Regrigerant":
            pdf.drawCentredString(67,  source1Middle + 6,  fields.get("S1_EnergySource"))
            pdf.drawCentredString(67, source1Middle - 6, fields.get("S1_PSI") + " PSI")
        case "Chemical":
            pdf.drawCentredString(67,  source1Middle + 16,  fields.get("S1_EnergySource"))
            pdf.drawCentredString(67, source1Middle, fields.get("S1_ChemicalName"))
            pdf.drawCentredString(67, source1Middle - 16, fields.get("S1_PSI") + " PSI")
        case "Gravity":
            pdf.drawCentredString(67,  source1Middle + 6,  fields.get("S1_EnergySource"))
            pdf.drawCentredString(67, source1Middle - 6, fields.get("S1_LBS") + " lbs")
        case "Thermal":
            pdf.drawCentredString(67,  source1Middle + 6,  fields.get("S1_EnergySource"))
            pdf.drawCentredString(67, source1Middle - 6, fields.get("S1_TEMP") + " F")

    S1_Device = []

    if checkExists(fields, "S1_Device"):
        max_device_lines = 10
        device_lines = splitText(fields.get("S1_Device"), charactersPerLine, max_device_lines)
        for int in range(len(device_lines)):
            S1_Device.append(device_lines[int])
    else:
        S1_Device.append("_____________")

    if checkExists(fields, "S1_Tag"):
        S1_Device.append("")
        S1_Device.append("Tag: #" + fields.get("S1_Tag"))
        S1_Device.append("")
    else:
        S1_Device.append("")
        S1_Device.append("Tag: #_______")
        S1_Device.append("")

    if checkExists(fields, "S1_Description"):
        max_description_lines = 10
        description_lines = splitText(fields.get("S1_Description"), charactersPerLine, max_description_lines)
        for int in range(len(description_lines)):
            S1_Device.append(description_lines[int])
    else:
        S1_Device.append("_____________")

    if deviceHeight % 2 == 1:
        for int in range(len(S1_Device)):
            pdf.drawCentredString(142.5, source1Middle + (math.floor(deviceHeight / 2) * 10) - (11 * int), S1_Device[int])
    else:
        for int in range(len(S1_Device)):
            pdf.drawCentredString(142.5, source1Middle + (((math.floor(deviceHeight / 2) - 1) * 10) + 5) - (11 * int), S1_Device[int])

    if checkExists(fields, "S1_IsolationMethod"):
        if len(splitText(fields.get("S1_IsolationMethod"), charactersPerLine, 10)) % 2 == 1:
            for int in range(len(splitText(fields.get("S1_IsolationMethod"), charactersPerLine, 10))):
                pdf.drawCentredString(326, source1Middle + (math.floor(IsolationMethodHeight / 2) * 10) - (11 * int), splitText(fields.get("S1_IsolationMethod"), charactersPerLine, 10)[int])
        else:
            for int in range(len(splitText(fields.get("S1_IsolationMethod"), charactersPerLine, 10))):
                pdf.drawCentredString(326, source1Middle + (((math.floor(IsolationMethodHeight / 2) - 1) * 10) + 5) - (11 * int), splitText(fields.get("S1_IsolationMethod"), charactersPerLine, 10)[int])
    else:
        pdf.drawCentredString(326, source1Middle, "_____________")


    if checkExists(fields, "S1_VerificationMethod"):
        if len(splitText(fields.get("S1_VerificationMethod"), charactersPerLine, 10)) % 2 == 1:
            for int in range(len(splitText(fields.get("S1_VerificationMethod"), charactersPerLine, 10))):
                pdf.drawCentredString(326, source1Middle + (math.floor(verificationMethodHeight / 2) * 10) - (11 * int), splitText(fields.get("S1_VerificationMethod"), charactersPerLine, 10)[int])
        else:
            for int in range(len(splitText(fields.get("S1_VerificationMethod"), charactersPerLine, 10))):
                pdf.drawCentredString(402, source1Middle + (((math.floor(verificationMethodHeight / 2) - 1) * 10) + 5) - (11 * int), splitText(fields.get("S1_VerificationMethod"), charactersPerLine, 10)[int])
    else:
        pdf.drawCentredString(402, source1Middle, "_____________")


    if checkExists(fields, "S1_IsolationPoint"):
        new_height, new_width = resize_to_fit(fields.get("S1_IsolationPoint"), height - 16, 100)
        pdf.drawImage(fields.get("S1_IsolationPoint"), (235 - (new_width / 2)), source1Middle - (new_height / 2), new_width, new_height)


    if checkExists(fields, "S1_VerificationDevice"):
        new_height, new_width = resize_to_fit(fields.get("S1_VerificationDevice"), height - 16, 100)
        pdf.drawImage(fields.get("S1_VerificationDevice"), (495 - (new_width / 2)), source1Middle - (new_height / 2), new_width, new_height)

pdf.save()