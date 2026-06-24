import logging
import os
from datetime import datetime, timezone

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from typing import Generator, Optional

from app.config import settings

log = logging.getLogger(__name__)

# Use SQLite as local fallback when PostgreSQL isn't available.
# On Railway, DATABASE_URL will point to the real Postgres instance.
_url = settings.database_url
try:
    engine = create_engine(_url, pool_pre_ping=True)
    engine.connect().close()
    _db_available = True
except Exception as e:
    log.warning(f"Postgres not available ({e}), falling back to SQLite")
    _sqlite_path = os.path.join(os.path.dirname(__file__), "../../storage/history.db")
    os.makedirs(os.path.dirname(_sqlite_path), exist_ok=True)
    engine = create_engine(f"sqlite:///{os.path.abspath(_sqlite_path)}")
    _db_available = True  # SQLite always works

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


class ExportHistory(Base):
    __tablename__ = "export_history"

    id = Column(Integer, primary_key=True, index=True)
    project_name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    pdf_recap_path = Column(String(512))
    pdf_layout_path = Column(String(512))
    total_panels = Column(Integer)
    waste_ratio = Column(Integer)
    summary_json = Column(Text)


def get_db() -> Generator[Optional[Session], None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
