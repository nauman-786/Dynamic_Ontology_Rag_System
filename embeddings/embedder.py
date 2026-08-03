from sentence_transformers import SentenceTransformer
from typing import List

class Embedder:
    """Generates dense vector embeddings using SentenceTransformers."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def embed_text(self, text: str) -> List[float]:
        """Generates embedding for a single text string."""
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generates embeddings for a list of text strings."""
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()