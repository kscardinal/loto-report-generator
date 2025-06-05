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

# DUPLICATE FILE
def duplicate_pdf(input_path, output_path = "untitled.pdf"):
    try:
        base_name, extension = os.path.splitext(output_path)
        counter = 1
        while os.path.exists(output_path):
            output_path = f"{base_name} ({counter}){extension}"
            counter += 1
        shutil.copy(input_path, output_path)
        return output_path
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
        return new_name
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
    
# GET PAGES
def pageCount(pdf_path):
    try:
        reader = PdfReader(pdf_path)
        return len(reader.pages)
    except Exception as e:
        print(f"Error reading PDF file: {e}")
        return 0

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
def resizeImage(image_path, spot_width, spot_height):

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
        base_name, ext = os.path.splitext(image_path)
        resized_img.save(base_name + "(resized)" + ext)
        output_file = base_name + "(resized)" + ext

        # Return sizes
        return [new_width, new_height, output_file]
    
# ADD IMAGE TO PDF
def placeImage(image_file, top, left, input_file, output_file, page, width = 256, height = 256):
    try:
        fillpdfs.place_image(image_file, top, left, input_file, output_file, page, width, height)
        os.remove(input_file)
        os.remove(image_file)
        rename_file(output_file, input_file)
    except Exception as e:
        printError(f"Could not place image: {e}")

# ADD TEXT TO PDF
def placeText(text, top, left, input_file, output_file, page, font_size=12, font_name="helv", color=None):
    try:
        if page == 0:
            for page in range(pageCount(input_file)):
                fillpdfs.place_text(text, top, left, input_file, output_file, page + 1, font_size, font_name, color)
                os.remove(input_file)
                rename_file(output_file, input_file)
        else:
            fillpdfs.place_text(text, top, left, input_file, output_file, page, font_size, font_name, color)
            os.remove(input_file)
            rename_file(output_file, input_file)
    except Exception as e:
        printError(f"Could not place text: {e}")


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

    # Ensure output is properly truncated and formatted
    result = '\n'.join(lines).strip()

    return result


# MAIN LOGIC
def fillPDF():
    data = loadData("data2.json")
    template = loadData("template2.json")

    for form, fields in data.items():
        print(f"{form} : {fields.get('template', '')}")
        file_name = duplicate_pdf("LOTO_Fillable.pdf", form + ".pdf")

        form_type = fields.get('template', '')
        if not form_type:
            printError(f"Can't find template from.")

        template_fields = template.get(form_type, {})

        for field_name, field_value in fields.items():
            if field_name != "template":

                template_field_data = template_fields.get(field_name, {})

                if template_fields.get(field_name, {}).get('field_type', '') == "SLT":
                    placeText(field_value, template_field_data.get('x_pos', ''), template_field_data.get('y_pos', ''), file_name, "in-progress.pdf", template_field_data.get('page', ''), template_field_data.get('font_size', ''))
                elif template_fields.get(field_name, {}).get('field_type', '') == "MLT":
                   placeText(splitText(field_value, template_field_data.get('max_length', ''), template_field_data.get('max_lines', '')), template_field_data.get('x_pos', ''), template_field_data.get('y_pos', ''), file_name, "in-progress.pdf", template_field_data.get('page', ''), template_field_data.get('font_size', ''))
                elif template_fields.get(field_name, {}).get('field_type', '') == "IMG":
                    image_size = resizeImage(field_value, template_field_data.get('max_width', ''), template_field_data.get('max_height',''))
                    starting_x = template_field_data["center_x_pos"] - (image_size[0] / 2)
                    starting_y = template_field_data["center_y_pos"] - (image_size[1] / 2)
                    placeImage(image_size[2], starting_x, starting_y, file_name, "in-progress.pdf", template_field_data["page"], image_size[0], image_size[1])


fillPDF()