# IMPORT FUNCTIONS
from fillpdf import fillpdfs
import shutil
import os


# DUPLICATE FILE
def duplicate_pdf(input_path, output_path="untitled.pdf"):
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
        print(f"The file {old_name} does not exist.")
    except PermissionError:
        print(f"Permission denied while renaming {old_name}.")
    except Exception as e:
        print(f"An error occurred: {e}")


duplicate_pdf("LOTO_Fillable.pdf")
fillpdfs.place_text("Electric", 41, 325, "untitled.pdf", "in-progress.pdf", 1, 10)
os.remove("untitled.pdf")
rename_file("in-progress.pdf", "untitled.pdf")
fillpdfs.place_text("120V", 41, 340, "untitled.pdf", "in-progress.pdf", 1, 10)
os.remove("untitled.pdf")
os.startfile("in-progress.pdf")
