import os
import PyPDF2

UPLOAD_DIR = "uploads"

def save_file(file):
    filepath = os.path.join(UPLOAD_DIR, file.filename)

    with open(filepath, "wb") as f:
        f.write(file.file.read())

    return filepath

def read_pdf(filepath):
    text = ""

    with open(filepath, "rb") as file:
        reader = PyPDF2.PdfReader(file)

        for page in reader.pages:
            text += page.extract_text()

    return text