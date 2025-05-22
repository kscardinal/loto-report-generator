# pip install fillpdf
# pip install pillow
# pip install reportlab

# IMPORT FUNCTIONS
from fillpdf import fillpdfs
from PIL import Image
import json
import shutil
import os

# DUPLICATE FILE
def duplicate_pdf(input_path, output_path = "untitled.pdf"):
    try:
        base_name, extension = os.path.splitext(output_path)
        counter = 1
        while os.path.exists(output_path):
            output_path = f"{base_name} ({counter}){extension}"
            counter += 1
        shutil.copy(input_path, output_path)
    except Exception as e:
        printError(f"Could not duplicate file: {e}")

# RENAME FILE
def rename_file(old_name, new_name):
    try:
        base_name, extension = os.path.splitext(new_name)
        counter = 1
        while os.path.exists(new_name):
            new_name = f"{base_name} ({counter}){extension}"
            counter += 1
        os.rename(old_name, new_name)
    except FileNotFoundError:
        printError(f"The file {old_name} does not exist.")
    except PermissionError:
        printError(f"Permission denied while renaming {old_name}.")
    except Exception as e:
        printError(f"An error occurred: {e}")

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
    
# CROP IMAGE
def cropImage(input_path, output_path, left, upper, right, lower):
    try:
        # Open the image
        image = Image.open(input_path)
    except Exception as e:
        printError("Could not find image file: {e}")

    # Define the cropping box (left, upper, right, lower)
    crop_box = (left, upper, right, lower)

    # Crop the image
    cropped_image = image.crop(crop_box)

    # Save the cropped image
    cropped_image.save(output_path)

# RESIZE IMAGE
def resizeImage(image_path, output_path, spot_width, spot_height):

    # Open the image
    with Image.open(image_path) as img:
        # Calculate the aspect ratio of the image
        img_width, img_height = img.size
        img_aspect = img_width / img_height

        # Calculate the aspect ratio of the spot
        spot_aspect = spot_width / spot_height

        # Determine the scaling factor to fit the image in the spot
        if img_aspect > spot_aspect:
            # Image is wider than the spot
            new_width = spot_width
            new_height = int(spot_width / img_aspect)
        else:
            # Image is taller than the spot
            new_height = spot_height
            new_width = int(spot_height * img_aspect)

        # Resize the image
        resized_img = img.resize((new_width, new_height))
        
        # Save the resized image
        resized_img.save(output_path)

        # Return sizes
        return [new_width, new_height]
    
# ADD IMAGE TO PDF
def placeImage(image_file, top, left, input_file, output_file, page, width = 256, height = 256):
    try:
        fillpdfs.place_image(image_file, top, left, input_file, output_file, page, width, height)
    except Exception as e:
        printError(f"Could not place image: {e}")

# ADD TEXT TO PDF
def placeText(text, top, left, input_file, output_file, page, font_size=12, font_name="helv", color=None):
    try:
        fillpdfs.place_text(text, top, left, input_file, output_file, page, font_size, font_name, color)
    except Exception as e:
        printError(f"Could not place text: {e}")

# SPLITS TEXT IF NEEDED
def splitText(input_text, line_length, max_lines):
    splits = 0
    lines = []
    for line in max_lines:
        lines[line] = input_text[(splits * line_length + line_length):((splits + 1) * line_length)]

# MAIN LOGIC
def fillPDF():
    data = loadData("data2.json")
    template = loadData("template2.json")

    for form, fields in data.items():
        print(f"{form} : {fields.get('template', '')}")
        duplicate_pdf("LOTO_Fillable.pdf")

        form_type = fields.get('template', '')
        if not form_type:
            printError(f"Can't find template from.")

        for field_name, field_value in fields.items():
            



fillPDF()