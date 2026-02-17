from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from auth import (
    ADMIN_USERNAME,
    ADMIN_PASSWORD_HASH,
    verify_password,
    hash_password,
    create_access_token,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class HashRequest(BaseModel):
    password: str


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest):
    """Authenticate user and return JWT token."""
    # If no password hash is set, use a default for development
    password_hash = ADMIN_PASSWORD_HASH or hash_password("admin")

    if request.username != ADMIN_USERNAME:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos",
        )

    if not verify_password(request.password, password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos",
        )

    token = create_access_token(data={"sub": request.username})
    return TokenResponse(access_token=token)


@router.post("/hash-password")
def generate_hash(request: HashRequest):
    """Utility endpoint to generate a password hash. Only available in development."""
    import os
    if os.getenv("ENVIRONMENT", "development") != "development":
        raise HTTPException(status_code=404, detail="Not found")
    return {"hash": hash_password(request.password)}
