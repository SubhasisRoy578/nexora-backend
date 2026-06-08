from sentence_transformers import (
    SentenceTransformer
)

_model = None


def get_model():

    global _model

    if _model is None:

        try:

            _model = SentenceTransformer(
                "BAAI/bge-small-en-v1.5"
            )

        except Exception as e:

            print(
                "Embedding model error:",
                str(e)
            )

            _model = None

    return _model


def create_embeddings(chunks):

    model = get_model()

    if model is None:

        return [[0.0] * 384 for _ in chunks]

    return model.encode(
        chunks
    )