import os
import tempfile
import json
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# Load Environment Variables
load_dotenv()

from utils.workflow import IngestionWorkflow
from retrieval.vector_store import FAISSVectorStore
from embeddings.embedder import Embedder
from retrieval.hybrid_retriever import HybridRetriever
from agents.answer_agent import AnswerGenerationAgent
from graph.neo4j_connection import Neo4jConnection

# Initialize FastAPI App
app = FastAPI(
    title="Dynamic Ontology RAG API",
    description="Backend API powering the React Knowledge Graph & RAG UI",
    version="1.0.0"
)

# Enable CORS for React Frontend (Vite runs on http://localhost:5173 by default)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows requests from any frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Vector Store Instance (In-Memory singleton)
vector_store = FAISSVectorStore(Embedder())


# ==========================================
# PYDANTIC REQUEST / RESPONSE SCHEMAS
# ==========================================
class MessageHistory(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    prompt: str
    history: Optional[List[MessageHistory]] = []

class ChatResponse(BaseModel):
    response: str
    context: str

# ==========================================
# API ENDPOINTS
# ==========================================

@app.get("/api/health")
def check_health():
    """Returns database connection status and total vector chunks."""
    is_connected = Neo4jConnection.verify_connection()
    return {
        "status": "online",
        "neo4j_connected": is_connected,
        "total_faiss_chunks": len(vector_store.chunks)
    }


# ==========================================
# GLOBAL PROGRESS TRACKER
# ==========================================
upload_progress = {"percent": 0, "message": "Idle"}

@app.get("/api/progress")
def get_upload_progress():
    """Frontend will poll this endpoint to get the real-time percentage."""
    return upload_progress


@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...)):
    """Handles document upload, clears old data, runs LangGraph, and tracks progress."""
    global upload_progress
    upload_progress = {"percent": 0, "message": "Initializing upload..."}

    if not file.filename.endswith(('.pdf', '.docx', '.txt')):
        upload_progress = {"percent": 0, "message": "Error: Invalid file type."}
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF, DOCX, and TXT are supported.")

    # ==========================================
    # 🧹 WIPE OLD DATA (Graph & Vector Store)
    # ==========================================
    try:
        upload_progress = {"percent": 5, "message": "Clearing previous knowledge graph..."}
        # 1. Delete all nodes and relationships in Neo4j
        if Neo4jConnection.verify_connection():
            Neo4jConnection.execute_query("MATCH (n) DETACH DELETE n")
            print("✅ Successfully cleared old Neo4j Graph.")
        
        # 2. Reset the FAISS Vector Store
        global vector_store
        vector_store = FAISSVectorStore(Embedder())
        print("✅ Successfully cleared old FAISS Vectors.")
    except Exception as e:
        print(f"⚠️ Warning: Could not clear old data: {e}")
    # ==========================================

    upload_progress = {"percent": 10, "message": "Saving document..."}
    
    # Save uploaded file to temp location
    suffix = f".{file.filename.split('.')[-1]}"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_path = temp_file.name

    try:
        # Define a callback to update the global progress variable
        def update_progress(percent: int, message: str):
            global upload_progress
            # Scale the pipeline percentage (0-100) to fit between 10% and 95% of total progress
            scaled_percent = 10 + int((percent / 100) * 85)
            upload_progress["percent"] = scaled_percent
            upload_progress["message"] = message

        # Run Ingestion Pipeline
        workflow = IngestionWorkflow(vector_store)
        
        # Pass the callback into the workflow so it can report progress during chunks
        if hasattr(workflow, 'set_progress_callback'):
            workflow.set_progress_callback(update_progress)
            
        # Run workflow in a background thread so main event loop can respond to GET /api/progress
        result_state = await run_in_threadpool(workflow.run, temp_path)

        # Cleanup temp file
        os.unlink(temp_path)

        # Convert Pydantic Ontology into dict
        ontology_data = None
        if result_state.get("ontology"):
            ontology_data = result_state["ontology"].model_dump()

        # Mark as 100% complete
        upload_progress = {"percent": 100, "message": "Successfully Processed"}

        return {
            "success": True,
            "filename": file.filename,
            "ontology": ontology_data,
            "status_messages": result_state.get("status_messages", [])
        }

    except Exception as e:
        upload_progress = {"percent": 0, "message": "Error: Ingestion failed"}
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@app.get("/api/graph")
def get_graph():
    """Fetches nodes & relationships from Neo4j, structured specifically for react-force-graph."""
    if not Neo4jConnection.verify_connection():
        raise HTTPException(status_code=503, detail="Neo4j Database is not connected.")

    query = "MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 200"
    records = Neo4jConnection.execute_query(query)

    nodes_dict = {}
    links = []

    if records:
        for record in records:
            source_node = record['n']
            target_node = record['m']
            rel = record['r']

            # Safe extraction logic
            source_id = source_node.get('name', 'Unknown') if isinstance(source_node, dict) else source_node.get('name')
            target_id = target_node.get('name', 'Unknown') if isinstance(target_node, dict) else target_node.get('name')

            source_group = source_node.get("labels", ["Entity"])[0] if isinstance(source_node, dict) else (list(source_node.labels)[0] if hasattr(source_node, 'labels') else "Entity")
            target_group = target_node.get("labels", ["Entity"])[0] if isinstance(target_node, dict) else (list(target_node.labels)[0] if hasattr(target_node, 'labels') else "Entity")

            rel_type = rel.get("type", "RELATED_TO") if isinstance(rel, dict) else getattr(rel, 'type', "RELATED_TO")

            # Collect Unique Nodes
            if source_id and source_id not in nodes_dict:
                nodes_dict[source_id] = {"id": source_id, "name": source_id, "group": source_group}
            if target_id and target_id not in nodes_dict:
                nodes_dict[target_id] = {"id": target_id, "name": target_id, "group": target_group}

            # Collect Link
            if source_id and target_id:
                links.append({
                    "source": source_id,
                    "target": target_id,
                    "label": rel_type
                })

    return {
        "nodes": list(nodes_dict.values()),
        "links": links
    }


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Hybrid Search Chat endpoint combining FAISS, Neo4j graph context, 5-turn history, and global graph overview (Streaming)."""
    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty.")

    try:
        # 1. Fetch Global Knowledge Graph Overview (Macro-awareness)
        global_graph_summary = Neo4jConnection.get_graph_summary()

        # 2. Extract STRICTLY the LAST 5 messages for memory and context resolution
        last_5_history = request.history[-5:] if request.history else []

        # 3. Contextualize search query for ambiguous prompts (e.g., "tell me more about it")
        search_query = request.prompt
        if last_5_history:
            last_user_msg = [m.content for m in last_5_history if m.role == 'user']
            if last_user_msg:
                search_query = f"{last_user_msg[-1]} {request.prompt}"

        # 4. Retrieve local vector & graph context
        retriever = HybridRetriever(vector_store)
        context = retriever.retrieve(search_query)
        agent = AnswerGenerationAgent()

        async def generate():
            # Send retrieved context chunks first so the UI can display sources
            yield f"data: {json.dumps({'type': 'context', 'content': context.formatted_context})}\n\n"
            
            # Stream the answer with global graph summary and the last 5 messages
            # 🟢 FIX: Updated keyword arguments to match AnswerGenerationAgent signature
            for chunk in agent.stream_answer(
                question=request.prompt,       # Changed from prompt=
                hybrid_context=context,        # Changed from context=
                history=last_5_history,
                graph_summary=global_graph_summary
            ):
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
                
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat generation failed: {str(e)}")