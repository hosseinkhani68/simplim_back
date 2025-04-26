from fastapi import FastAPI, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, simplify, pdf
import os
from dotenv import load_dotenv
import time
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
import mysql.connector
from mysql.connector import Error
from database.database import get_db
from sqlalchemy.orm import Session

# Load environment variables
load_dotenv()

# Get environment variables
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
PORT = int(os.getenv("PORT", "8000"))
HOST = os.getenv("HOST", "0.0.0.0")
MYSQL_PUBLIC_URL = os.getenv("MYSQL_PUBLIC_URL")

app = FastAPI(
    title="Simplim Backend",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(simplify.router, prefix="/simplify", tags=["Simplify"])
app.include_router(pdf.router, prefix="/pdf", tags=["PDF Management"])

def check_database_connection(db: Session = Depends(get_db)):
    try:
        # Try to execute a simple query
        db.execute("SELECT 1")
        return True
    except Exception as e:
        print(f"Database connection error: {str(e)}")
        return False

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    if not check_database_connection(db):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection failed"
        )
    return {"status": "healthy", "database": "connected"}

@app.get("/", status_code=status.HTTP_200_OK)
async def root(db: Session = Depends(get_db)):
    try:
        print("Attempting to connect to database...")  # Debug log
        # Check database connection
        db.execute("SELECT 1")
        print("Database connection successful")  # Debug log
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Welcome to Simplim Backend API",
                "status": "healthy",
                "database": "connected",
                "version": "1.0.0",
                "timestamp": time.time(),
                "environment": ENVIRONMENT
            }
        )
    except Exception as e:
        print(f"Database connection failed: {str(e)}")  # Debug log
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unavailable: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        reload=ENVIRONMENT == "development"
    ) 