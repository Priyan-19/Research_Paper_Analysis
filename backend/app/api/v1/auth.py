from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database.postgres import get_db
from app.models.user import User
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token, oauth2_scheme
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    UserResponse
)

router = APIRouter(prefix="/auth", tags=["User Authentication & Security"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register New User",
    description="Registers a new user account with hashed password storage."
)
async def register_user(
    request: UserRegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    # Check if user with same email exists
    stmt = select(User).where(User.email == request.email.lower())
    res = await db.execute(stmt)
    existing = res.scalars().first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists."
        )

    # Create new user
    new_user = User(
        email=request.email.lower(),
        hashed_password=hash_password(request.password),
        full_name=request.full_name
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return UserResponse(
        id=new_user.id,
        email=new_user.email,
        full_name=new_user.full_name,
        is_active=new_user.is_active
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="User Login & JWT Token Generation",
    description="Authenticates user credentials and returns a signed JWT access token."
)
async def login_user(
    request: UserLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(User).where(User.email == request.email.lower())
    res = await db.execute(stmt)
    user = res.scalars().first()

    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password credentials."
        )

    token = create_access_token({"sub": user.email, "user_id": user.id})
    return TokenResponse(access_token=token, token_type="bearer")


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Current Authenticated User Profile",
    description="Decodes JWT token and returns the current user profile."
)
async def get_current_user_profile(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is missing."
        )

    payload = decode_access_token(token)
    if not payload or not isinstance(payload, dict):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token."
        )

    email = payload.get("sub")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload."
        )

    stmt = select(User).where(User.email == email.lower())
    res = await db.execute(stmt)
    user = res.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User account not found."
        )

    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active
    )
