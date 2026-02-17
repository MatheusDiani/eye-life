import time
from collections import defaultdict

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

from auth import (
    ADMIN_USERNAME,
    ADMIN_PASSWORD_HASH,
    verify_password,
    hash_password,
    create_access_token,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])

# --- Rate Limiting ---
MAX_LOGIN_ATTEMPTS = 8
RATE_LIMIT_WINDOW_SECONDS = 15 * 60  # 15 minutes
_login_attempts: dict[str, list[float]] = defaultdict(list)


def _check_rate_limit(client_ip: str):
    """Block login if IP exceeded MAX_LOGIN_ATTEMPTS in the last 15 minutes."""
    now = time.time()
    cutoff = now - RATE_LIMIT_WINDOW_SECONDS

    # Remove old attempts
    _login_attempts[client_ip] = [
        t for t in _login_attempts[client_ip] if t > cutoff
    ]

    if len(_login_attempts[client_ip]) >= MAX_LOGIN_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Muitas tentativas de login. Tente novamente em 15 minutos.",
        )


def _record_attempt(client_ip: str):
    """Record a failed login attempt."""
    _login_attempts[client_ip].append(time.time())


# --- Models ---


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class HashRequest(BaseModel):
    password: str


# --- Endpoints ---


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, req: Request):
    """Authenticate user and return JWT token."""
    client_ip = req.client.host if req.client else "unknown"

    # Check rate limit before processing
    _check_rate_limit(client_ip)

    # If no password hash is set, use a default for development
    password_hash = ADMIN_PASSWORD_HASH or hash_password("admin")

    if request.username != ADMIN_USERNAME:
        _record_attempt(client_ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos",
        )

    if not verify_password(request.password, password_hash):
        _record_attempt(client_ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos",
        )

    # Login successful — clear failed attempts for this IP
    _login_attempts.pop(client_ip, None)

    token = create_access_token(data={"sub": request.username})
    return TokenResponse(access_token=token)


@router.post("/hash-password")
def generate_hash(request: HashRequest):
    """Utility endpoint to generate a password hash. Only available in development."""
    import os
    if os.getenv("ENVIRONMENT", "development") != "development":
        raise HTTPException(status_code=404, detail="Not found")
    return {"hash": hash_password(request.password)}
