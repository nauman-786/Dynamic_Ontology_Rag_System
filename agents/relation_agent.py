from pydantic import BaseModel, Field
from typing import List

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

from config.settings import settings
from ontology.schema import OntologySchema
from agents.entity_agent import ExtractedEntity
from documents.metadata import DocumentChunk


class ExtractedTriple(BaseModel):
    """Represents a relationship edge extracted from text."""

    source: str = Field(
        ...,
        description="Name of the source entity."
    )

    relation: str = Field(
        ...,
        description="Name of the relationship (must match ontology)."
    )

    target: str = Field(
        ...,
        description="Name of the target entity."
    )


class RelationExtractionResult(BaseModel):
    """Container for all triples extracted from a single chunk."""

    triples: List[ExtractedTriple] = Field(
        default_factory=list
    )


class RelationExtractionAgent:
    """Extracts relationships between previously identified entities."""

    def __init__(self):

        self.llm = ChatGroq(
            model=settings.DEFAULT_MODEL,
            api_key=settings.GROQ_API_KEY,
            temperature=0.0,
            max_retries=5
        )

        self.structured_llm = self.llm.with_structured_output(
            RelationExtractionResult
        )

        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
You are a precise relation extraction system.

Your task is to extract relationships between the provided known entities based on the text.

CRITICAL RULES:
1. EXHAUSTIVE EXTRACTION: You MUST extract EVERY SINGLE valid relationship between the Known Entities that is mentioned or strongly implied in the text. Do not skip any valid connections.
2. You may ONLY use the relation names provided in the Allowed Relationships list.
3. The source and target MUST exactly match the names of the Known Entities.
4. Do not create new entities.
5. Return only valid structured output.

Allowed Relationships:
{relations_str}

Known Entities:
{entities_str}
"""
                ),
                (
                    "user",
                    """
Text:
{text}
"""
                )
            ]
        )


    def extract(
        self,
        chunk: DocumentChunk,
        entities: List[ExtractedEntity],
        ontology: OntologySchema
    ) -> RelationExtractionResult:
        """
        Extracts triples connecting the provided entities.
        """

        if not entities:
            return RelationExtractionResult(
                triples=[]
            )

        # Format ontology relationship constraints
        relations_str = "\n".join(
            [
                f"- {r.name} "
                f"(Domain: {r.domain}, Range: {r.range})"
                for r in ontology.relations
            ]
        )

        # Format known entities
        entities_str = "\n".join(
            [
                f"- {e.name} (Type: {e.type})"
                for e in entities
            ]
        )

        chain = self.prompt | self.structured_llm

        result = chain.invoke(
            {
                "relations_str": relations_str,
                "entities_str": entities_str,
                "text": chunk.text
            }
        )

        return result