from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, simplify, pdf
import os
from dotenv import load_dotenv
import time
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
import mysql.connector
from mysql.connector import Error

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

def check_database_connection():
    if not os.getenv("MYSQL_PUBLIC_URL"):
        return False
    try:
        # Parse the MySQL URL
        MYSQL_PUBLIC_URL = os.getenv("MYSQL_PUBLIC_URL")
        # Remove the mysql:// prefix
        MYSQL_PUBLIC_URL = MYSQL_PUBLIC_URL.replace("mysql://", "")
        # Split into parts
        credentials, host_port_db = MYSQL_PUBLIC_URL.split("@")
        user, password = credentials.split(":")
        host_port, database = host_port_db.split("/")
        host, port = host_port.split(":")
        
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            port=int(port)
        )
        if connection.is_connected():
            connection.close()
            return True
        return False
    except Error as e:
        print(f"Database connection error: {str(e)}")
        return False
    except Exception as e:
        print(f"Error parsing MySQL URL: {str(e)}")
        return False

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

# @app.get("/health", status_code=status.HTTP_200_OK)
# async def health_check():
#     try:
#         # Basic health check without database dependency
#         return JSONResponse(
#             status_code=status.HTTP_200_OK,
#             content={
#                 "status": "healthy",
#                 "message": "API is running",
#                 "environment": ENVIRONMENT,
#                 "version": "1.0.0",
#                 "timestamp": time.time()
#             }
#         )
#     except Exception as e:
#         # Still return 200 OK but with error details
#         return JSONResponse(
#             status_code=status.HTTP_200_OK,
#             content={
#                 "status": "degraded",
#                 "message": f"API is running but encountered an error: {str(e)}",
#                 "environment": ENVIRONMENT,
#                 "version": "1.0.0",
#                 "timestamp": time.time()
#             }
#         )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        reload=ENVIRONMENT == "development"
    ) 