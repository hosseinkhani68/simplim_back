from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
import urllib.parse

# Load environment variables
load_dotenv()

# Get MySQL URL from Railway
MYSQL_URL = os.getenv("MYSQL_URL")

if not MYSQL_URL:
    raise ValueError("MYSQL_URL environment variable is not set")

# Parse the MySQL URL
parsed_url = urllib.parse.urlparse(MYSQL_URL)
username = parsed_url.username
password = parsed_url.password
hostname = parsed_url.hostname
port = parsed_url.port or 3306
database = parsed_url.path.lstrip('/')

# Create SQLAlchemy URL
SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{username}:{password}@{hostname}:{port}/{database}"

print(f"Connecting to database at: {hostname}:{port}")  # For debugging

# Create engine with Railway-specific settings
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,  # Enable connection health checks
    pool_recycle=3600,   # Recycle connections after 1 hour
    pool_size=5,         # Maximum number of connections to keep open
    max_overflow=10,     # Maximum number of connections to create above pool_size
    echo=True,          # Set to True for debugging SQL queries
    connect_args={
        "connect_timeout": 10,  # 10 second timeout
        "ssl": {"verify_cert": False}  # Disable SSL verification for internal connections
    }
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