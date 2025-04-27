from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from database.database import get_db, init_db
from sqlalchemy.orm import Session
from database.models import User
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get environment variables
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

app = FastAPI(
    title="Simplim Backend",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup"""
    try:
        init_db()
        logger.info("Database connection initialized during startup")
    except Exception as e:
        logger.error(f"Error initializing database during startup: {str(e)}")
        # Don't raise the exception, let the app start without database

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "message": "Simplim API is running",
        "environment": ENVIRONMENT,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/db-status")
async def db_status(db: Session = Depends(get_db)):
    """Check database connection status"""
    try:
        # Test database connection by querying User table
        user_count = db.query(User).count()
        return {
            "status": "connected",
            "message": "Database connection successful",
            "user_count": user_count
        }
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        return {
            "status": "disconnected",
            "error": str(e)
        } 