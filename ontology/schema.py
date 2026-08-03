from pydantic import BaseModel, Field
from typing import List

class OntologyClass(BaseModel):
    """Represents a node type in the knowledge graph."""
    name: str = Field(
        ..., 
        description="Name of the class/entity type (PascalCase, e.g., Person, Company, Technology)."
    )
    description: str = Field(
        ..., 
        description="A brief description of what this class represents in the context of the document."
    )

class OntologyRelation(BaseModel):
    """Represents a relationship edge between two node types."""
    name: str = Field(
        ..., 
        description="Name of the relationship (UPPER_SNAKE_CASE, e.g., WORKS_AT, DEVELOPED_BY)."
    )
    domain: str = Field(
        ..., 
        description="The source class of the relationship. Must exactly match a generated class name."
    )
    range: str = Field(
        ..., 
        description="The target class of the relationship. Must exactly match a generated class name."
    )
    description: str = Field(
        ..., 
        description="Explanation of when this relationship applies."
    )

class OntologySchema(BaseModel):
    """The complete generated ontology."""
    classes: List[OntologyClass] = Field(
        ..., 
        description="List of core entity classes discovered in the document."
    )
    relations: List[OntologyRelation] = Field(
        ..., 
        description="List of valid relationships between the discovered classes."
    )