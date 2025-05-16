from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "message": "Simplim API is running",
        "environment": ENVIRONMENT,
        "timestamp": datetime.utcnow().isoformat()
    }

# Initialize database and include routers after the health check endpoint
@app.on_event("startup")
async def startup_event():
    """Initialize database and include routers after startup"""
    try:
        # Import necessary modules
        from database.database import init_db
        from routers import auth, pdf
        
        # Initialize database
        init_db()
        logger.info("Database connection initialized")
        
        # Include routers
        app.include_router(auth.router, prefix="/auth", tags=["authentication"])
        app.include_router(pdf.router, prefix="/pdf", tags=["pdf"])
        logger.info("Routers included successfully")
        
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        # Don't raise the exception, let the app continue running 