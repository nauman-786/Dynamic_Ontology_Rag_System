from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

from config.settings import settings
from ontology.schema import OntologySchema


class OntologyGenerationAgent:
    """Agent responsible for analyzing text and dynamically designing an ontology."""

    def __init__(self):

        self.llm = ChatGroq(
            model=settings.DEFAULT_MODEL,
            api_key=settings.GROQ_API_KEY,
            temperature=0.0,
            max_tokens=4096,
            max_retries=5 # Increased token limit to prevent JSON truncation
        )

        # Enforce the Pydantic schema as the output format
        self.structured_llm = self.llm.with_structured_output(
            OntologySchema
        )

        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
You are an expert Ontologist and Knowledge Graph Architect.

Your task is to analyze the provided document text and extract a high-level ontology.

CRITICAL RULES:
1. COMPREHENSIVE BUT CONCISE: Design an ontology that captures the full domain of the text, but you MUST keep the 'description' fields extremely brief (2-5 words maximum) to conserve token space.
2. Identify all relevant entity types (Classes) present in the text (e.g., Person, Deity, Monster, Location, Group, Event). Limit to a maximum of 20 highly relevant classes.
3. Identify how these entities relate to each other (Relations). Be specific (e.g., RULER_OF, FOUGHT_IN, OPPOSES, PROTECTS). Limit to a maximum of 25 relationships.
4. Ensure Relations strictly define domain (source class) and range (target class).
5. Return only valid structured output matching the ontology schema.
"""
                ),
                (
                    "user",
                    """
Document Text Sample:

{text}

Generate the ontology schema.
"""
                )
            ]
        )

    def generate(self, text_sample: str) -> OntologySchema:
        """
        Generates the ontology schema based on a text sample.
        """
        print("Generating dynamic ontology from document sample...")

        chain = self.prompt | self.structured_llm

        result = chain.invoke(
            {
                "text": text_sample
            }
        )

        return result