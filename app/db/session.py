import os

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.db.models import Base

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://cashflow:cashflow@db:5432/cashflow_db"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)


def check_connection() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"[DB] Error de conexion: {e}")
        return False


def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
