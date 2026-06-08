import chromadb
from sentence_transformers import SentenceTransformer

client = chromadb.PersistentClient(path="vector_db")

collection = client.get_or_create_collection(
    name="nexora_memory"
)

embedding_model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

def store_memory(text: str):

    embedding = embedding_model.encode(text).tolist()

    collection.add(
        documents=[text],
        embeddings=[embedding],
        ids=[str(hash(text))]
    )

def retrieve_memory(query: str):

    query_embedding = embedding_model.encode(query).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=3
    )

    return results["documents"]