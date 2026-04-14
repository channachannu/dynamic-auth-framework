"""
routes.py
==========
FastAPI schemas and route definitions for DAF authentication.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_session
from implementations import UserRepository, UserService
from exceptions import (
    UserAlreadyExistsError,
    InvalidPasswordStructureError,
    AuthenticationFailedError,
    UserInactiveError,
)

router = APIRouter(prefix="/v1/auth", tags=["Authentication"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class RegisterRequest(BaseModel):
    username:    str = Field(..., min_length=3, max_length=50,  examples=["Botnet"])
    password:    str = Field(..., min_length=6, max_length=128, examples=["Botxxnetxx"])
    placeholder: str = Field(default="x", min_length=1, max_length=1, examples=["x"])

    @field_validator("username")
    @classmethod
    def no_spaces(cls, v: str) -> str:
        if " " in v:
            raise ValueError("Username must not contain spaces.")
        return v.strip()


class RegisterResponse(BaseModel):
    message:       str
    username:      str
    parameter_map: str


class AuthRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50,  examples=["Botnet"])
    password: str = Field(..., min_length=6, max_length=128, examples=["Bot21net30"])


class AuthResponse(BaseModel):
    success:  bool
    username: str
    message:  str


# ---------------------------------------------------------------------------
# Dependency — builds service per request
# ---------------------------------------------------------------------------

async def get_user_service(session: AsyncSession = Depends(get_session)):
    """Wire repository → service per request."""
    return UserService(user_repository=UserRepository(session))


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/health", tags=["Health"])
async def health():
    """Health check."""
    return {"status": "DAF Phase 1 is running.", "version": "1.0.0"}


@router.post("/register", response_model=RegisterResponse, status_code=201)
async def register(
    request: RegisterRequest,
    service: UserService = Depends(get_user_service),
):
    """
    Register a new DAF user with a dynamic password.

    Use placeholder characters (default **x**) to mark dynamic positions.

    **Example:** `Botxxnetxx` → at 21:30 UTC, login with `Bot21net30`
    """
    try:
        result = await service.register(
            username=request.username,
            password=request.password,
            placeholder=request.placeholder,
        )
        return RegisterResponse(
            message="Registration successful.",
            username=result.user.username,
            parameter_map=result.parameter_map,
        )
    except UserAlreadyExistsError:
        raise HTTPException(status_code=409, detail="Username already taken.")
    except InvalidPasswordStructureError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/authenticate", response_model=AuthResponse, status_code=200)
async def authenticate(
    request: AuthRequest,
    service: UserService = Depends(get_user_service),
):
    """
    Authenticate using a dynamic password.

    Fill dynamic positions with current **UTC time (HHMM)**.

    **Example** at 21:30 UTC with pattern `Botxxnetxx`: login with `Bot21net30`
    """
    try:
        result = await service.authenticate(
            username=request.username,
            password=request.password,
        )
        return AuthResponse(
            success=True,
            username=result.username,
            message=result.message,
        )
    except (AuthenticationFailedError, UserInactiveError):
        raise HTTPException(status_code=401, detail="Invalid credentials.")
