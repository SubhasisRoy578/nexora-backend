from sentence_transformers import SentenceTransformer

embedding_model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)


# ==================================================
# SINGLE EMBEDDING
# ==================================================

def create_embedding(text: str):
    """
    Encodes a single string into a vector.
    Returns a list of floats.
    """
    return embedding_model.encode(text).tolist()


# ==================================================
# BATCH EMBEDDINGS
# REQUIRED BY: rag_engine.py -> create_embeddings([query])
# ==================================================

def create_embeddings(texts: list) -> list:
    """
    Encodes a list of strings into a list of vectors.
    Each vector is a list of floats.
    """
    return [
        embedding_model.encode(text).tolist()
        for text in texts
    ]
