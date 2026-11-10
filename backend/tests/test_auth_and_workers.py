import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.database.postgres import get_db
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    decode_access_token
)
from app.workers.paper_processing import PaperProcessingWorker

client = TestClient(app)


def test_password_hashing_and_jwt_tokens():
    """
    Tests password hashing, verification, and JWT token encoding/decoding.
    """
    raw_password = "SuperSecretPassword123!"
    hashed = get_password_hash(raw_password)

    assert hashed != raw_password
    assert verify_password(raw_password, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

    payload = {"sub": "user@example.com", "user_id": "usr_123"}
    token = create_access_token(payload)
    assert token is not None and isinstance(token, str)

    decoded = decode_access_token(token)
    assert decoded is not None
    assert decoded["sub"] == "user@example.com"
    assert decoded["user_id"] == "usr_123"


def test_invalid_token_decoding():
    """
    Tests handling of invalid or corrupted JWT tokens.
    """
    invalid_token = "invalid.jwt.token"
    decoded = decode_access_token(invalid_token)
    assert decoded is None


def test_user_registration_endpoint():
    """
    Tests POST /api/v1/auth/register endpoint logic using FastAPI dependency override.
    """
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_session.execute.return_value = mock_result

    async def mock_get_db_override():
        yield mock_session

    app.dependency_overrides[get_db] = mock_get_db_override

    try:
        reg_payload = {
            "email": "researcher@example.com",
            "full_name": "Dr. Researcher",
            "password": "Password123!"
        }

        response = client.post("/api/v1/auth/register", json=reg_payload)
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "researcher@example.com"
        assert data["full_name"] == "Dr. Researcher"
        assert "id" in data
        assert "hashed_password" not in data
    finally:
        app.dependency_overrides.clear()


def test_user_login_endpoint():
    """
    Tests POST /api/v1/auth/login endpoint for OAuth2 token generation.
    """
    mock_session = AsyncMock()
    mock_user = MagicMock()
    mock_user.id = "usr_001"
    mock_user.email = "researcher@example.com"
    mock_user.hashed_password = get_password_hash("Password123!")
    
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_user
    mock_session.execute.return_value = mock_result

    async def mock_get_db_override():
        yield mock_session

    app.dependency_overrides[get_db] = mock_get_db_override

    try:
        login_data = {
            "email": "researcher@example.com",
            "password": "Password123!"
        }

        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 200
        token_response = response.json()
        assert "access_token" in token_response
        assert token_response["token_type"] == "bearer"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
@patch("app.workers.paper_processing.PDFLoader.extract_pages")
@patch("app.workers.paper_processing.Neo4jGraphBuilder.persist_paper_graph")
async def test_paper_processing_worker(mock_persist, mock_extract):
    """
    Tests PaperProcessingWorker background task pipeline.
    """
    mock_page = MagicMock()
    mock_page.page_number = 1
    mock_page.text = "React uses Virtual DOM and JSX for UI development. LangChain simplifies RAG pipelines."
    mock_extract.return_value = [mock_page]
    mock_persist.return_value = True

    result = await PaperProcessingWorker.process_paper(
        paper_id="paper_test_001",
        file_path="sample.pdf",
        title="Sample React & RAG Research Paper"
    )

    assert result["paper_id"] == "paper_test_001"
    assert result["status"] == "COMPLETED"
    assert result["pages_count"] == 1
    assert result["chunks_count"] >= 1
    assert result["graph_entities"] >= 1
    assert result["graph_persisted"] is True
