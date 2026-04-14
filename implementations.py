"""
implementations.py
===================
Concrete repository and service implementations.
"""

from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import dpp_core
from user import User, IUserRepository, IUserService, RegisterResult, AuthResult
from exceptions import (
    UserAlreadyExistsError,
    InvalidPasswordStructureError,
    AuthenticationFailedError,
    UserInactiveError,
)
from database import UserModel


# ---------------------------------------------------------------------------
# Repository
# ---------------------------------------------------------------------------

class UserRepository(IUserRepository):
    """SQLAlchemy PostgreSQL implementation of IUserRepository."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_username(self, username: str) -> User | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.username == username)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def create(self, user: User) -> User:
        model = UserModel(
            username=user.username,
            static_hash=user.static_hash,
            parameter_map=user.parameter_map,
            placeholder=user.placeholder,
            is_active=user.is_active,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def exists(self, username: str) -> bool:
        result = await self._session.execute(
            select(UserModel.id).where(UserModel.username == username)
        )
        return result.scalar_one_or_none() is not None

    @staticmethod
    def _to_entity(model: UserModel) -> User:
        return User(
            id=model.id,
            username=model.username,
            static_hash=model.static_hash,
            parameter_map=model.parameter_map,
            placeholder=model.placeholder,
            created_at=model.created_at,
            is_active=model.is_active,
        )


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class UserService(IUserService):
    """Concrete DAF user service — wires DPP core with the repository."""

    def __init__(self, user_repository: IUserRepository):
        self._repository = user_repository

    async def register(self, username: str, password: str, placeholder: str) -> RegisterResult:
        # Duplicate check
        if await self._repository.exists(username):
            raise UserAlreadyExistsError(f"Username '{username}' is already registered.")

        # DPP core registration
        try:
            payload = dpp_core.register(password=password, placeholder=placeholder)
        except ValueError as e:
            raise InvalidPasswordStructureError(str(e))

        # Build and persist entity
        user = User(
            id=None,
            username=username,
            static_hash=payload.static_hash,
            parameter_map=payload.parameter_map,
            placeholder=placeholder,
            created_at=datetime.now(tz=timezone.utc),
            is_active=True,
        )
        saved = await self._repository.create(user)
        return RegisterResult(user=saved, parameter_map=payload.parameter_map)

    async def authenticate(self, username: str, password: str) -> AuthResult:
        # Fetch user
        user = await self._repository.get_by_username(username)
        if not user:
            raise AuthenticationFailedError()

        # Active check
        if not user.is_active:
            raise UserInactiveError()

        # DPP two-stage authentication
        result = dpp_core.authenticate(
            input_password=password,
            stored_hash=user.static_hash,
            parameter_map=user.parameter_map,
        )
        if not result.success:
            raise AuthenticationFailedError()

        return AuthResult(success=True, username=user.username, message="Authentication successful.")
