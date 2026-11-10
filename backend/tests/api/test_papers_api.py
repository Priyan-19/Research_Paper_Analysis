import pytest
import io
from datetime import datetime
from unittest.mock import AsyncMock, patch

from app.schemas.paper import PaperResponse


class TestPapersAPI:
    """API tests for research paper upload, validation, listing, and retrieval."""

    def test_upload_non_pdf_rejected(self, test_client):
        """Rejects non-PDF file upload with 400 Bad Request."""
        file_content = b"This is not a PDF file."
        files = {"file": ("document.txt", io.BytesIO(file_content), "text/plain")}

        res = test_client.post("/api/v1/papers/upload", files=files)
        assert res.status_code == 400
        assert "Only PDF files" in res.json()["detail"]

    def test_upload_valid_pdf_success(self, test_client):
        """Uploads valid PDF and triggers processing."""
        file_content = b"%PDF-1.4 sample pdf content for upload"
        files = {"file": ("sample.pdf", io.BytesIO(file_content), "application/pdf")}

        mock_paper_res = PaperResponse(
            id="p_123",
            title="Sample Paper",
            filename="sample.pdf",
            file_size_bytes=1024,
            total_pages=1,
            status="COMPLETED",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        with patch("app.api.v1.papers.PaperService.process_and_save_paper", new_callable=AsyncMock) as mock_save:
            mock_save.return_value = mock_paper_res

            res = test_client.post("/api/v1/papers/upload", files=files)
            assert res.status_code == 201
            data = res.json()
            assert data["id"] == "p_123"
            assert data["title"] == "Sample Paper"
            assert data["status"] == "COMPLETED"

    def test_list_papers(self, test_client):
        """Returns paginated list of papers."""
        mock_paper = PaperResponse(
            id="p_123",
            title="Attention Is All You Need",
            filename="attention.pdf",
            file_size_bytes=2048,
            total_pages=15,
            status="COMPLETED",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        with patch("app.api.v1.papers.PaperService.list_papers", new_callable=AsyncMock) as mock_list_svc:
            mock_list_svc.return_value = ([mock_paper], 1)

            res = test_client.get("/api/v1/papers?skip=0&limit=10")
            assert res.status_code == 200
            data = res.json()
            assert data["total"] == 1
            assert len(data["papers"]) == 1
            assert data["papers"][0]["title"] == "Attention Is All You Need"

    def test_delete_paper_success(self, test_client):
        """Deletes research paper and associated vector chunks and graph triples (204 No Content)."""
        with patch("app.api.v1.papers.PaperService.delete_paper", new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = True

            res = test_client.delete("/api/v1/papers/p_123")
            assert res.status_code == 204
            mock_delete.assert_awaited_once()

    def test_delete_paper_not_found(self, test_client):
        """Returns 404 when attempting to delete non-existent paper."""
        from app.core.exceptions import ResourceNotFoundError

        with patch("app.api.v1.papers.PaperService.delete_paper", new_callable=AsyncMock) as mock_delete:
            mock_delete.side_effect = ResourceNotFoundError(resource_type="Paper", resource_id="nonexistent")

            res = test_client.delete("/api/v1/papers/nonexistent")
            assert res.status_code == 404
