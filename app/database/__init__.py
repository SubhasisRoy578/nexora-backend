import os
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./nexora.db")

# Render/Neon uses postgres:// which sqlalchemy doesn't support directly
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
elif DATABASE_URL.startswith("postgresql+asyncpg://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://", 1)

# Configure sqlite/postgresql appropriately
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    HAS_PGVECTOR = False
else:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        pool_size=5,
        max_overflow=10
    )
    
    # Check if pgvector is supported by the PostgreSQL server
    HAS_PGVECTOR = False
    try:
        with engine.connect() as conn:
            res = conn.execute(text("SELECT 1 FROM pg_available_extensions WHERE name = 'vector'")).scalar()
            if res:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                conn.commit()
                HAS_PGVECTOR = True
                print("[DB] pgvector extension checked and enabled")
            else:
                print("[DB] pgvector extension NOT available on database server. Storing as TEXT fallback.")
    except Exception as e:
        print(f"[WARN] pgvector availability check/init failed: {e}. Storing as TEXT fallback.")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create tables using metadata."""
    from app.models.document import DocumentChunk
    from app.models.chat import ChatMessage

    Base.metadata.create_all(bind=engine)
    print("[DB] Tables initialized")
