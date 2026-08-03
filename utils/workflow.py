import time
from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from documents.loader import DocumentLoader
from documents.splitter import DocumentSplitter
from documents.metadata import ParsedDocument, DocumentChunk
from ontology.schema import OntologySchema
from ontology.ontology_builder import OntologyBuilder
from agents.ontology_agent import OntologyGenerationAgent
from agents.entity_agent import EntityExtractionAgent, ExtractedEntity
from agents.relation_agent import RelationExtractionAgent, ExtractedTriple
from agents.validation_agent import OntologyValidationAgent
from graph.graph_builder import GraphBuilder
from retrieval.vector_store import FAISSVectorStore
from embeddings.embedder import Embedder

# Define the state dictionary for LangGraph
class GraphState(TypedDict):
    file_path: str
    document: ParsedDocument
    chunks: List[DocumentChunk]
    ontology: OntologySchema
    entities: List[ExtractedEntity]
    triples: List[ExtractedTriple]
    valid_triples: List[ExtractedTriple]
    status_messages: List[str]

class IngestionWorkflow:
    """LangGraph orchestrator for document ingestion and graph building."""
    
    def __init__(self, vector_store: FAISSVectorStore):
        self.vector_store = vector_store
        self.progress_callback = None  # Added callback for real-time progress
        self.workflow = StateGraph(GraphState)
        self._build_graph()

    def set_progress_callback(self, callback):
        """Allows the server to hook into the workflow's progress."""
        self.progress_callback = callback

    def _build_graph(self):
        # Define Nodes
        self.workflow.add_node("load_and_split", self.load_and_split_node)
        self.workflow.add_node("generate_ontology", self.generate_ontology_node)
        self.workflow.add_node("extract_knowledge", self.extract_knowledge_node)
        self.workflow.add_node("validate_and_store", self.validate_and_store_node)

        # Define Edges
        self.workflow.set_entry_point("load_and_split")
        self.workflow.add_edge("load_and_split", "generate_ontology")
        self.workflow.add_edge("generate_ontology", "extract_knowledge")
        self.workflow.add_edge("extract_knowledge", "validate_and_store")
        self.workflow.add_edge("validate_and_store", END)

        self.app = self.workflow.compile()

    def load_and_split_node(self, state: GraphState):
        doc = DocumentLoader.load_document(state["file_path"])
        splitter = DocumentSplitter()
        chunks = splitter.split(doc)
        
        # Add to vector store immediately
        self.vector_store.add_chunks(chunks)
        
        state["document"] = doc
        state["chunks"] = chunks
        state["status_messages"] = [f"Loaded {doc.metadata.filename} and created {len(chunks)} chunks."]
        return state

    def generate_ontology_node(self, state: GraphState):
        # Use first 3 chunks to sample text for ontology generation
        sample_text = "\n\n".join([c.text for c in state["chunks"][:3]])
        
        agent = OntologyGenerationAgent()
        schema = agent.generate(sample_text)
        
        # Build and save Turtle file
        builder = OntologyBuilder()
        builder.build_and_save(schema)
        
        state["ontology"] = schema
        state["status_messages"].append(f"Generated ontology with {len(schema.classes)} classes and {len(schema.relations)} relations.")
        return state

    def extract_knowledge_node(self, state: GraphState):
        entity_agent = EntityExtractionAgent()
        relation_agent = RelationExtractionAgent()
        
        all_entities = []
        all_triples = []
        
        # Process first 10 chunks for demo speed (in production, process all or batch)
        process_chunks = state["chunks"]
        total_chunks = len(process_chunks)
        
        for i, chunk in enumerate(process_chunks):
            # 1. Extract Entities (Groq API Call 1)
            entity_result = entity_agent.extract(chunk, state["ontology"])
            
            # Brief pause between entity and relation calls
            time.sleep(6.0)
            
            if entity_result.entities:
                all_entities.extend(entity_result.entities)
                # 2. Extract Relations (Groq API Call 2)
                rel_result = relation_agent.extract(chunk, entity_result.entities, state["ontology"])
                all_triples.extend(rel_result.triples)
            
            # Longer pause before moving to the next chunk for Groq Free Tier
            time.sleep(7.0)

            # --- Trigger the progress update back to the server ---
            if self.progress_callback:
                percent = int(((i + 1) / total_chunks) * 100)
                self.progress_callback(percent, f"Extracting nodes: Chunk {i + 1} of {total_chunks}")
                
        state["entities"] = all_entities
        state["triples"] = all_triples
        state["status_messages"].append(f"Extracted {len(all_entities)} entities and {len(all_triples)} relationships.")
        return state

    def validate_and_store_node(self, state: GraphState):
        # Validate against OWL ontology
        validator = OntologyValidationAgent()
        valid_triples = validator.validate_triples(state["triples"], state["entities"])
        
        # Store in Neo4j
        graph_builder = GraphBuilder()
        graph_builder.build_graph(state["entities"], valid_triples)
        
        state["valid_triples"] = valid_triples
        state["status_messages"].append(f"Validated triples and stored {len(valid_triples)} edges in Neo4j.")
        return state

    def run(self, file_path: str) -> GraphState:
        """Executes the workflow."""
        initial_state = GraphState(
            file_path=file_path, document=None, chunks=[], ontology=None, 
            entities=[], triples=[], valid_triples=[], status_messages=[]
        )
        return self.app.invoke(initial_state)
    