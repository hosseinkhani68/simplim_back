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
                
            return f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
        else:
            # Use public URL for local development
            MYSQL_PUBLIC_URL = os.getenv("MYSQL_PUBLIC_URL")
            if not MYSQL_PUBLIC_URL:
                raise ValueError("MYSQL_PUBLIC_URL environment variable is not set")
            
            # Ensure the URL uses pymysql
            parsed_url = urllib.parse.urlparse(MYSQL_PUBLIC_URL)
            if parsed_url.scheme == "mysql":
                return MYSQL_PUBLIC_URL.replace("mysql://", "mysql+pymysql://", 1)
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
            pool_recycle=1800,   # Recycle connections after 30 minutes
            pool_size=20,        # Maximum number of connections to keep
            max_overflow=10,     # Maximum number of connections that can be created beyond pool_size
            pool_timeout=30,     # Seconds to wait before giving up on getting a connection from the pool
            connect_args={
                "connect_timeout": 5,    # Connection timeout in seconds
                "read_timeout": 5,       # Read timeout in seconds
                "write_timeout": 5,      # Write timeout in seconds
                "charset": "utf8mb4"     # Use utf8mb4 charset
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