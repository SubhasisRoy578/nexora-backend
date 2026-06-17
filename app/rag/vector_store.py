from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct
)

from functools import lru_cache
import uuid


# ==================================================
# QDRANT CLIENT
# ==================================================

@lru_cache(maxsize=1)
def get_qdrant_client():

    return QdrantClient(
        path="./qdrant_db"
    )


client = get_qdrant_client()

COLLECTION_NAME = "nexora_documents"

VECTOR_SIZE = 384


# ==================================================
# INITIALIZE COLLECTION
# ==================================================

def initialize_qdrant():

    try:

        collections = client.get_collections()

        existing_collections = [
            collection.name
            for collection in collections.collections
        ]

        if COLLECTION_NAME not in existing_collections:

            client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=VECTOR_SIZE,
                    distance=Distance.COSINE
                )
            )

            print(
                f"Created collection: {COLLECTION_NAME}"
            )

    except Exception as e:

        print(
            f"Qdrant Initialization Error: {e}"
        )


# ==================================================
# DEBUG DOCUMENTS
# ==================================================

def debug_documents():

    try:

        results = client.scroll(
            collection_name=COLLECTION_NAME,
            limit=5,
            with_payload=True,
            with_vectors=False
        )

        return results

    except Exception as e:

        print(
            f"Debug Error: {e}"
        )

        return []


# ==================================================
# STORE EMBEDDINGS
# ==================================================

def store_embeddings(
    chunks,
    embeddings,
    source_file="unknown"
):

    try:

        initialize_qdrant()

        points = []

        for idx, embedding in enumerate(
            embeddings
        ):

            if hasattr(
                embedding,
                "tolist"
            ):

                vector = embedding.tolist()

            else:

                vector = list(embedding)

            points.append(

                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vector,
                    payload={
                        "text": chunks[idx],
                        "source": source_file
                    }
                )
            )

        if points:

            client.upsert(
                collection_name=COLLECTION_NAME,
                points=points
            )

            print(
                f"Stored {len(points)} chunks"
            )

    except Exception as e:

        print(
            f"Store Embeddings Error: {e}"
        )


# ==================================================
# SEARCH DOCUMENTS
# REQUIRED BY RAG ENGINE
# ==================================================

def search_documents(
    query_embedding,
    top_k=5
):

    try:

        initialize_qdrant()

        if hasattr(
            query_embedding,
            "tolist"
        ):

            query_vector = (
                query_embedding.tolist()
            )

        else:

            query_vector = (
                list(query_embedding)
            )

        results = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            limit=top_k,
            with_payload=True
        )

        return results

    except Exception as e:

        print(
            f"Document Search Error: {e}"
        )

        return []


# ==================================================
# GENERIC VECTOR SEARCH
# ==================================================

def search(
    query_vector,
    limit=5
):

    try:

        initialize_qdrant()

        if hasattr(
            query_vector,
            "tolist"
        ):

            query_vector = (
                query_vector.tolist()
            )

        results = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            limit=limit,
            with_payload=True
        )

        return results

    except Exception as e:

        print(
            f"[QDRANT SEARCH ERROR]: {e}"
        )

        return []