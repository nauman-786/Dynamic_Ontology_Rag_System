import os
import logging
from neo4j import GraphDatabase, exceptions
from dotenv import load_dotenv

# Force load environment variables right here
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Neo4jConnection:
    _driver = None

    @classmethod
    def get_driver(cls):
        """Initializes or returns the driver with liveness checks and connection lifetime controls."""
        if cls._driver is None:
            uri = os.getenv("NEO4J_URI")
            user = os.getenv("NEO4J_USER")
            password = os.getenv("NEO4J_PASSWORD")
            
            if not uri or not user or not password:
                logger.error("❌ ERROR: Neo4j environment variables are missing. Check your .env file!")
                return None

            try:
                # Added max_connection_lifetime and liveness_check_timeout to prevent Aura disconnects
                cls._driver = GraphDatabase.driver(
                    uri, 
                    auth=(user, password),
                    max_connection_lifetime=30 * 60,       # Recycle connections older than 30 mins
                    max_connection_pool_size=50,
                    liveness_check_timeout=30.0,           # Check connection liveness if idle for >30s
                    connection_timeout=15.0
                )
                cls._driver.verify_connectivity()
                logger.info("✅ Successfully connected to Neo4j!")
            except Exception as e:
                logger.error(f"❌ Failed to connect to Neo4j: {str(e)}")
                cls._driver = None
        
        return cls._driver

    @classmethod
    def verify_connection(cls) -> bool:
        """Checks if the connection is alive, reconnecting if defunct."""
        try:
            driver = cls.get_driver()
            if driver:
                driver.verify_connectivity()
                return True
            return False
        except Exception as e:
            logger.warning(f"⚠️ Connection check failed: {e}. Re-initializing driver...")
            cls.close()
            try:
                driver = cls.get_driver()
                if driver:
                    driver.verify_connectivity()
                    return True
                return False
            except Exception:
                return False

    @classmethod
    def execute_query(cls, query: str, parameters: dict = None):
        """Executes Cypher query with automatic retry on defunct/stale connection errors."""
        parameters = parameters or {}
        
        # Verify and refresh socket if defunct before executing
        cls.verify_connection()
        driver = cls.get_driver()
        
        if not driver:
            raise Exception("Cannot execute query. Neo4j is not connected.")

        try:
            with driver.session() as session:
                result = session.run(query, parameters)
                return [record.data() for record in result]
                
        # Catch network disconnects and stale connection errors from Neo4j Aura
        except (exceptions.ServiceUnavailable, exceptions.SessionExpired, exceptions.DriverError) as e:
            logger.warning(f"🔄 Defunct connection caught during query execution: {e}. Retrying query...")
            cls.close() # Reset driver instance
            
            # Re-try query with a fresh session
            fresh_driver = cls.get_driver()
            if not fresh_driver:
                raise Exception("Failed to reconnect to Neo4j during retry.")
                
            with fresh_driver.session() as session:
                result = session.run(query, parameters)
                return [record.data() for record in result]
                
        except Exception as e:
            logger.error(f"❌ Neo4j query failed: {str(e)}")
            raise e

    @classmethod
    def get_graph_summary(cls) -> str:
        """Queries Neo4j for high-level statistics, hub nodes, and entities to build a global overview."""
        if not cls.verify_connection():
            return "No active Knowledge Graph available."

        try:
            # 1. Total Nodes and Relationships
            stats_query = """
            MATCH (n)
            WITH count(n) AS node_count
            OPTIONAL MATCH ()-[r]->()
            RETURN node_count, count(r) AS rel_count
            """
            stats = cls.execute_query(stats_query)
            if not stats or stats[0].get('node_count', 0) == 0:
                return "The Knowledge Graph is currently empty."

            node_count = stats[0]['node_count']
            rel_count = stats[0]['rel_count']

            # 2. Entity Labels & Distribution
            labels_query = """
            MATCH (n)
            RETURN labels(n)[0] AS category, count(n) AS count
            ORDER BY count DESC
            """
            labels_res = cls.execute_query(labels_query)
            category_str = ", ".join([f"{r['category']}: {r['count']}" for r in labels_res if r.get('category')])

            # 3. Top Most Connected Central Entities (Hubs)
            hubs_query = """
            MATCH (n)
            OPTIONAL MATCH (n)-[r]-()
            WITH n, count(r) AS degree
            ORDER BY degree DESC LIMIT 10
            RETURN n.name AS name, labels(n)[0] AS category, degree
            """
            hubs_res = cls.execute_query(hubs_query)
            hubs_str = ", ".join([f"{r['name']} ({r['category']} - {r['degree']} links)" for r in hubs_res if r.get('name')])

            # 4. List All Node Names (capped at 50 for token safety)
            nodes_query = "MATCH (n) RETURN n.name AS name LIMIT 50"
            nodes_res = cls.execute_query(nodes_query)
            all_node_names = ", ".join([r['name'] for r in nodes_res if r.get('name')])

            return f"""📊 KNOWLEDGE GRAPH GLOBAL SUMMARY:
- Total Nodes: {node_count} | Total Relationships: {rel_count}
- Entity Categories: {category_str if category_str else 'N/A'}
- Central Key Entities (Hubs): {hubs_str if hubs_str else 'None'}
- Extracted Entities List: {all_node_names if all_node_names else 'None'}"""
        except Exception as e:
            logger.error(f"❌ Error generating graph summary: {e}")
            return f"Error retrieving graph summary: {str(e)}"

    @classmethod
    def close(cls):
        """Closes the current driver instance safely."""
        if cls._driver:
            try:
                cls._driver.close()
            except Exception:
                pass
            cls._driver = None