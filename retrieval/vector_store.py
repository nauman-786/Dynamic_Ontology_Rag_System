import faiss
import numpy as np
from typing import List, Dict, Any, Tuple
from documents.metadata import DocumentChunk
from embeddings.embedder import Embedder

class FAISSVectorStore:
    """In-memory FAISS vector store for semantic search over document chunks."""

    def __init__(self, embedder: Embedder):
        self.embedder = embedder
        self.dimension = 384  # Default for all-MiniLM-L6-v2
        self.index = faiss.IndexFlatL2(self.dimension)
        self.chunks: List[DocumentChunk] = []

    def add_chunks(self, chunks: List[DocumentChunk]) -> None:
        """Embeds and indexes document chunks in FAISS."""
        if not chunks:
            return
            
        texts = [chunk.text for chunk in chunks]
        embeddings = self.embedder.embed_batch(texts)
        embeddings_np = np.array(embeddings, dtype=np.float32)

        self.index.add(embeddings_np)
        self.chunks.extend(chunks)

    def similarity_search(self, query: str, top_k: int = 4) -> List[Tuple[DocumentChunk, float]]:
        """Performs similarity search against indexed chunks."""
        if self.index.ntotal == 0:
            return []

        query_vector = np.array([self.embedder.embed_text(query)], dtype=np.float32)
        distances, indices = self.index.search(query_vector, top_k)

        results = []
        for idx, dist in zip(indices[0], distances[0]):
            if idx != -1 and idx < len(self.chunks):
                results.append((self.chunks[idx], float(dist)))
                
        return results