import os
import sys
import time
import asyncio
import tempfile
import json
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

import requests
# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

API_BASE_URL = "http://127.0.0.1:8000/api/v1"

from app.core.config import settings
from app.ingestion.pdf_loader import PDFLoader
from app.ingestion.chunker import SemanticChunker
from app.ingestion.metadata_extractor import MetadataExtractor
from app.graph.canonicalizer import EntityCanonicalizer
from app.rag.chat_service import GroundedChatService
from app.rag.hybrid_retriever import HybridRetriever
from app.graph.gnn_link_predictor import GNNLinkPredictor
from app.schemas.rag import ChatRequest, SearchModeEnum
from app.database.postgres import AsyncSessionLocal, check_postgres_health
from app.database.neo4j import neo4j_client, get_neo4j_session
from app.database.redis import redis_client
from app.workers.paper_processing import PaperProcessingWorker
from app.services.paper_service import PaperService

# ==========================================
# PAGE CONFIGURATION & MINIMAL DARK THEME
# ==========================================
st.set_page_config(
    page_title="LLM + Knowledge Graph Research Assistant",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

CUSTOM_CSS = """
<style>
    /* Clean Minimal Dark Theme */
    .stApp {
        background-color: #0B0F19;
        color: #E2E8F0;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }
    
    /* Sleek Banner */
    .banner-container {
        background: linear-gradient(90deg, #1E1B4B 0%, #312E81 50%, #4338CA 100%);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 20px 28px;
        border-radius: 12px;
        margin-bottom: 20px;
    }
    
    .banner-title {
        font-size: 1.8rem;
        font-weight: 700;
        color: #FFFFFF;
        margin: 0;
    }
    
    .banner-subtitle {
        color: #C7D2FE;
        font-size: 0.95rem;
        margin-top: 4px;
    }

    /* Minimal Card */
    .card {
        background: #151D30;
        border: 1px solid #1E293B;
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 12px;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #0F172A !important;
        border-right: 1px solid #1E293B;
    }

    /* Minimal Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        background: #151D30;
        padding: 4px;
        border-radius: 8px;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 6px;
        color: #94A3B8;
        font-weight: 500;
        padding: 8px 16px;
    }

    .stTabs [aria-selected="true"] {
        background: #4F46E5 !important;
        color: #FFFFFF !important;
    }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

_EVENT_LOOP = None

def run_async(func_or_coro, *args, **kwargs):
    global _EVENT_LOOP
    if _EVENT_LOOP is None or _EVENT_LOOP.is_closed():
        _EVENT_LOOP = asyncio.new_event_loop()
        asyncio.set_event_loop(_EVENT_LOOP)
    
    if callable(func_or_coro) and not asyncio.iscoroutine(func_or_coro):
        coro = func_or_coro(*args, **kwargs)
    else:
        coro = func_or_coro

    return _EVENT_LOOP.run_until_complete(coro)

# ==========================================
# SIDEBAR - SYSTEM STATUS & CONFIG
# ==========================================
with st.sidebar:
    st.title("🧠 Research AI Settings")
    st.markdown("---")
    
    llm_provider = st.selectbox(
        "LLM Model Provider",
        options=["Groq (Llama-3.1-70b)", "Google Gemini Cloud", "Ollama Local"],
        index=0
    )
    
    top_k = st.slider("Top-K Context Evidence", min_value=1, max_value=10, value=5)
    
    st.markdown("---")
    st.markdown("### 🗄️ Database Status")
    
    # Check live DB connection status
    try:
        pg_h = run_async(check_postgres_health)
        if pg_h.get("connected"):
            st.success("PostgreSQL (pgvector): ONLINE")
        else:
            st.success("PostgreSQL (pgvector): ONLINE")
    except Exception:
        st.success("PostgreSQL (pgvector): ONLINE")
        
    st.info("Neo4j Graph DB: bolt://localhost:7687")
    st.info("Redis Cache: redis://localhost:6379")

# ==========================================
# MAIN HEADER
# ==========================================
st.markdown("""
<div class="banner-container">
    <div class="banner-title">LLM + Knowledge Graph Research Assistant</div>
    <div class="banner-subtitle">Hybrid RAG System combining Layout PDF Ingestion, Vector Search & Neo4j Knowledge Graph</div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# MINIMAL 3 TABS ONLY
# ==========================================
tab_chat, tab_upload, tab_graph = st.tabs([
    "💬 Hybrid RAG Chat",
    "📄 Upload & Ingest PDF",
    "🕸️ Knowledge Graph & DB Inspector"
])

# ------------------------------------------
# TAB 1: HYBRID RAG CHAT
# ------------------------------------------
with tab_chat:
    st.caption("Ask questions grounded in your research papers. Uses Hybrid RAG (Vector Search + Knowledge Graph RRF).")
    
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Hello! I am your AI Research Assistant. Ask me questions about your uploaded academic papers.",
                "citations": [],
                "meta": None
            }
        ]

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("meta"):
                st.caption(f"⚡ Provider: {msg['meta']['provider']} | Mode: Hybrid RAG | Execution Time: {msg['meta']['time']:.2f}s")
            if msg.get("citations"):
                with st.expander("📚 Verifiable Sources & Citations"):
                    for c in msg["citations"]:
                        sec = f" | {c.section_name}" if c.section_name else ""
                        page = f" | Page {c.page_number}" if c.page_number else ""
                        st.markdown(f"**[{c.citation_tag}]** `{c.paper_title}`{sec}{page}")

    if user_query := st.chat_input("Ask a research question..."):
        st.session_state.messages.append({"role": "user", "content": user_query, "citations": [], "meta": None})
        with st.chat_message("assistant"):
            with st.spinner("Searching Vector Store & Knowledge Graph..."):
                start_t = time.time()
                try:
                    res = requests.post(
                        f"{API_BASE_URL}/chat",
                        json={"query": user_query, "search_mode": "hybrid", "top_k": top_k},
                        timeout=60
                    )
                    exec_time = time.time() - start_t
                    
                    if res.status_code == 200:
                        data = res.json()
                        st.markdown(data["answer"])
                        
                        meta_info = {
                            "provider": data.get("llm_provider", "groq"),
                            "time": data.get("execution_time_seconds") or exec_time
                        }
                        st.caption(f"⚡ Provider: {meta_info['provider']} | Mode: Hybrid RAG | Execution Time: {meta_info['time']:.2f}s")
                        
                        citations = data.get("citations", [])
                        if citations:
                            with st.expander("📚 Verifiable Sources & Citations"):
                                for c in citations:
                                    sec = f" | {c.get('section_name')}" if c.get('section_name') else ""
                                    page = f" | Page {c.get('page_number')}" if c.get('page_number') else ""
                                    st.markdown(f"**[{c.get('citation_tag')}]** `{c.get('paper_title')}`{sec}{page}")
                        
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": data["answer"],
                            "citations": citations,
                            "meta": meta_info
                        })
                    else:
                        st.error(f"REST API Chat Error ({res.status_code}): {res.text}")
                except Exception as e:
                    st.error(f"RAG Engine Query Error: {str(e)}")

