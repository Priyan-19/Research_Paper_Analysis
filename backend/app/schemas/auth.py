from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRegisterRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=6, description="User password (min 6 chars)")
    full_name: Optional[str] = Field(None, description="User full name")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "researcher@example.com",
                "password": "SecurePassword123!",
                "full_name": "Dr. Alex Vance"
            }
        }
    )


class UserLoginRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "researcher@example.com",
                "password": "SecurePassword123!"
            }
        }
    )


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type")


class UserResponse(BaseModel):
    id: str = Field(..., description="User unique identifier")
    email: str = Field(..., description="User email address")
    full_name: Optional[str] = Field(None, description="User full name")
    is_active: bool = Field(True, description="Account active status")

    model_config = ConfigDict(from_attributes=True)
