import streamlit as st
import os
import tempfile
from pyvis.network import Network
import streamlit.components.v1 as components
from dotenv import load_dotenv

# Load Env early
load_dotenv()

from config.settings import settings
from utils.workflow import IngestionWorkflow
from retrieval.vector_store import FAISSVectorStore
from embeddings.embedder import Embedder
from retrieval.hybrid_retriever import HybridRetriever
from agents.answer_agent import AnswerGenerationAgent
from graph.neo4j_connection import Neo4jConnection

# ==========================================
# PAGE CONFIGURATION & UI UPGRADES
# ==========================================
st.set_page_config(page_title="Dynamic Ontology RAG", page_icon="🕸️", layout="wide")

# Modern CSS with explicit dark-text fixes for Streamlit chat components
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    .stApp { 
        font-family: 'Inter', sans-serif; 
        background-color: #f8f9fa;
        color: #0f172a;
    }
    
    /* FIX CHATBOT TEXT INVISIBILITY */
    div[data-testid="stChatMessage"] {
        background-color: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 12px !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.03) !important;
        padding: 12px 16px !important;
    }

    div[data-testid="stChatMessage"] p, 
    div[data-testid="stChatMessage"] span, 
    div[data-testid="stChatMessage"] div,
    div[data-testid="stChatMessage"] li {
        color: #1e293b !important;
        font-size: 15px !important;
    }

    /* FIX CHAT INPUT TEXT VISIBILITY */
    div[data-testid="stChatInput"] textarea {
        color: #0f172a !important;
        background-color: #ffffff !important;
    }

    /* Connection Status Badges */
    .status-badge {
        display: inline-block;
        padding: 6px 16px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 14px;
        margin-bottom: 20px;
    }
    .neo4j-success { background-color: #d1e7dd; color: #0f5132; border: 1px solid #badbcc; }
    .neo4j-error { background-color: #f8d7da; color: #842029; border: 1px solid #f5c2c7; }
    
    /* Custom Card Styling for Ontology */
    .ontology-card {
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border-left: 5px solid #4F46E5;
        margin-bottom: 15px;
    }
    
    .relation-card {
        background: white;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border-left: 5px solid #10B981;
        margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# SESSION STATE INITIALIZATION
# ==========================================
if "vector_store" not in st.session_state:
    st.session_state.vector_store = FAISSVectorStore(Embedder())
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "ontology" not in st.session_state:
    st.session_state.ontology = None
if "ingestion_status" not in st.session_state:
    st.session_state.ingestion_status = []

# ==========================================
# SIDEBAR NAVIGATION & UPLOAD
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/8652/8652205.png", width=60)
    st.title("System Config")
    st.divider()
    
    # Neo4j Connection Check
    is_connected = Neo4jConnection.verify_connection()
    if is_connected:
        st.markdown("<div class='status-badge neo4j-success'>🟢 Neo4j Connected</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='status-badge neo4j-error'>🔴 Neo4j Disconnected</div>", unsafe_allow_html=True)
        st.error("Please check your .env settings and ensure Neo4j is running.")

    st.divider()
    st.subheader("📄 Knowledge Base Upload")
    uploaded_file = st.file_uploader("Upload PDF, DOCX, or TXT", type=["pdf", "docx", "txt"])
    
    if uploaded_file and st.button("Process Document", type="primary", disabled=not is_connected, use_container_width=True):
        with st.status("🚀 Processing Knowledge Pipeline...", expanded=True) as status:
            st.write("Extracting text...")
            
            # Save temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tf:
                tf.write(uploaded_file.read())
                temp_path = tf.name
            
            st.write("Running LangGraph Agents...")
            # Run Workflow
            workflow = IngestionWorkflow(st.session_state.vector_store)
            result_state = workflow.run(temp_path)
            
            st.session_state.ontology = result_state["ontology"]
            st.session_state.ingestion_status = result_state["status_messages"]
            os.unlink(temp_path)
            status.update(label="✅ Ingestion Complete!", state="complete", expanded=False)
            st.balloons()

# ==========================================
# MAIN WORKSPACE TABS
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs(["📊 Document Ontology", "🕸️ Interactive Graph", "💬 RAG Chat", "⚙️ System Logs"])

# --- TAB 1: ONTOLOGY ---
with tab1:
    st.header("Generated Domain Ontology")
    st.caption("The AI dynamically extracted these structural rules from your document.")
    
    if st.session_state.ontology:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🏛️ Discovered Classes")
            for cls in st.session_state.ontology.classes:
                st.markdown(f"""
                <div class="ontology-card">
                    <h4 style="margin:0; color:#4F46E5;">{cls.name}</h4>
                    <p style="margin:5px 0 0 0; color:#4b5563; font-size: 14px;">{cls.description}</p>
                </div>
                """, unsafe_allow_html=True)
        with col2:
            st.subheader("🔗 Valid Relationships")
            for rel in st.session_state.ontology.relations:
                st.markdown(f"""
                <div class="relation-card">
                    <p style="margin:0; font-size: 14px; color:#1e293b;"><b>{rel.domain}</b> ➡️ <span style="color:#10B981; font-weight:bold;">[{rel.name}]</span> ➡️ <b>{rel.range}</b></p>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("👈 Upload and process a document in the sidebar to generate the dynamic ontology.")

# --- TAB 2: KNOWLEDGE GRAPH ---
with tab2:
    st.header("Interactive Knowledge Graph")
    st.caption("Visualizing the extracted entities and their relationships stored in Neo4j.")
    
    if st.button("🔄 Refresh Graph Visualization", type="secondary"):
        if is_connected:
            with st.spinner("Fetching data from Neo4j..."):
                query = "MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 150"
                records = Neo4jConnection.execute_query(query)
                
                if records:
                    net = Network(height="600px", width="100%", bgcolor="#ffffff", font_color="#333333", directed=True)
                    
                    for record in records:
                        source_node = record['n']
                        target_node = record['m']
                        rel = record['r']
                        
                        # SAFE EXTRACTION: Handles both dicts and Neo4j Node objects
                        source_id = source_node.get('name', 'Unknown') if isinstance(source_node, dict) else source_node.get('name')
                        target_id = target_node.get('name', 'Unknown') if isinstance(target_node, dict) else target_node.get('name')
                        
                        source_title = source_node.get("labels", ["Entity"])[0] if isinstance(source_node, dict) else (list(source_node.labels)[0] if hasattr(source_node, 'labels') else "Entity")
                        target_title = target_node.get("labels", ["Entity"])[0] if isinstance(target_node, dict) else (list(target_node.labels)[0] if hasattr(target_node, 'labels') else "Entity")
                        
                        rel_type = rel.get("type", "RELATED_TO") if isinstance(rel, dict) else getattr(rel, 'type', "RELATED_TO")
                        
                        # Add nodes and edges to PyVis
                        net.add_node(source_id, label=source_id, title=source_title, color="#4F46E5")
                        net.add_node(target_id, label=target_id, title=target_title, color="#10B981")
                        net.add_edge(source_id, target_id, label=rel_type, color="#9CA3AF")
                    
                    # Save and render
                    net.save_graph("graph.html")
                    HtmlFile = open("graph.html", 'r', encoding='utf-8')
                    components.html(HtmlFile.read(), height=650)
                else:
                    st.warning("The graph is currently empty. Process a document first.")
        else:
            st.error("Neo4j not connected. Cannot visualize graph.")

# --- TAB 3: CHAT ---
with tab3:
    st.header("Ontology-Aware Chat")
    st.caption("Ask questions. The AI merges FAISS vector similarity with Neo4j exact graph relationships.")
    
    # Display Chat History
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    if prompt := st.chat_input("E.g., What are the main entities and relationships described?"):
        # Add user message
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        with st.chat_message("assistant"):
            with st.spinner("Retrieving hybrid context (Graph + Vector)..."):
                try:
                    retriever = HybridRetriever(st.session_state.vector_store)
                    context = retriever.retrieve(prompt)
                    
                    agent = AnswerGenerationAgent()
                    response = agent.generate_answer(prompt, context)
                    
                    st.markdown(response)
                    
                    # Context Expander
                    with st.expander("🔍 View Retrieved Context Sources"):
                        st.text(context.formatted_context)
                        
                    st.session_state.chat_history.append({"role": "assistant", "content": response})
                except Exception as e:
                    st.error(f"Error during retrieval: {str(e)}")

# --- TAB 4: SYSTEM STATUS ---
with tab4:
    st.header("System Logs & Database Status")
    
    colA, colB = st.columns(2)
    with colA:
        st.metric("Total Document Chunks (FAISS)", len(st.session_state.vector_store.chunks))
    with colB:
        st.metric("Neo4j Status", "Active" if is_connected else "Offline")
        
    st.divider()
    st.subheader("Pipeline Execution Logs")
    if not st.session_state.ingestion_status:
        st.info("No logs yet. Upload a document to view agent execution steps.")
    for msg in st.session_state.ingestion_status:
        st.code(msg, language="bash")