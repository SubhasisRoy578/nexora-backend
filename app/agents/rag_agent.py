from datetime import datetime
import time

from app.rag.rag_engine import RAGEngine


class RAGAgent:

    def __init__(self):

        self.rag = RAGEngine()

    async def run(
        self,
        query: str,
        user_id: str = "default"
    ):

        start_time = time.time()

        try:

            context = self.rag.retrieve_context(
                user_id=user_id,
                query=query
            )

            if not context:

                return {

                    # OLD FEATURES

                    "agent": "rag_agent",

                    "success": True,

                    "query": query,

                    "documents_found": 0,

                    "context": "",

                    "message":
                    "No relevant documents found",

                    # NEW FEATURES

                    "timestamp":
                    str(
                        datetime.utcnow()
                    ),

                    "execution_time":
                    round(
                        time.time() -
                        start_time,
                        2
                    ),

                    "confidence": 0,

                    "rag_status":
                    "empty"
                }

            document_count = (
                len(
                    context.split("\n")
                )
                if isinstance(
                    context,
                    str
                )
                else 1
            )

            execution_time = round(
                time.time() - start_time,
                2
            )

            preview = (
                context[:500]
                if isinstance(
                    context,
                    str
                )
                else str(context)[:500]
            )

            return {

                # OLD FEATURES

                "agent": "rag_agent",

                "success": True,

                "query": query,

                "documents_found":
                document_count,

                "context": context,

                # NEW FEATURES

                "context_preview":
                preview,

                "timestamp":
                str(
                    datetime.utcnow()
                ),

                "execution_time":
                execution_time,

                "confidence":
                min(
                    document_count * 10,
                    100
                ),

                "rag_status":
                "completed"
            }

        except Exception as e:

            return {

                "agent": "rag_agent",

                "success": False,

                "query": query,

                "documents_found": 0,

                "context": "",

                "error": str(e),

                "timestamp":
                str(
                    datetime.utcnow()
                ),

                "rag_status":
                "failed"
            }