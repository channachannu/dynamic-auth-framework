"""exceptions.py — DAF domain exceptions."""


class DomainException(Exception):
    """Base domain exception."""

class UserAlreadyExistsError(DomainException):
    """Username already registered."""

class UserNotFoundError(DomainException):
    """User does not exist."""

class UserInactiveError(DomainException):
    """Account is inactive."""

class InvalidPasswordStructureError(DomainException):
    """Password violates DPP rules."""

class AuthenticationFailedError(DomainException):
    """Generic auth failure — never reveals which stage failed."""
    def __init__(self):
        super().__init__("Invalid credentials.")
