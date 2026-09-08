from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

# Normalize database URL (Render provides URLs starting with postgres://)
raw_db_url = settings.DATABASE_URL
if raw_db_url.startswith("postgres://"):
    db_url = raw_db_url.replace("postgres://", "postgresql://", 1)
else:
    db_url = raw_db_url

# Engine arguments based on database dialect
connect_args = {}
engine_kwargs = {"echo": False}
if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
else:
    # PostgreSQL connection pool settings for cloud deployment
    engine_kwargs.update({
        "pool_size": 5,
        "max_overflow": 10,
        "pool_pre_ping": True,
        "pool_recycle": 300,
    })

try:
    engine = create_engine(
        db_url,
        connect_args=connect_args,
        **engine_kwargs
    )
except Exception as exc:
    print(f"[DATABASE WARNING] Failed to connect to {db_url}: {exc}. Falling back to SQLite.")
    engine = create_engine(
        "sqlite:///./legal_metrology.db",
        connect_args={"check_same_thread": False},
        echo=False
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency that provides a database session and ensures it closes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
