# ==================================================
# NEXORA AI — FILE AGENT
# Reads any uploaded file, extracts text,
# chunks it for RAG, and summarizes via LLM.
# ==================================================

from datetime import datetime
import time
import os

from app.tools.file_reader import read_file, chunk_text
from app.llm.llm_router import ask_llm
from app.rag.vector_store import store_embeddings
from app.rag.embeddings import create_embeddings


class FileAgent:

    async def run(
        self,
        file_path: str,
        query: str = None,
        user_id: str = "default",
        store_in_rag: bool = True
    ) -> dict:

        start_time = time.time()

        # ------------------------------------------
        # STEP 1: Read the file
        # ------------------------------------------
        file_result = read_file(file_path)

        if not file_result.get("success"):
            return {
                "agent": "file_agent",
                "success": False,
                "file_path": file_path,
                "error": file_result.get("error", "Failed to read file"),
                "timestamp": str(datetime.utcnow())
            }

        text = file_result.get("text", "")
        file_type = file_result.get("file_type", "unknown")
        file_name = os.path.basename(file_path)

        if not text.strip():
            return {
                "agent": "file_agent",
                "success": False,
                "file_path": file_path,
                "file_type": file_type,
                "error": "No text could be extracted from file",
                "timestamp": str(datetime.utcnow())
            }

        # ------------------------------------------
        # STEP 2: Chunk text for RAG
        # ------------------------------------------
        chunks = chunk_text(text, chunk_size=500, overlap=50)

        # ------------------------------------------
        # STEP 3: Store in vector DB (Qdrant)
        # ------------------------------------------
        rag_stored = False

        if store_in_rag and chunks:
            try:
                embeddings = create_embeddings(chunks)
                store_embeddings(
                    chunks=chunks,
                    embeddings=embeddings,
                    source_file=file_name
                )
                rag_stored = True
            except Exception as e:
                print(f"[FileAgent] RAG store error: {e}")

        # ------------------------------------------
        # STEP 4: LLM Summary or Query Answer
        # ------------------------------------------
        preview = text[:3000]

        if query:
            prompt = f"""You are Nexora AI analyzing a file for the user.

File: {file_name} ({file_type.upper()})

File Content:
{preview}

User Question: {query}

Answer the user's question based on the file content.
Be specific, accurate, and cite relevant parts.
"""
        else:
            prompt = f"""You are Nexora AI analyzing a file for the user.

File: {file_name} ({file_type.upper()})

File Content:
{preview}

Provide a clear summary of this file covering:
1. What this file is about
2. Key information or data points
3. Important findings or conclusions
"""

        try:
            summary = await ask_llm(prompt)
        except Exception as e:
            summary = f"File read successfully but summary failed: {str(e)}"

        execution_time = round(time.time() - start_time, 2)

        return {
            "agent": "file_agent",
            "success": True,
            "file_path": file_path,
            "file_name": file_name,
            "file_type": file_type,
            "text_length": len(text),
            "chunk_count": len(chunks),
            "rag_stored": rag_stored,
            "summary": summary,
            "metadata": file_result.get("metadata", {}),
            "execution_time": execution_time,
            "timestamp": str(datetime.utcnow())
        }