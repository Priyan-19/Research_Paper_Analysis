from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock
import pytest
from fastapi import HTTPException, status

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    get_current_user_optional,
    get_current_user_required,
)
from app.models.paper import Paper
from app.services.paper_service import PaperService


def run_coroutine(coro):
    """
    Executes a coroutine to completion by driving it with .send(None).
    Avoids Windows socketpair and Proactor loopback creation in sandbox environments.
    """
    try:
        coro.send(None)
    except StopIteration as exc:
        return exc.value


class TestSecurityAndMultiTenancy:
    """Unit tests for Phase 7 & 8 Multi-Tenancy Security and Access Control."""

    def test_password_hashing_and_verification(self):
        password = "SecureResearchPassword123!"
        hashed = hash_password(password)
        assert hashed != password
        assert verify_password(password, hashed) is True
        assert verify_password("WrongPassword!", hashed) is False

    def test_create_and_decode_access_token(self):
        payload = {"sub": "user-uuid-1234", "email": "researcher@lab.edu"}
        token = create_access_token(payload, expires_delta=timedelta(hours=1))
        assert isinstance(token, str)

        decoded = decode_access_token(token)
        assert decoded is not None
        assert decoded["sub"] == "user-uuid-1234"
        assert decoded["email"] == "researcher@lab.edu"
        assert "exp" in decoded

    def test_decode_invalid_token(self):
        assert decode_access_token("not-a-real-token.xyz.abc") is None

    def test_get_current_user_optional_unauthenticated(self):
        user = run_coroutine(get_current_user_optional(token=None))
        assert user is None

    def test_get_current_user_optional_authenticated(self):
        token = create_access_token({"sub": "user-999"})
        user = run_coroutine(get_current_user_optional(token=token))
        assert user is not None
        assert user["sub"] == "user-999"

    def test_get_current_user_required_missing_token_raises_401(self):
        with pytest.raises(HTTPException) as exc_info:
            run_coroutine(get_current_user_required(token=None))
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_current_user_required_invalid_token_raises_401(self):
        with pytest.raises(HTTPException) as exc_info:
            run_coroutine(get_current_user_required(token="invalid.bad.token"))
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_paper_by_id_owner_access_allowed(self):
        mock_db = AsyncMock()
        fake_paper = Paper(
            id="paper-101",
            title="Transformer Analysis",
            user_id="user-owner-1",
            file_path="dummy.pdf",
            file_hash="hash1"
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = fake_paper
        mock_db.execute.return_value = mock_result

        # Owner accesses their own paper
        paper = run_coroutine(PaperService.get_paper_by_id(mock_db, "paper-101", user_id="user-owner-1"))
        assert paper.id == "paper-101"
        assert paper.user_id == "user-owner-1"

    def test_get_paper_by_id_public_paper_accessible_by_anyone(self):
        mock_db = AsyncMock()
        fake_paper = Paper(
            id="paper-public",
            title="Public Landmark Paper",
            user_id=None,  # Legacy / public paper
            file_path="dummy.pdf",
            file_hash="hash2"
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = fake_paper
        mock_db.execute.return_value = mock_result

        # Any user can view legacy/public paper
        paper = run_coroutine(PaperService.get_paper_by_id(mock_db, "paper-public", user_id="any-user-99"))
        assert paper.id == "paper-public"
        assert paper.user_id is None

    def test_get_paper_by_id_different_user_denied_403(self):
        mock_db = AsyncMock()
        fake_paper = Paper(
            id="paper-secret",
            title="Confidential Research",
            user_id="user-owner-1",
            file_path="dummy.pdf",
            file_hash="hash3"
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = fake_paper
        mock_db.execute.return_value = mock_result

        # Different user tries to view paper
        with pytest.raises(HTTPException) as exc_info:
            run_coroutine(PaperService.get_paper_by_id(mock_db, "paper-secret", user_id="intruder-user-2"))
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "permission to access" in exc_info.value.detail
