from pydantic import BaseModel, Field
from typing import List, Dict, Any
from retrieval.vector_store import FAISSVectorStore
from retrieval.graph_retriever import GraphRetriever
from documents.metadata import DocumentChunk

class HybridContext(BaseModel):
    """Container holding merged vector and graph retrieval context."""
    vector_chunks: List[DocumentChunk] = Field(default_factory=list)
    graph_triples: List[Dict[str, Any]] = Field(default_factory=list)
    formatted_context: str = ""

class HybridRetriever:
    """Combines FAISS vector retrieval and Neo4j graph retrieval."""

    def __init__(self, vector_store: FAISSVectorStore):
        self.vector_store = vector_store
        self.graph_retriever = GraphRetriever()

    def retrieve(self, query: str, top_k_chunks: int = 3) -> HybridContext:
        """Performs hybrid vector + graph retrieval and formats context string."""
        # 1. Vector Search
        search_results = self.vector_store.similarity_search(query, top_k=top_k_chunks)
        vector_chunks = [item[0] for item in search_results]

        # 2. Graph Search
        graph_triples = self.graph_retriever.retrieve_graph_context(query)

        # 3. Format Merged Context
        context_parts = []

        if graph_triples:
            context_parts.append("=== KNOWLEDGE GRAPH FACTS ===")
            for t in graph_triples:
                context_parts.append(f"({t['source']}:{t.get('source_type', 'Entity')}) --[{t['relation']}]--> ({t['target']}:{t.get('target_type', 'Entity')})")
            context_parts.append("")

        if vector_chunks:
            context_parts.append("=== DOCUMENT TEXT PASSAGES ===")
            for i, chunk in enumerate(vector_chunks, 1):
                context_parts.append(f"[Passage {i} - {chunk.metadata.get('filename', 'Doc')}]:\n{chunk.text}\n")

        formatted_context = "\n".join(context_parts)

        return HybridContext(
            vector_chunks=vector_chunks,
            graph_triples=graph_triples,
            formatted_context=formatted_context
        )