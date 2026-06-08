from pypdf import PdfReader


def extract_pdf_text(file_path: str):

    text = ""

    page_count = 0

    try:

        reader = PdfReader(file_path)

        page_count = len(reader.pages)

        for page in reader.pages:

            page_text = page.extract_text()

            if page_text:

                text += page_text + "\n"

        return {

            "success": True,

            "text": text,

            "pages": page_count,

            "characters": len(text)
        }

    except Exception as e:

        return {

            "success": False,

            "error": str(e)
        }