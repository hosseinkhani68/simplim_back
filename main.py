from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, simplify, pdf
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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
    return {
        "message": "Welcome to Simplim Backend API",
        "status": "healthy",
        "version": "1.0.0"
    }

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    return {
        "status": "healthy",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "version": "1.0.0"
    } 