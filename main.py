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
MYSQL_URL = os.getenv("MYSQL_URL")

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
    if not os.getenv("MYSQL_URL"):
        return False
    try:
        # Parse the MySQL URL
        mysql_url = os.getenv("MYSQL_URL")
        # Remove the mysql:// prefix
        mysql_url = mysql_url.replace("mysql://", "")
        # Split into parts
        credentials, host_port_db = mysql_url.split("@")
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

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    try:
        # Basic API health check
        health_status = {
            "status": "healthy",
            "environment": ENVIRONMENT,
            "version": "1.0.0",
            "timestamp": time.time(),
            "services": {
                "api": "up",
                "database": "up" if MYSQL_URL else "down",
                "openai": "up" if os.getenv("OPENAI_API_KEY") else "down"
            }
        }
        
        # Try database connection if URL is available
        if MYSQL_URL:
            try:
                connection = mysql.connector.connect(
                    host=os.getenv("MYSQLHOST"),
                    user=os.getenv("MYSQLUSER"),
                    password=os.getenv("MYSQLPASSWORD"),
                    database=os.getenv("MYSQL_DATABASE"),
                    port=int(os.getenv("MYSQLPORT", "3306"))
                )
                if connection.is_connected():
                    connection.close()
                    health_status["services"]["database"] = "up"
                else:
                    health_status["services"]["database"] = "down"
            except Exception as db_error:
                health_status["services"]["database"] = "down"
                health_status["database_error"] = str(db_error)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=health_status
        )
    except Exception as e:
        # Return 200 OK even if there's an error, but include error details
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "degraded",
                "error": str(e),
                "environment": ENVIRONMENT,
                "version": "1.0.0",
                "timestamp": time.time(),
                "services": {
                    "api": "up",
                    "database": "down",
                    "openai": "up" if os.getenv("OPENAI_API_KEY") else "down"
                }
            }
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        reload=ENVIRONMENT == "development"
    ) 