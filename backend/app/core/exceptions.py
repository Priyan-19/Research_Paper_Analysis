from typing import Any, Dict, Optional
# pyrefly: ignore [missing-import]
from fastapi import HTTPException, status


class BaseAppException(HTTPException):
    """Base exception for all application custom errors."""
    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: Any = None,
        headers: Optional[Dict[str, str]] = None,
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class DatabaseConnectionError(BaseAppException):
    """Raised when connecting to PostgreSQL, Neo4j, or Redis fails."""
    def __init__(self, service_name: str, details: str = ""):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "Database Connection Failed",
                "service": service_name,
                "message": f"Could not connect to {service_name}. {details}".strip()
            }
        )


class ResourceNotFoundError(BaseAppException):
    """Raised when a requested resource (Paper, Chunk, Node) is not found."""
    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "Resource Not Found",
                "resource_type": resource_type,
                "resource_id": resource_id,
                "message": f"{resource_type} with ID '{resource_id}' was not found."
            }
        )


class PDFProcessingError(BaseAppException):
    """Raised when parsing or chunking a PDF document fails."""
    def __init__(self, filename: str, reason: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "PDF Processing Failed",
                "filename": filename,
                "reason": reason,
                "message": f"Failed to process PDF '{filename}': {reason}"
            }
        )


class LLMProviderError(BaseAppException):
    """Raised when an LLM API request or inference fails."""
    def __init__(self, provider: str, message: str):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "error": "LLM Service Failure",
                "provider": provider,
                "message": f"Error from LLM provider '{provider}': {message}"
            }
        )
