import os
from fastapi import APIRouter, UploadFile, File, Form

from ..llm.llm_router import ask_llm
from ..rag.pdf_processor import extract_pdf_text

router = APIRouter()
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ==================================================
# PDF UPLOAD + TEXT EXTRACTION
# ==================================================

@router.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    try:
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())

        result = extract_pdf_text(file_path)
        return result

    except Exception as e:
        return {"success": False, "error": str(e)}


# ==================================================
# PDF ANALYSIS
# ==================================================

@router.post("/analyze-pdf")
async def analyze_pdf(file: UploadFile = File(...)):
    try:
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())

        pdf_result = extract_pdf_text(file_path)

        if not pdf_result.get("success"):
            return pdf_result

        text = pdf_result.get("text", "")[:12000]

        analysis = await ask_llm(f"""
            Analyze this PDF.

            PDF Content:
            {text}

            Provide:
            1. Executive Summary
            2. Key Points
            3. Important Insights
            4. Actionable Recommendations
            5. Final Conclusion
        """)

        return {
            "success": True,
            "file_name": file.filename,
            "analysis": analysis
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


# ==================================================
# PDF QUESTION ANSWERING
# ==================================================

@router.post("/chat-with-pdf")
async def chat_with_pdf(file: UploadFile = File(...), question: str = Form(...)):
    try:
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())

        pdf_result = extract_pdf_text(file_path)

        if not pdf_result.get("success"):
            return pdf_result

        text = pdf_result.get("text", "")[:12000]

        answer = await ask_llm(f"""
            Use ONLY the PDF content below.

            PDF Content:
            {text}

            User Question:
            {question}

            Give a detailed answer.
        """)

        return {
            "success": True,
            "question": question,
            "answer": answer
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


# ==================================================
# PDF SUMMARY
# ==================================================

@router.post("/summarize-pdf")
async def summarize_pdf(file: UploadFile = File(...)):
    try:
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())

        pdf_result = extract_pdf_text(file_path)

        if not pdf_result.get("success"):
            return pdf_result

        text = pdf_result.get("text", "")[:12000]

        summary = await ask_llm(f"""
            Summarize this PDF.
            {text}
        """)

        return {"success": True, "summary": summary}

    except Exception as e:
        return {"success": False, "error": str(e)}


# ==================================================
# ASK PDF
# ==================================================

@router.post("/ask-pdf")
async def ask_pdf(file: UploadFile = File(...), question: str = Form(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())

    pdf_result = extract_pdf_text(file_path)

    if not pdf_result["success"]:
        return pdf_result

    text = pdf_result["text"][:12000]

    answer = await ask_llm(f"""
        PDF Content:
        {text}

        User Question:
        {question}

        Answer only using the PDF.
    """)

    return {
        "success": True,
        "question": question,
        "answer": answer,
        "features": {
            "llm": True,
            "pdf_analysis": True,
            "pdf_question_answering": True,
            "research_agent": True,
            "memory_agent": True,
            "rag_agent": True,
            "dynamic_agents": True,
            "groq": True
        }
    }
