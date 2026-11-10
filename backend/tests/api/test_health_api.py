import pytest
from unittest.mock import AsyncMock, patch


class TestHealthAPI:
    """API tests for GET /api/v1/health operational and degraded states."""

    def test_health_check_all_services_healthy(self, test_client):
        """Returns 200 OK with 'healthy' status when all services are connected."""
        mock_pg = {"status": "healthy", "connected": True, "pgvector_enabled": True}
        mock_neo4j = {"status": "healthy", "connected": True}
        mock_redis = {"status": "healthy", "connected": True}

        with patch("app.api.v1.health.check_postgres_health", new_callable=AsyncMock) as p_health, \
             patch("app.api.v1.health.neo4j_client.check_health", new_callable=AsyncMock) as n_health, \
             patch("app.api.v1.health.redis_client.check_health", new_callable=AsyncMock) as r_health:

            p_health.return_value = mock_pg
            n_health.return_value = mock_neo4j
            r_health.return_value = mock_redis

            res = test_client.get("/api/v1/health")
            assert res.status_code == 200
            data = res.json()
            assert data["status"] == "healthy"
            assert data["services"]["postgresql"]["connected"] is True
            assert data["services"]["neo4j"]["connected"] is True
            assert data["services"]["redis"]["connected"] is True

    def test_health_check_degraded_when_postgres_down(self, test_client):
        """Returns 'degraded' status when PostgreSQL is disconnected."""
        mock_pg = {"status": "unhealthy", "connected": False, "error": "Connection refused"}
        mock_neo4j = {"status": "healthy", "connected": True}
        mock_redis = {"status": "healthy", "connected": True}

        with patch("app.api.v1.health.check_postgres_health", new_callable=AsyncMock) as p_health, \
             patch("app.api.v1.health.neo4j_client.check_health", new_callable=AsyncMock) as n_health, \
             patch("app.api.v1.health.redis_client.check_health", new_callable=AsyncMock) as r_health:

            p_health.return_value = mock_pg
            n_health.return_value = mock_neo4j
            r_health.return_value = mock_redis

            res = test_client.get("/api/v1/health")
            assert res.status_code == 200
            data = res.json()
            assert data["status"] == "degraded"
            assert data["services"]["postgresql"]["connected"] is False

