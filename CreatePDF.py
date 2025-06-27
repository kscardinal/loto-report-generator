# pip install fillpdf
# pip install pillow
# pip install reportlab

# IMPORT FUNCTIONS
import json
import math

from PIL import Image
from PyPDF2 import PdfReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


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
    except Exception as e:
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
        if len(" ".join(current_line + [word])) <= line_length:
            current_line.append(word)
        else:
            lines.append(" ".join(current_line).strip())
            current_line = [word]
            if len(lines) == max_lines:
                break  # Stop if max_lines is reached

    if current_line and len(lines) < max_lines:
        lines.append(" ".join(current_line).strip())

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
pageHeight = 792
pageWidth = 612
pageSize = pageWidth, pageHeight
pageMiddleWidth = pageWidth / 2
pageMiddleHeight = pageHeight / 2

# Line Widths
defaultLineWidth = 0.25

# Font Sizes
documentTitle_FS = 18

# Fonts
documentTitle_FT = "DM Serif Display"


# Get Data
data = loadData("data_2.json")

# Creating PDF and setting document title
fileName = list(data.keys())[0]
pdf = canvas.Canvas(fileName + ".pdf")
pdf.setTitle(list(data.keys())[0])

# Registering Fonts
pdfmetrics.registerFont(TTFont("DM Serif Display", "DMSerifDisplay_Regular.ttf"))
pdfmetrics.registerFont(TTFont("Inter", "Inter_Regular.ttf"))
pdfmetrics.registerFont(TTFont("Times", "times.ttf"))

# Creating Header Title
pdf.setFont(documentTitle_FT, documentTitle_FS)
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

pdf.setFont("Times", 12)
pdf.drawString(440, 806, "Developed By:")

# ARRAY AND FOR LOOP FOR PRINTING
pdf.setFont("Times", 9)
pdf.drawString(405, 790, "Cardinal Compliance Consultants")
pdf.drawString(405, 778, "5353 Secor Rd.")
pdf.drawString(405, 766, "Toledo, OH 43623")
pdf.drawString(405, 754, "P: 419-882-9224")

# SAME AS ABOVE
pdf.setFont("Times", 10)
pdf.drawString(33, 736, "Description:")
pdf.drawString(33, 715, "Facility:")
pdf.drawString(219, 715, "Location:")
pdf.drawString(353, 715, "Rev:")
pdf.drawString(403, 736, "Procedure #:")
pdf.drawString(403, 715, "Date: ")
pdf.drawString(474, 715, "Origin:")

pdf.drawImage("CardinalLogo.png", 30, 760, 150, 50)

# CREATING MACHINE LOCKOUT SUMMARY

additionalNotesOffset = 20

pdf.setFont("Inter", 10)
for form, fields in data.items():
    print(f"{form}")

    # SIMPLIFY CODE WITH THE SECOND STRING
    if checkExists(fields, "Description"):
        pdf.drawString(85, 736, checkLength(fields.get("Description", ""), 60, True))

    if checkExists(fields, "ProcedureNumber"):
        pdf.drawString(455, 736, checkLength(fields.get("ProcedureNumber"), 12, True))

    if checkExists(fields, "Facility"):
        pdf.drawString(68, 715, checkLength(fields.get("Facility"), 29, True))

    if checkExists(fields, "Location"):
        pdf.drawString(260, 715, checkLength(fields.get("Location"), 17, True))

    if checkExists(fields, "Revision"):
        pdf.drawString(373, 715, checkLength(fields.get("Revision"), 4))

    if checkExists(fields, "Date"):
        pdf.drawString(425, 715, checkLength(fields.get("Date"), 8))

    if checkExists(fields, "Origin"):
        pdf.drawString(504, 715, checkLength(fields.get("Origin"), 8))

    if checkExists(fields, "IsolationPoints"):
        pdf.setFont("Inter", 20)
        pdf.drawString(296, 657, checkLength(fields.get("IsolationPoints"), 3))
        pdf.setFont("Inter", 10)

    # MORE CLEAR VARIABLES (change int to lineNumber)
    if checkExists(fields, "Notes"):
        max_lines = 10
        lines = splitText(fields.get("Notes"), 50, max_lines)
        for int in range(len(lines)):
            pdf.drawString(294, 609 - (11 * int), lines[int])
            if int > 5:
                additionalNotesOffset = (int - 5) * 11

    if checkExists(fields, "MachineImage"):
        new_height, new_width = resize_image(fields.get("MachineImage"), (110 + additionalNotesOffset), 180)
        pdf.drawImage(
            fields.get("MachineImage"),
            (160 - (new_width / 2)),
            555 - additionalNotesOffset,
            new_width,
            new_height,
        )


