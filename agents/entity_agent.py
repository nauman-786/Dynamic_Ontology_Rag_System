from pydantic import BaseModel, Field
from typing import List

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

from config.settings import settings
from ontology.schema import OntologySchema
from documents.metadata import DocumentChunk


class ExtractedEntity(BaseModel):
    """An entity extracted from the text, mapped to an ontology class."""

    name: str = Field(
        ...,
        description="The actual name of the entity found in text (e.g., 'Tesla', 'Elon Musk')."
    )

    type: str = Field(
        ...,
        description="The ontology class this entity belongs to (e.g., 'Company', 'Person')."
    )


class EntityExtractionResult(BaseModel):
    """Container for all entities extracted from a single chunk."""

    entities: List[ExtractedEntity] = Field(default_factory=list)


class EntityExtractionAgent:
    """Extracts entities from text strictly based on provided ontology classes."""

    def __init__(self):

        self.llm = ChatGroq(
            model=settings.DEFAULT_MODEL,
            api_key=settings.GROQ_API_KEY,
            temperature=0.0,
            max_retries=5
        )

        # Enable structured output for Pydantic schema
        self.structured_llm = self.llm.with_structured_output(
            EntityExtractionResult
        )

        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
You are an ontology-aware information extraction system.

Your task is to extract entities from the given text.

CRITICAL RULES:
1. EXHAUSTIVE EXTRACTION: You MUST extract EVERY SINGLE valid entity mentioned in the text. Do not summarize, do not skip secondary entities, and do not group them. (e.g. Extract every individual person, every location, and every specific group).
2. You may ONLY extract entities that perfectly match one of the provided Ontology Classes.
3. Ignore entities that do not fit into the provided classes.
4. The 'type' field must EXACTLY match the ontology class name.
5. Do not create new classes.
6. Return only valid structured output.

Allowed Ontology Classes:
{classes_str}
"""
                ),
                (
                    "user",
                    """
Text to extract from:

{text}
"""
                )
            ]
        )


    def extract(
        self,
        chunk: DocumentChunk,
        ontology: OntologySchema
    ) -> EntityExtractionResult:
        """
        Extracts entities from a document chunk based on the ontology.
        """

        # Format ontology classes
        classes_str = "\n".join(
            [
                f"- {c.name}: {c.description}"
                for c in ontology.classes
            ]
        )

        chain = self.prompt | self.structured_llm

        result = chain.invoke(
            {
                "classes_str": classes_str,
                "text": chunk.text
            }
        )

        return result