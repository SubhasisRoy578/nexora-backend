from app.rag.chunker import chunk_text

from app.rag.embeddings import (
    create_embeddings
)

from app.rag.vector_store import (
    initialize_qdrant,
    store_embeddings
)


def process_document(
    text,
    source_file="unknown"
):

    chunks = chunk_text(text)

    embeddings = create_embeddings(
        chunks
    )

    initialize_qdrant()

    store_embeddings(
        chunks=chunks,
        embeddings=embeddings,
        source_file=source_file
    )

    return {

        "chunks": len(chunks),

        "indexed": True,

        "source_file": source_file
    }