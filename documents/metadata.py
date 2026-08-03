from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import uuid

class DocumentMetadata(BaseModel):
    """Metadata for a processed document."""
    filename: str
    extension: str
    total_pages: int = 1
    custom_meta: Dict[str, Any] = Field(default_factory=dict)

class ParsedDocument(BaseModel):
    """Represents a fully ingested document."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str
    metadata: DocumentMetadata

class DocumentChunk(BaseModel):
    """Represents a segment of a document for vector/graph processing."""
    chunk_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)