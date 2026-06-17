from app.database.chroma_db import collection
from app.ai.embeddings import create_embedding
import uuid

def store_memory(text: str):

    embedding = create_embedding(text)

    collection.add(
        ids=[str(uuid.uuid4())],
        embeddings=[embedding],
        documents=[text]
    )

def retrieve_memory(query: str):

    embedding = create_embedding(query)

    results = collection.query(
        query_embeddings=[embedding],
        n_results=3
    )

    return results["documents"][0]