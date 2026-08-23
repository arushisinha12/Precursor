import os

from sqlalchemy import create_engine
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


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
