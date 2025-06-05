from fillpdf import fillpdfs
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
        return output_path
    except Exception as e:
        print(f"Could not duplicate file: {e}")

try:
    if os.path.exists("testing_end.pdf"):
        os.remove("testing_end.pdf")
except Exception as e:
    print("Failed!")


duplicate_pdf("LOTO_Fillable.pdf", "testing_start.pdf")
fillpdfs.place_text("HHHHHHHHHKHHHHHHHHHKHHHHHHHHHK", 278, 742, "testing_start.pdf", "testing_end.pdf", 2, 10)
os.remove("testing_start.pdf")
os.startfile("testing_end.pdf")
