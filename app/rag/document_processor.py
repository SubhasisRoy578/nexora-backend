from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader
from docx import Document


class DocumentProcessor:
    def __init__(self):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=1200,
            chunk_overlap=200,
        )

    async def process_document(self, file_path: str):
        path = Path(file_path)

        if path.suffix == ".pdf":
            text = self.extract_pdf(file_path)

        elif path.suffix == ".docx":
            text = self.extract_docx(file_path)

        else:
            text = Path(file_path).read_text(
                encoding="utf-8",
                errors="ignore"
            )

        chunks = self.splitter.split_text(text)

        return {
            "text": text,
            "chunks": chunks
        }

    def extract_pdf(self, file_path: str):
        pdf = PdfReader(file_path)

        text = ""

        for page in pdf.pages:
            extracted = page.extract_text()

            if extracted:
                text += extracted + "\n"

        return text

    def extract_docx(self, file_path: str):
        doc = Document(file_path)

        return "\n".join(
            [p.text for p in doc.paragraphs]
        )