pdf.line(30, 690, 550, 690)
pdf.line(30, 670, 290, 670)
pdf.line(30, 550 - additionalNotesOffset, 550, 550 - additionalNotesOffset)
pdf.line(30, 690, 30, 550 - additionalNotesOffset)
pdf.line(290, 690, 290, 550 - additionalNotesOffset)
pdf.line(290, 640, 550, 640)
pdf.line(290, 620, 550, 620)
pdf.line(550, 690, 550, 550 - additionalNotesOffset)

pdf.setFont("DM Serif Display", 12)
pdf.drawString(90, 676, "Machine to be Locked Out")
pdf.drawString(400, 626, "Notes:")

pdf.line(295, 685, 335, 685)
pdf.line(295, 645, 335, 645)
pdf.line(295, 685, 295, 645)
pdf.line(335, 685, 335, 645)

pdf.setFont("DM Serif Display", 16)
pdf.drawString(390, 670, "Isolation Points to be")
pdf.drawString(390, 650, "Locked and Tagged")

pdf.drawImage("LockTag.png", 345, 650, 30, 30)

pdf.line(30, 530 - additionalNotesOffset, 550, 530 - additionalNotesOffset)
pdf.line(30, 530 - additionalNotesOffset, 30, 550 - additionalNotesOffset)
pdf.line(550, 530 - additionalNotesOffset, 550, 550 - additionalNotesOffset)

pdf.drawImage("Red.png", 30, 530 - additionalNotesOffset, 520, 20)

pdf.setFillColorRGB(255, 255, 255)
pdf.setFont("DM Serif Display", 12)
pdf.drawString(225, 535 - additionalNotesOffset, "SHUTDOWN SEQUENCE")

pdf.line(30, 505 - additionalNotesOffset, 550, 505 - additionalNotesOffset)
pdf.line(30, 530 - additionalNotesOffset, 30, 505 - additionalNotesOffset)
pdf.line(550, 530 - additionalNotesOffset, 550, 505 - additionalNotesOffset)

pdf.setFillColorRGB(0, 0, 0)
pdf.setFont("Inter", 8)
pdf.drawString(
    40,
    520 - additionalNotesOffset,
    "1. Notify affected personanel. 2. Properly shut down machine. 3. Isolate all energy sources. 4. Apply LOTO Devices. 5. Verify total",
)
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


pdf.setFont("Times", 10)
pdf.drawString(38, startInstructionLine - 18, "Energy Source")
pdf.drawString(128, startInstructionLine - 18, "Device")
pdf.drawString(208, startInstructionLine - 18, "Isolation Point")
pdf.drawString(298, startInstructionLine - 18, "Isolation Point")
pdf.drawString(378, startInstructionLine - 12, "Verification")
pdf.drawString(388, startInstructionLine - 22, "Method")
pdf.drawString(452, startInstructionLine - 18, "Verification Device")


# CREATING LOCKOUT POINTS
# MAKE SOURCES ARRAY OF DICTS SO SOURCE NUMBER IS UNLIMITED
source1 = False
source2 = False
source3 = False
source4 = False
source5 = False
source6 = False
source7 = False
source8 = False

for key in fields.keys():
    if "S1" in key:
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


previousBottom = endInstructionLine

