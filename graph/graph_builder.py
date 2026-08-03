from typing import List
from graph.neo4j_connection import Neo4jConnection
from agents.entity_agent import ExtractedEntity
from agents.relation_agent import ExtractedTriple

class GraphBuilder:
    """Builds and updates the Neo4j graph using validated entity and relation data."""

    def __init__(self):
        self.connection = Neo4jConnection

    def build_graph(self, entities: List[ExtractedEntity], triples: List[ExtractedTriple]) -> None:
        """Writes entities and valid relationships into Neo4j."""
        self._create_entity_nodes(entities)
        self._create_relationship_edges(triples)

    def _create_entity_nodes(self, entities: List[ExtractedEntity]) -> None:
        """Creates nodes for extracted entities with their respective labels."""
        for entity in entities:
            # Clean label to prevent Cypher injection issues
            label = entity.type.replace(" ", "_")
            query = f"""
            MERGE (n:`{label}` {{name: $name}})
            ON CREATE SET n.created_at = timestamp()
            """
            self.connection.execute_query(query, {"name": entity.name})

    def _create_relationship_edges(self, triples: List[ExtractedTriple]) -> None:
        """Creates directed relationship edges between nodes in Neo4j."""
        for triple in triples:
            rel_type = triple.relation.replace(" ", "_").upper()
            query = f"""
            MATCH (source {{name: $source_name}})
            MATCH (target {{name: $target_name}})
            MERGE (source)-[r:`{rel_type}`]->(target)
            ON CREATE SET r.created_at = timestamp()
            """
            self.connection.execute_query(query, {
                "source_name": triple.source,
                "target_name": triple.target
            })