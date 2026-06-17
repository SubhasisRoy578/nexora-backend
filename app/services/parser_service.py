import fitz
from docx import Document


def parse_pdf(file_path):

    text = ""

    pdf = fitz.open(file_path)

    for page in pdf:
        text += page.get_text()

    return text


def parse_docx(file_path):

    doc = Document(file_path)

    text = "\n".join(
        [p.text for p in doc.paragraphs]
    )

    return text