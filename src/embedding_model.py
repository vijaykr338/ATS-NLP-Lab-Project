from sentence_transformers import SentenceTransformer


class EmbeddingModel:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def encode(self, texts):
        return self.model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)


_embedding_model = None


def get_embedding_model(model_name="all-MiniLM-L6-v2"):
    global _embedding_model

    if _embedding_model is None:
        _embedding_model = EmbeddingModel(model_name=model_name)

    return _embedding_model