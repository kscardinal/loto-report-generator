# pip install fillpdf
# pip install pillow
# pip install reportlab


from fillpdf import fillpdfs
from PIL import Image
import json
import shutil
import os

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

# SPLITS TEXT
def split_text_multiline(text, max_length, max_parts=3):

    parts = []
    for _ in range(max_parts):
        if len(text) <= max_length:
            parts.append(text)
            break
        split_index = text[:max_length].rfind(" ")
        if split_index == -1:  # No whitespace found, split at max_length
            split_index = max_length
        parts.append(text[:split_index].strip())
        text = text[split_index:].strip()
    while len(parts) < max_parts:  # Fill remaining parts with empty strings
        parts.append("")
    return parts

# PLACES TEXT
def process_text(field_value, template_field):

    max_length = template_field["max_characters"]
    max_parts = 3 if len(field_value) > max_length * 2 else 2 if len(field_value) > max_length else 1
    parts = split_text_multiline(field_value, max_length, max_parts)

    y_position = template_field["y"]
    for i, part in enumerate(parts):
        if not part:  # Skip empty parts
            continue
        if template_field["page"] == 0:
            placeText(part, template_field["x"], y_position, "untitled.pdf", "in_progress.pdf", 1, template_field["font_size"])
            os.remove("untitled.pdf")
            rename_file("in_progress.pdf", "untitled.pdf")
            placeText(part, template_field["x"], y_position, "untitled.pdf", "in_progress.pdf", 2, template_field["font_size"])
        else:
            placeText(part, template_field["x"], y_position, "untitled.pdf", "in_progress.pdf", template_field["page"], template_field["font_size"])
        os.remove("untitled.pdf")
        rename_file("in_progress.pdf", "untitled.pdf")
        y_position += 8  # Adjust Y-position for each line

# COMPUTING
def fillPDF():
    data = loadData("data.json")
    template = loadData("template.json")
    
    for file_name, fields in data.items():
        print(f"Processing file: {file_name}")
        duplicate_pdf("LOTO_Fillable.pdf")
        for field_name, field_value in fields.items():

            template_field = template[fields["Template"]].get(field_name)
            
            if not template_field:
                printError(f"Template information for {field_name} is missing.")
                continue

            if "_I" in field_name:
                image_size = resizeImage(field_value, "test.jpg", template_field["max_width"], template_field["max_height"])
                starting_x = template_field["center_x"] - (image_size[0] / 2)
                starting_y = template_field["center_y"] - (image_size[1] / 2)
                placeImage("test.jpg", starting_x, starting_y, "untitled.pdf", "in_progress.pdf", template_field["page"], image_size[0], image_size[1])
                os.remove("untitled.pdf")
                os.remove("test.jpg")
                rename_file("in_progress.pdf", "untitled.pdf")
            else:
                process_text(field_value, template_field)
            
        rename_file("untitled.pdf", file_name + ".pdf")


fillPDF()