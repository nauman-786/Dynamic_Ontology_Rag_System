from typing import List, Dict, Any
from graph.graph_query import GraphQueryEngine

class GraphRetriever:
    """Retrieves subgraph relationship contexts based on entity matching."""

    def __init__(self):
        self.graph_query = GraphQueryEngine()

    def retrieve_graph_context(self, query: str) -> List[Dict[str, Any]]:
        """Identifies key entities in the query and fetches their connected triples."""
        words = [w.strip("?,!.") for w in query.split() if len(w) > 2]
        matched_entities = set()

        # Find entity nodes matching query terms
        for word in words:
            found = self.graph_query.search_entities_by_keyword(word)
            matched_entities.update(found)

        if not matched_entities:
            return []

        # Retrieve 1-hop connected graph facts
        triples = self.graph_query.get_entity_neighborhood(list(matched_entities), depth=1)
        return triples