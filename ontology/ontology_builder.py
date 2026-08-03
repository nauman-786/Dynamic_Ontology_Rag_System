import os
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, OWL
from ontology.schema import OntologySchema

class OntologyBuilder:
    """Converts a Pydantic OntologySchema into a standardized OWL/Turtle file."""
    
    def __init__(self, base_uri: str = "http://example.org/dynamic-ontology#"):
        self.base_uri = base_uri
        self.namespace = Namespace(base_uri)
        # Ensure the generated output directory exists
        self.output_dir = os.path.join(os.path.dirname(__file__), "generated")
        os.makedirs(self.output_dir, exist_ok=True)

    def build_and_save(self, schema: OntologySchema, filename: str = "current.ttl") -> str:
        """Builds the RDF graph and serializes it to a Turtle file."""
        g = Graph()
        g.bind("dynto", self.namespace)
        g.bind("owl", OWL)
        
        # 1. Define the Ontology itself
        ontology_uri = URIRef("http://example.org/dynamic-ontology")
        g.add((ontology_uri, RDF.type, OWL.Ontology))

        # 2. Add Classes
        for cls in schema.classes:
            class_uri = self.namespace[cls.name]
            g.add((class_uri, RDF.type, OWL.Class))
            g.add((class_uri, RDFS.label, Literal(cls.name)))
            g.add((class_uri, RDFS.comment, Literal(cls.description)))

        # 3. Add Relationships (Object Properties)
        for rel in schema.relations:
            rel_uri = self.namespace[rel.name]
            domain_uri = self.namespace[rel.domain]
            range_uri = self.namespace[rel.range]
            
            g.add((rel_uri, RDF.type, OWL.ObjectProperty))
            g.add((rel_uri, RDFS.label, Literal(rel.name)))
            g.add((rel_uri, RDFS.comment, Literal(rel.description)))
            
            # Add constraints: Domain and Range
            g.add((rel_uri, RDFS.domain, domain_uri))
            g.add((rel_uri, RDFS.range, range_uri))

        # Save to file
        output_path = os.path.join(self.output_dir, filename)
        g.serialize(destination=output_path, format="turtle")
        print(f"Ontology successfully saved to {output_path}")
        
        return output_path