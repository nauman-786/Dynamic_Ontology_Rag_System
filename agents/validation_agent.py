from typing import List, Dict, Tuple
from rdflib import Graph, URIRef
from rdflib.namespace import RDF, RDFS
from ontology.ontology_loader import OntologyLoader
from agents.entity_agent import ExtractedEntity
from agents.relation_agent import ExtractedTriple

class OntologyValidationAgent:
    """Deterministically validates extracted triples against the OWL/Turtle ontology."""
    
    def __init__(self, base_uri: str = "http://example.org/dynamic-ontology#"):
        self.base_uri = base_uri
        # Load the RDF graph generated in Module 3
        self.ontology_graph: Graph = OntologyLoader.load_ontology()

    def _normalize(self, text: str) -> str:
        """Removes spaces, underscores, and lowers case for robust string matching."""
        if not text:
            return ""
        return text.replace(" ", "").replace("_", "").replace("-", "").lower()

    def validate_triples(
        self, 
        triples: List[ExtractedTriple], 
        entities: List[ExtractedEntity]
    ) -> List[ExtractedTriple]:
        """Filters out triples that violate the ontology's domain and range constraints."""
        
        # Create a fast lookup dictionary for entity types: {"Elon Musk": "Person"}
        entity_type_map = {e.name: e.type for e in entities}
        valid_triples = []

        for triple in triples:
            source_type = entity_type_map.get(triple.source)
            target_type = entity_type_map.get(triple.target)
            
            # If we don't know the type of the source or target, it's invalid
            if not source_type or not target_type:
                print(f"⚠️ Validation Failed: Unknown entity type in triple {triple}")
                continue
                
            if self._is_valid_relation(source_type, triple.relation, target_type):
                valid_triples.append(triple)
            else:
                print(f"🚫 Validation Failed: [{source_type}] --({triple.relation})--> [{target_type}] violates ontology rules.")

        return valid_triples

    def _is_valid_relation(self, source_type: str, relation_name: str, target_type: str) -> bool:
        """Queries the RDF graph to verify domain and range constraints robustly."""
        
        # Clean the relation name so it matches standard URI formatting
        clean_relation = relation_name.replace(" ", "_")
        relation_uri = URIRef(self.base_uri + clean_relation)
        
        # Normalize the incoming types from the LLM
        norm_source = self._normalize(source_type)
        norm_target = self._normalize(target_type)

        # Check Domain
        domain_query = list(self.ontology_graph.objects(subject=relation_uri, predicate=RDFS.domain))
        if domain_query:
            expected_domain = str(domain_query[0]).replace(self.base_uri, "")
            if self._normalize(expected_domain) != norm_source:
                return False

        # Check Range
        range_query = list(self.ontology_graph.objects(subject=relation_uri, predicate=RDFS.range))
        if range_query:
            expected_range = str(range_query[0]).replace(self.base_uri, "")
            if self._normalize(expected_range) != norm_target:
                return False

        return True