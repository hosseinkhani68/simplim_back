from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()


# Get MySQL configuration from Railway environment variables
MYSQL_USER = os.getenv("MYSQLUSER", "root")
MYSQL_PASSWORD = os.getenv("MYSQLPASSWORD")
MYSQL_HOST = os.getenv("MYSQLHOST", "containers-us-west-181.railway.app")  # Use public host
MYSQL_PORT = os.getenv("MYSQLPORT", "3306")
MYSQL_DATABASE = os.getenv("MYSQLDATABASE", "railway")

# Create MySQL URL
SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"

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