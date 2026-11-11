"""
Centralized pytest configuration and reusable fixtures for kg-research-assistant backend tests.
Ensures zero live database dependencies, zero paid/external LLM API calls, and instant test execution.
"""
import os
import sys

# Guarantee test environment flag is set immediately before any app modules are imported
os.environ["TESTING"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
import atexit
import logging
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock
import pytest

# Silence httpcore / httpx / huggingface_hub debug logs that can write to closed stdout/stderr at teardown
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("huggingface_hub").setLevel(logging.WARNING)

# Prevent huggingface_hub close_session from executing via atexit after pytest closes stdout/stderr
try:
    from huggingface_hub.utils import _http
    if hasattr(_http, "close_session"):
        atexit.unregister(_http.close_session)
except Exception:
    pass

# Ensure backend root is on sys.path
backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

# ------------------------------------------------------------------------------
# Prevent Starlette / FastAPI TestClient from executing live database connection lifespan
# ------------------------------------------------------------------------------
@asynccontextmanager
async def _noop_lifespan(application):
    yield

try:
    from app.main import app
    app.router.lifespan_context = _noop_lifespan
    app.lifespan_context = _noop_lifespan
except Exception:
    pass

from app.schemas.graph import KnowledgeGraphExtractionResult, GraphEntity, GraphRelationship, EntityType, RelationType


# ==============================================================================
# Auto-Use Fixtures: Disable Lifespan DB Connections & External LLM Calls Globally
# ==============================================================================

@pytest.fixture(autouse=True)
def mock_db_lifespan(monkeypatch):
    """
    Prevents TestClient and FastAPI lifespan from attempting live socket connections
    to PostgreSQL, Neo4j, or Redis during unit and API test execution.
    """
    monkeypatch.setattr("app.main.init_postgres_extensions", AsyncMock(return_value=None))
    monkeypatch.setattr("app.database.postgres.init_postgres_extensions", AsyncMock(return_value=None))
    monkeypatch.setattr("app.database.neo4j.neo4j_client.connect", AsyncMock(return_value=None))
    monkeypatch.setattr("app.database.neo4j.neo4j_client.close", AsyncMock(return_value=None))
    monkeypatch.setattr("app.database.redis.redis_client.connect", AsyncMock(return_value=None))
    monkeypatch.setattr("app.database.redis.redis_client.close", AsyncMock(return_value=None))
    monkeypatch.setattr("app.services.paper_service.PaperService.process_paper_background", AsyncMock(return_value=None))


@pytest.fixture(autouse=True)
def guard_external_llm(monkeypatch):
    """
    Guarantees no real external API requests are made to Groq, Google Gemini, or Ollama.
    """
    mock_llm = MagicMock()
    mock_llm.provider_name = "mock_provider"
    mock_llm.generate_text = AsyncMock(return_value="Mocked grounded answer [Paper: p_001, Page: 1].")
    mock_llm.generate = AsyncMock(return_value="Mocked grounded answer [Paper: p_001, Page: 1].")
    mock_llm.generate_structured = AsyncMock(return_value=KnowledgeGraphExtractionResult(
        entities=[
            GraphEntity(name="Transformer", type=EntityType.CONCEPT, description="Attention architecture"),
            GraphEntity(name="BERT", type=EntityType.MODEL, description="Language representation model")
        ],
        relationships=[
            GraphRelationship(source_entity="BERT", target_entity="Transformer", relation_type=RelationType.USES_METHOD)
        ]
    ))

    monkeypatch.setattr("app.llm.get_llm_provider", lambda *args, **kwargs: mock_llm)
    monkeypatch.setattr("app.graph.extractor.get_llm_provider", lambda *args, **kwargs: mock_llm)
    monkeypatch.setattr("app.rag.chat_service.get_llm_provider", lambda *args, **kwargs: mock_llm)


# ==============================================================================
# Reusable Database & Service Mock Fixtures
# ==============================================================================

@pytest.fixture
def mock_async_db_session():
    """Provides a fully mocked SQLAlchemy AsyncSession."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def mock_neo4j_session():
    """Provides a mocked Neo4j session context manager."""
    session = AsyncMock()
    session.run = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def mock_redis():
    """Provides a mocked Redis async client."""
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock(return_value=True)
    redis.setex = AsyncMock(return_value=True)
    redis.delete = AsyncMock(return_value=True)
    redis.ping = AsyncMock(return_value=True)
    return redis


@pytest.fixture
def test_client():
    """Provides a FastAPI TestClient with standard dependency overrides."""
    from app.main import app
    from app.database.postgres import get_db

    mock_session = AsyncMock()

    async def _override_get_db():
        yield mock_session

    app.dependency_overrides[get_db] = _override_get_db
    from fastapi.testclient import TestClient
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


# ==============================================================================
# Reusable Data Fixtures
# ==============================================================================

@pytest.fixture
def sample_pdf_path(tmp_path):
    """
    Creates a temporary valid 2-page academic PDF with standard headings using PyMuPDF.
    """
    import fitz  # PyMuPDF

    doc = fitz.open()
    # Page 1
    p1 = doc.new_page()
    p1.insert_text(
        fitz.Point(50, 72),
        "Attention Is All You Need\n\n"
        "Abstract\n\n"
        "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks.\n\n"
        "1. Introduction\n\n"
        "Recurrent neural networks, long short-term memory and gated recurrent neural networks have been firmly established."
    )
    # Page 2
    p2 = doc.new_page()
    p2.insert_text(
        fitz.Point(50, 72),
        "2. Model Architecture\n\n"
        "The Transformer follows this overall architecture using stacked self-attention and point-wise layers.\n\n"
        "3. References\n\n"
        "[1] Vaswani et al. 2017. Attention is all you need."
    )
    pdf_file = tmp_path / "sample_academic_paper.pdf"
    doc.save(str(pdf_file))
    doc.close()
    return str(pdf_file)


@pytest.fixture
def empty_pdf_path(tmp_path):
    """Creates a temporary empty PDF file."""
    import fitz

    doc = fitz.open()
    doc.new_page()  # Page without text
    pdf_file = tmp_path / "empty_paper.pdf"
    doc.save(str(pdf_file))
    doc.close()
    return str(pdf_file)


@pytest.fixture
def corrupt_pdf_path(tmp_path):
    """Creates an invalid/corrupted PDF file."""
    corrupt_file = tmp_path / "corrupt_paper.pdf"
    corrupt_file.write_bytes(b"%PDF-1.4\nCorrupted content completely invalid binary data")
    return str(corrupt_file)


@pytest.fixture
def sample_graph_data():
    """Provides a sample KnowledgeGraphExtractionResult."""
    return KnowledgeGraphExtractionResult(
        entities=[
            GraphEntity(name="Transformer", type=EntityType.CONCEPT, description="Attention architecture"),
            GraphEntity(name="BERT", type=EntityType.MODEL, description="Language representation model"),
            GraphEntity(name="GLUE", type=EntityType.DATASET, description="General Language Understanding Evaluation benchmark")
        ],
        relationships=[
            GraphRelationship(source_entity="BERT", target_entity="Transformer", relation_type=RelationType.USES_METHOD, description="BERT uses Transformer"),
            GraphRelationship(source_entity="BERT", target_entity="GLUE", relation_type=RelationType.EVALUATED_ON, description="Evaluated on GLUE")
        ]
    )


def pytest_sessionfinish(session, exitstatus):
    """Cleanly close any open huggingface / httpx sessions while stdout/stderr are still valid."""
    try:
        from huggingface_hub.utils import _http
        if hasattr(_http, "close_session"):
            _http.close_session()
    except Exception:
        pass
