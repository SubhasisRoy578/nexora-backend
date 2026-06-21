# app/database/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# ============================================
# SYNC DATABASE (For chat_routes.py)
# ============================================

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./nexora.db")

# Sync engine for traditional (non-async) routes
sync_engine = create_engine(DATABASE_URL)
SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

Base = declarative_base()

def get_sync_db():
    """Dependency for sync routes (like chat)."""
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================
# ASYNC DATABASE (For other parts)
# ============================================

# Try to import async dependencies, but fallback gracefully
try:
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker as async_sessionmaker
    
    # Convert postgresql:// to postgresql+asyncpg:// for async
    async_db_url = DATABASE_URL
    if async_db_url.startswith("postgresql://"):
        async_db_url = async_db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    async_engine = create_async_engine(
        async_db_url,
        echo=True,
        future=True,
    )
    
    AsyncSessionLocal = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async def get_async_db():
        async with AsyncSessionLocal() as session:
            yield session
    
    ASYNC_AVAILABLE = True
    print("[DB] Async database available")
    
except ImportError:
    ASYNC_AVAILABLE = False
    print("[DB] Async database not available (sqlite or missing asyncpg)")


# ============================================
# PGVECTOR DETECTION
# ============================================

HAS_PGVECTOR = False
try:
    from pgvector.sqlalchemy import Vector
    HAS_PGVECTOR = True
    print("[DB] pgvector detected")
except ImportError:
    print("[DB] pgvector not installed")


# ============================================
# INIT DATABASE
# ============================================

def init_db():
    """Create all tables."""
    Base.metadata.create_all(bind=sync_engine)
    print("[DB] Tables created/verified")


# For backward compatibility
get_db = get_sync_db
