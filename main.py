from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

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

@app.get("/")
async def root():
    return {
        "message": "Hello from Simplim",
        "environment": ENVIRONMENT,
        "version": "1.0.0"
    } 