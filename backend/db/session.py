from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from backend.config import settings

# DATABASE_URL is read from backend/.env via config.py (pydantic-settings).
# No host/port defaults are assumed here — the full Neon connection string
# (including ?sslmode=require) must be set in backend/.env.
# pool_pre_ping=True silently recycles stale connections, which is important
# for a cloud-hosted database where idle connections may be dropped.
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for yielding DB sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