if source1:

    charactersPerLine = 14

    deviceHeight = (
        numLines(fields.get("S1_Device"), charactersPerLine, 10) + 3 + numLines(fields.get("S1_Description"), charactersPerLine, 10)
    )
    IsolationMethodHeight = numLines(fields.get("S1_IsolationMethod"), charactersPerLine, 10)
    verificationMethodHeight = numLines(fields.get("S1_VerificationMethod"), charactersPerLine, 10)

    minHeight = 110
    height = (max(deviceHeight, IsolationMethodHeight, verificationMethodHeight) * 11) + 16

    if height < minHeight:
        height = minHeight

    spaceRemaining = previousBottom - 30
    if spaceRemaining < 30:
        pdf.showPage()
    else:
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

        if checkExists(fields, "S1_EnergySource"):
            match fields.get("S1_EnergySource"):
                case "Electric":
                    pdf.drawCentredString(67, source1Middle + 8, fields.get("S1_EnergySource"))
                    pdf.drawCentredString(67, source1Middle - 8, fields.get("S1_VOLTS") + " V")
                case "Natural Gas" | "Steam" | "Hydraulic" | "Regrigerant":
                    pdf.drawCentredString(67, source1Middle + 8, fields.get("S1_EnergySource"))
                    pdf.drawCentredString(67, source1Middle - 8, fields.get("S1_PSI") + " PSI")
                case "Chemical":
                    pdf.drawCentredString(67, source1Middle + 16, fields.get("S1_EnergySource"))
                    pdf.drawCentredString(67, source1Middle, fields.get("S1_ChemicalName"))
                    pdf.drawCentredString(67, source1Middle - 16, fields.get("S1_PSI") + " PSI")
                case "Gravity":
                    pdf.drawCentredString(67, source1Middle + 8, fields.get("S1_EnergySource"))
                    pdf.drawCentredString(67, source1Middle - 8, fields.get("S1_LBS") + " lbs")
                case "Thermal":
                    pdf.drawCentredString(67, source1Middle + 8, fields.get("S1_EnergySource"))
                    pdf.drawCentredString(67, source1Middle - 8, fields.get("S1_TEMP") + " F")
        else:
            pdf.drawCentredString(67, source1Middle + 8, "_____________")
            pdf.drawCentredString(67, source1Middle - 8, "_____________")

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
                pdf.drawCentredString(
                    142.5,
                    source1Middle + (math.floor(deviceHeight / 2) * 10) - (11 * int),
                    S1_Device[int],
                )
        else:
            for int in range(len(S1_Device)):
                pdf.drawCentredString(
                    142.5,
                    source1Middle + (((math.floor(deviceHeight / 2) - 1) * 10) + 5) - (11 * int),
                    S1_Device[int],
                )

        if checkExists(fields, "S1_IsolationMethod"):
            if len(splitText(fields.get("S1_IsolationMethod"), charactersPerLine, 10)) % 2 == 1:
                for int in range(len(splitText(fields.get("S1_IsolationMethod"), charactersPerLine, 10))):
                    pdf.drawCentredString(
                        326,
                        source1Middle + (math.floor(IsolationMethodHeight / 2) * 10) - (11 * int),
                        splitText(fields.get("S1_IsolationMethod"), charactersPerLine, 10)[int],
                    )
            else:
                for int in range(len(splitText(fields.get("S1_IsolationMethod"), charactersPerLine, 10))):
                    pdf.drawCentredString(
                        326,
                        source1Middle + (((math.floor(IsolationMethodHeight / 2) - 1) * 10) + 5) - (11 * int),
                        splitText(fields.get("S1_IsolationMethod"), charactersPerLine, 10)[int],
                    )
        else:
            pdf.drawCentredString(326, source1Middle, "_____________")

        if checkExists(fields, "S1_VerificationMethod"):
            if len(splitText(fields.get("S1_VerificationMethod"), charactersPerLine, 10)) % 2 == 1:
                for int in range(len(splitText(fields.get("S1_VerificationMethod"), charactersPerLine, 10))):
                    pdf.drawCentredString(
                        326,
                        source1Middle + (math.floor(verificationMethodHeight / 2) * 10) - (11 * int),
                        splitText(fields.get("S1_VerificationMethod"), charactersPerLine, 10)[int],
                    )
            else:
                for int in range(len(splitText(fields.get("S1_VerificationMethod"), charactersPerLine, 10))):
                    pdf.drawCentredString(
                        402,
                        source1Middle + (((math.floor(verificationMethodHeight / 2) - 1) * 10) + 5) - (11 * int),
                        splitText(fields.get("S1_VerificationMethod"), charactersPerLine, 10)[int],
                    )
        else:
            pdf.drawCentredString(402, source1Middle, "_____________")

        if checkExists(fields, "S1_IsolationPoint"):
            new_height, new_width = resize_image(fields.get("S1_IsolationPoint"), height - 16, 100)
            pdf.drawImage(
                fields.get("S1_IsolationPoint"),
                (235 - (new_width / 2)),
                source1Middle - (new_height / 2),
                new_width,
                new_height,
            )

        if checkExists(fields, "S1_VerificationDevice"):
            new_height, new_width = resize_image(fields.get("S1_VerificationDevice"), height - 16, 100)
            pdf.drawImage(
                fields.get("S1_VerificationDevice"),
                (495 - (new_width / 2)),
                source1Middle - (new_height / 2),
                new_width,
                new_height,
            )


pdf.save()
