from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, simplify, pdf
import os
from dotenv import load_dotenv
import time
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException

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

@app.get("/", status_code=status.HTTP_200_OK)
async def root():
    try:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Welcome to Simplim Backend API",
                "status": "healthy",
                "version": "1.0.0",
                "timestamp": time.time(),
                "environment": ENVIRONMENT
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    try:
        # Check if the application can respond
        health_status = {
            "status": "healthy",
            "environment": ENVIRONMENT,
            "version": "1.0.0",
            "timestamp": time.time(),
            "services": {
                "api": "up",
                "database": "up" if os.getenv("MYSQL_URL") else "down",
                "openai": "up" if os.getenv("OPENAI_API_KEY") else "down"
            }
        }
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=health_status
        )
    except Exception as e:
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