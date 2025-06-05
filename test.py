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
        print(f"Could not duplicate file: {e}")

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
    except Exception as e:
        print(f"Could not place image: {e}")

duplicate_pdf("LOTO_Fillable.pdf")

imageSize = resizeImage("Signature-KyleSchang.png", 100, 500)
placeImage(imageSize[2],200, 200, "untitled.pdf", "ZZZ.pdf", 2, 100, 50)
os.startfile("ZZZ.pdf")
