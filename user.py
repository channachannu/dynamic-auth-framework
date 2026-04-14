"""
user.py
========
User domain entity + repository and service interfaces.
Pure Python — zero framework dependencies.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass
class User:
    """DAF user domain entity."""
    id:            int | None
    username:      str
    static_hash:   str
    parameter_map: str
    placeholder:   str
    created_at:    datetime
    is_active:     bool = True

    def deactivate(self) -> None:
        if not self.is_active:
            raise ValueError(f"User '{self.username}' is already inactive.")
        self.is_active = False

    def password_length(self) -> int:
        return len(self.parameter_map)


@dataclass(frozen=True)
class RegisterResult:
    user:          User
    parameter_map: str


@dataclass(frozen=True)
class AuthResult:
    success:  bool
    username: str
    message:  str


class IUserRepository(ABC):

    @abstractmethod
    async def get_by_username(self, username: str) -> User | None: ...

    @abstractmethod
    async def create(self, user: User) -> User: ...

    @abstractmethod
    async def exists(self, username: str) -> bool: ...


class IUserService(ABC):

    @abstractmethod
    async def register(self, username: str, password: str, placeholder: str) -> RegisterResult: ...

    @abstractmethod
    async def authenticate(self, username: str, password: str) -> AuthResult: ...
