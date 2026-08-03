from langchain_text_splitters import RecursiveCharacterTextSplitter
from documents.metadata import ParsedDocument, DocumentChunk
from config.settings import settings
from typing import List

class DocumentSplitter:
    """Splits a ParsedDocument into smaller chunks for embeddings and entity extraction."""
    
    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", ".", " ", ""]
        )

    def split(self, document: ParsedDocument) -> List[DocumentChunk]:
        """Splits the text and maps it into DocumentChunk models."""
        texts = self.text_splitter.split_text(document.text)
        chunks = []
        
        for i, text in enumerate(texts):
            chunk_metadata = {
                "filename": document.metadata.filename,
                "chunk_index": i,
                "total_chunks": len(texts)
            }
            # Merge with custom metadata if any exists
            chunk_metadata.update(document.metadata.custom_meta)
            
            chunks.append(
                DocumentChunk(
                    document_id=document.id,
                    text=text,
                    metadata=chunk_metadata
                )
            )
            
        return chunks