from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# ============================================
# ENVIRONMENT DETECTION
# ============================================
ENV = os.getenv("ENV", "development")  # Default to development

# Load appropriate .env file based on environment
if ENV == "production":
    env_file = ".env.production"
    print("🚀 PRODUCTION MODE")
else:
    env_file = ".env.development"
    print("💻 DEVELOPMENT MODE")

# Load environment variables from file
if os.path.exists(env_file):
    load_dotenv(env_file)
    print(f"✅ Loaded: {env_file}")
else:
    print(f"⚠️  Warning: {env_file} not found, using default .env")
    load_dotenv()  # Fallback to .env

# ============================================
# DATABASE CONFIGURATION
# ============================================
DATABASE_URL = os.getenv("DATABASE_URL")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Validation
if not DATABASE_URL:
    raise ValueError(f"❌ DATABASE_URL not found in {env_file}!")

# Display connection info (hide password)
if "@" in DATABASE_URL:
    db_info = DATABASE_URL.split("@")[1]  # host:port/dbname
    print(f"🗄️  Database: {db_info}")
else:
    print(f"🗄️  Database: localhost")

# ============================================
# SQLALCHEMY ENGINE SETUP
# ============================================
# Different settings for development vs production
if ENVIRONMENT == "production":
    # Production: Optimized for performance
    engine = create_engine(
        DATABASE_URL,
        echo=False,  # Don't print SQL queries
        pool_pre_ping=True,  # Verify connections before using
        pool_size=10,  # Connection pool size
        max_overflow=20,  # Extra connections when pool is full
        pool_recycle=3600,  # Recycle connections every hour
        connect_args={
            "connect_timeout": 10,
            "options": "-c timezone=utc"
        }
    )
    print("⚙️  Production engine configured")
else:
    # Development: Verbose logging for debugging
    engine = create_engine(
        DATABASE_URL,
        echo=True,  # Print all SQL queries for debugging
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10
    )
    print("⚙️  Development engine configured (SQL logging enabled)")

# ============================================
# SESSION FACTORY
# ============================================
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# ============================================
# BASE CLASS FOR MODELS
# ============================================
Base = declarative_base()

# ============================================
# DEPENDENCY FOR FASTAPI ROUTES
# ============================================
def get_db():
    """
    Database session dependency for FastAPI routes.
    Usage: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ============================================
# UTILITY FUNCTIONS
# ============================================
def get_database_info():
    """Return current database connection info"""
    return {
        "environment": ENVIRONMENT,
        "database_url": DATABASE_URL.split("@")[1] if "@" in DATABASE_URL else "localhost",
        "engine": str(engine.url)
    }

def test_connection():
    """Test database connection"""
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        print("✅ Database connection successful!")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

# ============================================
# AUTO-TEST CONNECTION ON IMPORT
# ============================================
if __name__ != "__main__":
    # Test connection when module is imported
    test_connection()
