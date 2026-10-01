"""
SQLAlchemy engine + session setup. SQLite (quick local checks/CI) aur
Postgres (real dev/prod) dono DATABASE_URL se drive hote hain - baaki code
identical rehta hai, bas connection string badalta hai.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from src.api.config import settings

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
