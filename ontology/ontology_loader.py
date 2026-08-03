import os
from rdflib import Graph

class OntologyLoader:
    """Loads a serialized OWL/Turtle ontology for downstream validation."""
    
    @staticmethod
    def load_ontology(filename: str = "current.ttl") -> Graph:
        file_path = os.path.join(os.path.dirname(__file__), "generated", filename)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Ontology file not found at {file_path}")
            
        g = Graph()
        g.parse(file_path, format="turtle")
        return g