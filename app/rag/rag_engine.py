from app.memory.memory_manager import MemoryManager

from app.rag.embeddings import (
    create_embeddings
)

from app.rag.vector_store import (
    search_documents,
    initialize_qdrant
)


class RAGEngine:

    def __init__(self):

        self.memory = MemoryManager()

    # =====================================
    # RETRIEVE CONTEXT
    # =====================================

    def retrieve_context(
        self,
        user_id,
        query
    ):

        try:

            initialize_qdrant()

        except Exception as e:

            print(
                f"Qdrant Init Error: {e}"
            )

        memories = self.memory.search_memory(
            user_id=user_id,
            query=query
        )

        try:

            query_embedding = create_embeddings(
                [query]
            )[0]

            documents = search_documents(
                query_embedding=query_embedding,
                top_k=5
            )

        except Exception as e:

            print(
                f"RAG Search Error: {e}"
            )

            documents = []

        doc_context = []

        for item in documents:

            try:

                text = item.payload.get(
                    "text",
                    ""
                )

                if text:

                    doc_context.append(
                        text
                    )

            except Exception:
                pass

        return {

            "memories": memories,

            "documents": doc_context
        }

    # =====================================
    # GENERATE CONTEXT
    # =====================================

    def generate_context(
        self,
        user_id,
        query
    ):

        context = self.retrieve_context(
            user_id=user_id,
            query=query
        )

        documents = context.get(
            "documents",
            []
        )

        if not documents:

            return ""

        return "\n".join(
            documents
        )