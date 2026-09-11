from typing import Optional, Dict, Any

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field


class ServiceHealth(BaseModel):
    status: str = Field(..., description="Service status: 'healthy' or 'unhealthy'")
    connected: bool = Field(..., description="Connection state boolean")
    error: Optional[str] = Field(None, description="Error message if unhealthy")
    details: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional health properties")


class SystemHealthResponse(BaseModel):
    status: str = Field(..., description="Overall system health status")
    app_name: str = Field(..., description="Application name")
    version: str = Field(..., description="System version string")
    services: Dict[str, Any] = Field(..., description="Individual database and service health checks")