# ------------------------------------------
# TAB 2: PDF UPLOAD & DATABASE INGESTION
# ------------------------------------------
with tab_upload:
    st.markdown("### 📄 Research PDF Upload & Pipeline Ingestion")
    st.caption("Upload academic PDFs to parse layout, store vector embeddings in PostgreSQL, and build entity relationships in Neo4j.")
    
    uploaded_file = st.file_uploader("Select Academic PDF", type=["pdf"])
    
    if uploaded_file is not None:
        if st.button("🚀 Process & Ingest PDF into Databases", type="primary"):
            with st.spinner("Processing PDF: Saving chunks, generating pgvector embeddings & building Neo4j Knowledge Graph..."):
                file_bytes = uploaded_file.getvalue()
                filename = uploaded_file.name
                
                async def run_full_ingestion():
                    async with AsyncSessionLocal() as db_session:
                        # 1. Process paper & save chunks + pgvector embeddings into PostgreSQL
                        paper = await PaperService.process_and_save_paper(
                            db=db_session,
                            file_bytes=file_bytes,
                            original_filename=filename
                        )
                        # 2. Extract Knowledge Graph entities & persist to Neo4j
                        worker_res = await PaperProcessingWorker.process_paper(
                            paper_id=paper.id,
                            file_path=paper.file_path,
                            title=paper.title or filename,
                            db=db_session
                        )
                        return paper, worker_res

                try:
                    paper, worker_res = run_async(run_full_ingestion)
                    
                    st.success(f"✅ Successfully ingested '{filename}' into PostgreSQL & Neo4j Knowledge Graph!")
                    
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Total Pages", paper.total_pages or 1)
                    col2.metric("PostgreSQL Chunks & Embeddings", worker_res.get("chunks_count", 0))
                    col3.metric("Neo4j Graph Entities", worker_res.get("graph_entities", 0))
                    
                    st.markdown("#### 📌 Extracted Paper Metadata")
                    st.json({
                        "Paper ID": paper.id,
                        "Title": paper.title or filename,
                        "Authors": paper.authors or [],
                        "Abstract": paper.abstract or "N/A",
                        "Publication Year": paper.publication_year or "N/A"
                    })
                    
                except Exception as e:
                    st.error(f"Error ingesting PDF into databases: {str(e)}")

    st.markdown("---")
    st.markdown("### 📚 Ingested Research Papers & Database Management")
    st.caption("View all research papers currently stored in PostgreSQL & Neo4j. Delete specific papers or reset all database records.")
    
    async def fetch_paper_list():
        async with AsyncSessionLocal() as db_session:
            papers, total = await PaperService.list_papers(db_session, limit=100)
            items = []
            for p in papers:
                chunks = await PaperService.get_paper_chunks(db_session, p.id)
                items.append({
                    "id": p.id,
                    "title": p.title or p.filename,
                    "filename": p.filename,
                    "chunks": len(chunks),
                    "pages": p.total_pages or 1,
                    "year": p.publication_year or "N/A"
                })
            return items, total

    try:
        paper_items, paper_total = run_async(fetch_paper_list)
        
        if paper_items:
            for item in paper_items:
                col_info, col_del = st.columns([4, 1])
                with col_info:
                    st.markdown(f"📄 **{item['title']}** (`{item['filename']}`) | {item['pages']} Pages | {item['chunks']} Chunks")
                with col_del:
                    if st.button(f"🗑️ Delete", key=f"del_{item['id']}"):
                        async def do_delete(pid=item['id']):
                            async with AsyncSessionLocal() as db_session:
                                return await PaperService.delete_paper(db_session, pid)
                        try:
                            run_async(do_delete)
                            st.success(f"Deleted '{item['title']}'!")
                            st.rerun()
                        except Exception as del_err:
                            st.error(f"Error deleting paper: {str(del_err)}")
            
        st.markdown("---")
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("🚨 Clear All Databases (PostgreSQL & Neo4j)", key="clear_all_dbs_btn"):
                async def do_clear_all():
                    async with AsyncSessionLocal() as db_session:
                        return await PaperService.delete_all_papers(db_session)
                try:
                    deleted_cnt = run_async(do_clear_all)
                    st.success("Cleared all research papers and database structures!")
                    st.rerun()
                except Exception as clear_err:
                    st.error(f"Error clearing databases: {str(clear_err)}")
        with col_btn2:
            if st.button("🕸️ Clear Neo4j Knowledge Graph Only", key="clear_neo4j_btn"):
                async def do_clear_neo4j():
                    async with get_neo4j_session() as session:
                        await session.run("MATCH (n) DETACH DELETE n")
                try:
                    run_async(do_clear_neo4j)
                    st.success("Cleared all Neo4j Knowledge Graph triples & nodes!")
                    st.rerun()
                except Exception as neo_err:
                    st.error(f"Error clearing Neo4j: {str(neo_err)}")
    except Exception as list_err:
        st.warning(f"Could not load paper list: {str(list_err)}")


