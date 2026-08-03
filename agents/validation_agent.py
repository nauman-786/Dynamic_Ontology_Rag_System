from typing import List, Dict, Tuple
from rdflib import Graph, URIRef
from rdflib.namespace import RDF, RDFS
from ontology.ontology_loader import OntologyLoader
from ontology.schema import OntologySchema
from agents.entity_agent import ExtractedEntity
from agents.relation_agent import ExtractedTriple
from utils.text_normalize import normalize_text

class OntologyValidationAgent:
    """Deterministically validates extracted triples against the OWL/Turtle ontology."""
    
    def __init__(self, base_uri: str = "http://example.org/dynamic-ontology#"):
        self.base_uri = base_uri
        # Load the RDF graph generated in Module 3
        self.ontology_graph: Graph = OntologyLoader.load_ontology()

    def _normalize(self, text: str) -> str:
        """Removes spaces, underscores, and lowers case for robust string matching."""
        return normalize_text(text)

    def validate_entities(self, entities: List[ExtractedEntity], ontology: OntologySchema) -> List[ExtractedEntity]:
        """Validate and deduplicate extracted entities against the ontology.

        - Ensures the entity `type` normalizes to a known ontology class.
        - Ensures entity `name` is non-empty after stripping.
        - Deduplicates by normalized (name, type) pairs.

        Returns a list of validated, deduplicated `ExtractedEntity` objects.
        """
        if not entities:
            return []

        # Build normalized ontology class mapping
        norm_to_class = {normalize_text(c.name): c.name for c in ontology.classes}
        valid_entities: List[ExtractedEntity] = []
        seen = set()

        for ent in entities:
            if not ent.name or not ent.name.strip():
                print(f"⚠️ Entity Validation: Dropping entity with empty name and type '{ent.type}'")
                continue

            norm_type = normalize_text(ent.type)
            if norm_type not in norm_to_class:
                print(f"⚠️ Entity Validation: Dropping entity '{ent.name}' with unknown type '{ent.type}'")
                continue

            # Correct the type to canonical class name
            canonical_type = norm_to_class[norm_type]

            # Normalize name for deduplication (collapse spacing and lowercase)
            norm_name = normalize_text(ent.name)
            key = (norm_name, normalize_text(canonical_type))
            if key in seen:
                print(f"⚠️ Entity Validation: Removing duplicate entity '{ent.name}' of type '{canonical_type}'")
                continue

            seen.add(key)
            ent.type = canonical_type
            valid_entities.append(ent)

        return valid_entities

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