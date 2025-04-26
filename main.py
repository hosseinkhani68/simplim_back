from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from routers import auth
from database.database import get_db, engine
from sqlalchemy.orm import Session

# Load environment variables
load_dotenv()

# Get environment variables
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
PORT = int(os.getenv("PORT", "8000"))
HOST = os.getenv("HOST", "0.0.0.0")

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
async def root(db: Session = Depends(get_db)):
    try:
        # Test database connection
        db.execute("SELECT 1")
        return {
            "message": "Hello from Simplim",
            "environment": ENVIRONMENT,
            "version": "1.0.0",
            "database": "connected"
        }
    except Exception as e:
        return {
            "message": "Hello from Simplim",
            "environment": ENVIRONMENT,
            "version": "1.0.0",
            "database": "disconnected",
            "error": str(e)
        }