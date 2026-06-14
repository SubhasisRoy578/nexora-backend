from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

# Get DATABASE_URL and convert for psycopg2
DATABASE_URL = settings.DATABASE_URL

# Convert asyncpg URL to psycopg2 URL
if "postgresql+asyncpg://" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)
elif "postgresql://" in DATABASE_URL and "+psycopg2" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

# Create sync engine
engine = create_engine(
    DATABASE_URL,
    echo=True,
    pool_pre_ping=True,
)

# Create sync session
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)

# Base class for models
Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
