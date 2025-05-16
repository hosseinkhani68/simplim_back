from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
import logging
from datetime import datetime
from database.database import init_db
from routers import auth, pdf

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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers immediately
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(pdf.router, prefix="/pdf", tags=["pdf"])
logger.info("Routers included successfully")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "message": "Simplim API is running",
        "environment": ENVIRONMENT,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.on_event("startup")
async def startup_event():
    """Initialize database after startup"""
    try:
        # Initialize database
        init_db()
        logger.info("Database connection initialized")
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        # Don't raise the exception, let the app continue running 