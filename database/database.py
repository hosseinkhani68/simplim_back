from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
import urllib.parse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Initialize engine as None
engine = None
SessionLocal = None

def get_db_url():
    """Get database URL based on environment"""
    try:
        if ENVIRONMENT == "production":
            # Use internal URL for Railway deployment
            MYSQL_USER = os.getenv("MYSQLUSER")
            MYSQL_PASSWORD = os.getenv("MYSQLPASSWORD")
            MYSQL_HOST = os.getenv("MYSQLHOST")
            MYSQL_PORT = os.getenv("MYSQLPORT")
            MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")
            
            if not all([MYSQL_USER, MYSQL_PASSWORD, MYSQL_HOST, MYSQL_PORT, MYSQL_DATABASE]):
                raise ValueError("Missing required MySQL environment variables")
                
            return f"mysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
        else:
            # Use public URL for local development
            MYSQL_PUBLIC_URL = os.getenv("MYSQL_PUBLIC_URL")
            if not MYSQL_PUBLIC_URL:
                raise ValueError("MYSQL_PUBLIC_URL environment variable is not set")
            
            return MYSQL_PUBLIC_URL
    except Exception as e:
        logger.error(f"Error getting database URL: {str(e)}")
        raise

def init_db():
    """Initialize database connection"""
    global engine, SessionLocal
    try:
        db_url = get_db_url()
        logger.info(f"Initializing database connection to: {db_url}")
        
        # Create engine with connection parameters
        engine = create_engine(
            db_url,
            pool_pre_ping=True,  # Enable connection health checks
            pool_recycle=3600,   # Recycle connections after 1 hour
            connect_args={
                "connect_timeout": 10,  # Connection timeout in seconds
                "read_timeout": 10,     # Read timeout in seconds
                "write_timeout": 10     # Write timeout in seconds
            }
        )
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        logger.info("Database connection initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create Base for models
Base = declarative_base() 