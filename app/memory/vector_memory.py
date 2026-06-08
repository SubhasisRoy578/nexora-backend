import chromadb

from sentence_transformers import SentenceTransformer


class VectorMemory:

    def __init__(self):

        self.client = chromadb.Client()

        self.collection = self.client.get_or_create_collection(
            name="nexora_memory"
        )

        self.embedding_model = SentenceTransformer(
            "all-MiniLM-L6-v2"
        )

    def add_memory(self, text: str):

        embedding = self.embedding_model.encode(text).tolist()

        self.collection.add(
            documents=[text],
            embeddings=[embedding],
            ids=[str(hash(text))]
        )

    def search_memory(self, query: str):

        embedding = self.embedding_model.encode(query).tolist()

        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=3
        )

        return results