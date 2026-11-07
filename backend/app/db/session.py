from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


class DatabaseNotConfigured(RuntimeError):
    """Raised when the application is used before DATABASE_URL is configured."""


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    database_url = get_settings().database_url
    if not database_url:
        raise DatabaseNotConfigured(
            "DATABASE_URL não configurada. Copie .env.example para .env e ajuste-a."
        )
    engine = create_engine(database_url, pool_pre_ping=True)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()
