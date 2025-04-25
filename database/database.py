from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Get MySQL URL from Railway
MYSQL_URL = os.getenv("MYSQL_URL")

if not MYSQL_URL:
    raise ValueError("MYSQL_URL environment variable is not set")

# Convert mysql:// to mysql+pymysql:// for SQLAlchemy
SQLALCHEMY_DATABASE_URL = MYSQL_URL.replace("mysql://", "mysql+pymysql://")

# Create engine with Railway-specific settings
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,  # Enable connection health checks
    pool_recycle=3600,   # Recycle connections after 1 hour
    pool_size=5,         # Maximum number of connections to keep open
    max_overflow=10,     # Maximum number of connections to create above pool_size
    echo=False          # Set to True for debugging SQL queries
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 