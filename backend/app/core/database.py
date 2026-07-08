import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base = declarative_base()

# Attempt to configure engine. Fallback to SQLite if PostgreSQL connection fails.
try:
    # If using postgresql, check if we need to auto-create the database first
    if "postgresql" in settings.DATABASE_URL:
        # Connect to postgres server to check/create the db
        temp_url = settings.DATABASE_URL.rsplit("/", 1)[0] + "/postgres"
        temp_engine = create_engine(temp_url, isolation_level="AUTOCOMMIT")
        with temp_engine.connect() as conn:
            db_name = settings.DATABASE_URL.split("/")[-1]
            exists = conn.execute(
                text(f"SELECT 1 FROM pg_database WHERE datname='{db_name}'")
            ).scalar()
            if not exists:
                logger.info(f"Database {db_name} does not exist. Creating...")
                conn.execute(text(f"CREATE DATABASE {db_name}"))
        temp_engine.dispose()

    engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
    # Test connection
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    logger.info("Successfully connected to PostgreSQL database.")
except Exception as e:
    logger.warning(f"Could not connect to PostgreSQL: {e}. Falling back to SQLite.")
    sqlite_url = "sqlite:///./insightflow.db"
    engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
