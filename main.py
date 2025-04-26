from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from routers import auth
from database.database import get_db, engine
from sqlalchemy.orm import Session
import logging
from database.models import User, TextHistory, PDFDocument

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get environment variables
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
PORT = int(os.getenv("PORT", "8000"))
HOST = os.getenv("HOST", "0.0.0.0")

# Log environment info
logger.info(f"Starting application in {ENVIRONMENT} environment")
logger.info(f"Database host: {os.getenv('MYSQLHOST')}")

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

# Include routers
# app.include_router(auth.router, prefix="/auth", tags=["Authentication"])

@app.get("/")
async def root():
    """Simple health check endpoint that doesn't depend on database"""
    return {
        "message": "Hello from Simplim",
        "environment": ENVIRONMENT,
        "version": "1.0.0",
        "status": "healthy"
    }

# @app.get("/db-status")
# async def db_status(db: Session = Depends(get_db)):
#     """Endpoint to check database connection status"""
#     try:
#         logger.info("Attempting database connection...")
#         # Test database connection by counting users
#         user_count = db.query(User).count()
#         logger.info(f"Database connection successful. Found {user_count} users.")
#         return {
#             "status": "connected",
#             "tables": ["users", "text_history", "pdf_document"],
#             "user_count": user_count
#         }
#     except Exception as e:
#         logger.error(f"Database connection failed: {str(e)}")
#         return {
#             "status": "disconnected",
#             "error": str(e),
#             "host": os.getenv("MYSQLHOST")
#         }