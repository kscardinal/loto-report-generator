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


def resize_height(filename, max_height):
    width, height = Image.open(filename).size
    ratio = height / max_height
    return height / ratio, width / ratio

def resize_width(filename, max_width):
    width, height = Image.open(filename).size
    ratio = width / max_width
    return height / ratio, width / ratio

def max_offset(offset, max_offset):
    if offset > max_offset:
        print("Offset too large")
        return max_offset
    else:
        return offset



# CREATING PDF
pdf = canvas.Canvas("Create_Test.pdf")

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
pdf.line(475, 730, 475, 710)
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
pdf.drawString(478, 715, "Origin:")

pdf.drawImage("CardinalLogo.png", 30, 760, 150, 50)

# CREATING MACHINE LOCKOUT SUMMARY

additionalNotesOffset = 20
additionalNotesOffset = max_offset(additionalNotesOffset, 40)

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

new_height, new_width = resize_height("test_1.jpg", (100 + additionalNotesOffset))

pdf.drawImage('test_1.jpg', (160 - (new_width / 2)), 560 - additionalNotesOffset, new_width, new_height)

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
pdf.drawString(40, 520 - additionalNotesOffset, "1. Notify affected personanel. 2. Properly shut down machine. 3. Isolate all energy sources. 4. Apply LOTO Devices. 5. Verify")
pdf.drawString(225, 510 - additionalNotesOffset, "total de-energizing of all sources.")


# CREATING LOCKOUT POINTS

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









pdf.save()