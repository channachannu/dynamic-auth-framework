"""
database.py
============
SQLAlchemy async session, Base, and ORM models for PostgreSQL.
"""

from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, Text
from sqlalchemy.ext.asyncio import (
    AsyncSession, create_async_engine, async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from settings import app_settings

engine = create_async_engine(
    app_settings.DATABASE_URL,
    echo=(app_settings.APP_ENV == "development"),
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

class Base(DeclarativeBase):
    pass

class UserModel(Base):
    __tablename__ = "daf_users"
    id:            Mapped[int]      = mapped_column(primary_key=True, autoincrement=True)
    username:      Mapped[str]      = mapped_column(String(50), unique=True, nullable=False, index=True)
    static_hash:   Mapped[str]      = mapped_column(Text, nullable=False)
    parameter_map: Mapped[str]      = mapped_column(String(256), nullable=False)
    placeholder:   Mapped[str]      = mapped_column(String(1), nullable=False, default="x")
    is_active:     Mapped[bool]     = mapped_column(Boolean, default=True, nullable=False)
    created_at:    Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=timezone.utc),
        nullable=False,
    )

async def get_session() -> AsyncSession:
    """Async generator for FastAPI Depends — NO @asynccontextmanager decorator."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
