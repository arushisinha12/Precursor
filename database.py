import os

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

# Defaults to a local SQLite file so the prototype runs immediately with no
# database server to install/configure. Set DATABASE_URL in .env (e.g. a
# Postgres URL) to use a real database instead - nothing else needs to change.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./precursor.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def ensure_observation_resolution_column():
    """Small, non-destructive SQLite migration for existing prototype DBs."""
    if not DATABASE_URL.startswith("sqlite"):
        return
    inspector = inspect(engine)
    if "observations" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("observations")}
    if "resolved" not in columns:
        with engine.begin() as connection:
            connection.execute(text(
                "ALTER TABLE observations ADD COLUMN resolved BOOLEAN NOT NULL DEFAULT 0"
            ))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