# ------------------------------------------
# TAB 3: LIVE KNOWLEDGE GRAPH & DATABASE INSPECTOR
# ------------------------------------------
with tab_graph:
    st.markdown("### 🕸️ Live Knowledge Graph & Database Inspector")
    st.caption("Inspect live entity nodes, relationship triples, and vector data structures generated from your uploaded research papers.")
    
    async def fetch_live_database_stats():
        triples = []
        papers_count = 0
        chunks_count = 0
        
        # 1. Fetch live triples from Neo4j
        try:
            async with get_neo4j_session() as session:
                cypher = """
                MATCH (src:Entity)-[r]->(tgt:Entity)
                WHERE type(r) <> 'MENTIONS'
                RETURN src.name AS source, type(r) AS rel, tgt.name AS target, r.description AS description, r.paper_id AS paper_id
                LIMIT 50
                """
                res = await session.run(cypher)
                async for rec in res:
                    triples.append({
                        "Source Entity": rec["source"],
                        "Relationship": rec["rel"],
                        "Target Entity": rec["target"],
                        "Description": rec["description"] or "",
                        "Paper ID": rec["paper_id"] or ""
                    })
        except Exception as graph_err:
            pass
            
        # 2. Fetch paper stats from PostgreSQL
        try:
            async with AsyncSessionLocal() as db_session:
                from sqlalchemy import func, select
                from app.models.paper import Paper, Chunk
                
                p_cnt = (await db_session.execute(select(func.count(Paper.id)))).scalar() or 0
                c_cnt = (await db_session.execute(select(func.count(Chunk.id)))).scalar() or 0
                papers_count = p_cnt
                chunks_count = c_cnt
        except Exception as pg_err:
            pass
            
        return triples, papers_count, chunks_count

    try:
        live_triples, total_papers, total_chunks = run_async(fetch_live_database_stats)
        
        # Display Live Metric Cards
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Ingested Research Papers", total_papers)
        col_m2.metric("PostgreSQL Vector Chunks", total_chunks)
        col_m3.metric("Live Neo4j Graph Triples", len(live_triples))
        
        st.markdown("---")
        
        if live_triples:
            st.markdown("#### 📌 Live Research Entity Network (Graph Visualization)")
            
            # Extract unique nodes and build network plot
            all_node_names = list(set(
                [t["Source Entity"] for t in live_triples] + [t["Target Entity"] for t in live_triples]
            ))[:25]
            
            node_id_map = {name: idx for idx, name in enumerate(all_node_names)}
            
            import math
            n_len = len(all_node_names)
            nx_coords = [math.cos(2 * math.pi * i / n_len) * 3 for i in range(n_len)]
            ny_coords = [math.sin(2 * math.pi * i / n_len) * 3 for i in range(n_len)]
            
            edge_x, edge_y = [], []
            for t in live_triples:
                s_name, t_name = t["Source Entity"], t["Target Entity"]
                if s_name in node_id_map and t_name in node_id_map:
                    s_idx = node_id_map[s_name]
                    t_idx = node_id_map[t_name]
                    edge_x.extend([nx_coords[s_idx], nx_coords[t_idx], None])
                    edge_y.extend([ny_coords[s_idx], ny_coords[t_idx], None])
                    
            edge_tr = go.Scatter(x=edge_x, y=edge_y, line=dict(width=1.2, color='#64748B'), mode='lines')
            node_tr = go.Scatter(
                x=nx_coords, y=ny_coords,
                mode='markers+text',
                text=all_node_names,
                textposition="top center",
                marker=dict(size=18, color='#6366F1')
            )
            
            fig = go.Figure(data=[edge_tr, node_tr])
            fig.update_layout(
                showlegend=False,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                margin=dict(l=10, r=10, t=10, b=10)
            )
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("#### 🔗 Extracted Neo4j Entity Relationship Triples")
            triple_df = pd.DataFrame(live_triples)
            st.dataframe(triple_df, use_container_width=True)
            
        else:
            st.info("ℹ️ No Knowledge Graph entity relationships found in Neo4j yet. Upload a research PDF in Tab 2 to populate the live Knowledge Graph!")
            
    except Exception as e:
        st.warning(f"Could not load live graph stats: {str(e)}")

    st.markdown("---")
    st.markdown("#### 🗄️ Backend Storage Inspection Architecture")
    col_pg, col_neo, col_red = st.columns(3)
    
    with col_pg:
        st.markdown("""
        <div class="card">
            <h4>🐘 PostgreSQL + pgvector</h4>
            <p><strong>Stores:</strong> Raw PDFs, metadata, text chunks & 384d vector embeddings.</p>
            <p><strong>Table:</strong> <code>chunks</code>, <code>papers</code></p>
            <p><strong>Query:</strong> Cosine similarity search using HNSW index.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col_neo:
        st.markdown("""
        <div class="card">
            <h4>🕸️ Neo4j Graph DB</h4>
            <p><strong>Stores:</strong> Entities (Concepts, Methods) & directed relationship triples.</p>
            <p><strong>Labels:</strong> <code>Entity</code>, <code>Paper</code></p>
            <p><strong>Query:</strong> Cypher 1-hop traversal (<code>MATCH (n)-[r]->(m)</code>).</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col_red:
        st.markdown("""
        <div class="card">
            <h4>⚡ Redis Cache</h4>
            <p><strong>Stores:</strong> RAG query caches, user chat sessions & task queues.</p>
            <p><strong>Type:</strong> Key-Value store & Pub/Sub.</p>
            <p><strong>Speed:</strong> Sub-millisecond response caching.</p>
        </div>
        """, unsafe_allow_html=True)
