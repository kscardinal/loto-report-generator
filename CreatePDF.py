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


# creating a pdf object
pdf = canvas.Canvas("Create_Test.pdf")

# setting the title of the document
pdf.setTitle("Create Test")

# registering a external font in python
pdfmetrics.registerFont(TTFont('DM Serif Display', 'DMSerifDisplay_Regular.ttf'))
pdfmetrics.registerFont(TTFont('Inter', 'Inter_Regular.ttf'))
pdfmetrics.registerFont(TTFont('Times', 'times.ttf'))




# HEADER
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

pdf.setFont('Times', 12)
pdf.drawString(33, 735, "Description:")
pdf.drawString(33, 715, "Facility:")
pdf.drawString(219, 715, "Location:")
pdf.drawString(353, 715, "Rev:")
pdf.drawString(403, 735, "Procedure #:")
pdf.drawString(403, 715, "Date: ")
pdf.drawString(478, 715, "Origin:")

pdf.drawImage("CardinalLogo.png", 30, 760, 150, 50)

# MACHINE LOCKOUT SUMMARY

additionalNotesOffset = 0

if additionalNotesOffset > 40:
    print("Notes are too long")
    additionalNotesOffset = 40

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

# Get dimensions
width, height = Image.open("test_1.jpg").size
max_height = 100 + additionalNotesOffset
ratio = height / max_height
new_height, new_width = height / ratio, width / ratio

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

pdf.save()