from typing import List, Dict, Any
from graph.neo4j_connection import Neo4jConnection

class GraphQueryEngine:
    """Executes Graph queries to extract subgraphs for retrieval."""

    def __init__(self):
        self.connection = Neo4jConnection

    def get_entity_neighborhood(self, entity_names: List[str], depth: int = 1) -> List[Dict[str, Any]]:
        """Retrieves 1-hop or 2-hop connected triples for a given list of entity names."""
        if not entity_names:
            return []

        query = f"""
        MATCH (source)-[r]->(target)
        WHERE source.name IN $entity_names OR target.name IN $entity_names
        RETURN source.name AS source, type(r) AS relation, target.name AS target, 
               labels(source)[0] AS source_type, labels(target)[0] AS target_type
        LIMIT 50
        """
        results = self.connection.execute_query(query, {"entity_names": entity_names})
        return results

    def search_entities_by_keyword(self, keyword: str) -> List[str]:
        """Finds entity names containing fuzzy keyword matches."""
        query = """
        MATCH (n)
        WHERE toLower(n.name) CONTAINS toLower($keyword)
        RETURN n.name AS name
        LIMIT 10
        """
        records = self.connection.execute_query(query, {"keyword": keyword})
        return [record["name"] for record in records]