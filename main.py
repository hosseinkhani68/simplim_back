from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from database.database import get_db, init_db
from sqlalchemy.orm import Session
from database.models import User
import logging
from datetime import datetime
from sqlalchemy import text
from routers import auth, pdf
# from services.supabase_storage_service import SupabaseStorageService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get environment variables
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
PORT = os.getenv("PORT", "8000")

app = FastAPI(
    title="Simplim Backend",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Initialize storage service
# storage_service = SupabaseStorageService()

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(pdf.router, prefix="/pdf", tags=["pdf"])
logger.info("Routers included successfully")

# Log all registered routes
logger.info("Registered routes:")
for route in app.routes:
    logger.info(f"Route: {route.path}, methods: {route.methods}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "status": "ok",
        "message": "Simplim API is running",
        "environment": ENVIRONMENT,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for Railway"""
    health_status = {
        "status": "healthy",
        "version": "1.0.0",
        "environment": ENVIRONMENT,
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "database": "unknown",
            "storage": "unknown"
        }
    }
    
    try:
        # Check database
        db = next(get_db())
        db.execute(text("SELECT 1"))
        health_status["services"]["database"] = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        health_status["services"]["database"] = "unhealthy"
        health_status["status"] = "unhealthy"
    
    try:
        # Check Supabase storage
        # Try to list files in the bucket
        # files = await storage_service.list_user_files(0)  # Test with user_id 0
        health_status["services"]["storage"] = "healthy"
        # health_status["storage"] = {
        #     "bucket": storage_service.bucket_name,
        #     "connected": True
        # }
    except Exception as e:
        logger.error(f"Storage health check failed: {str(e)}")
        health_status["services"]["storage"] = "unhealthy"
        health_status["status"] = "unhealthy"
        # health_status["storage"] = {
        #     "bucket": storage_service.bucket_name,
        #     "connected": False,
        #     "error": str(e)
        # }
    
    return health_status

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    try:
        # Initialize database
        init_db()
        logger.info("Database connection initialized during startup")
        
        # Initialize storage service
        try:
            # Test Supabase connection
            # await storage_service.list_user_files(0)  # Test with user_id 0
            logger.info("Supabase storage service initialized successfully")
        except Exception as e:
            logger.error(f"Storage service initialization failed: {str(e)}")
            # Don't raise the exception, let the app start without storage
            
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        # Don't raise the exception, let the app start without database

@app.get("/db-status")
async def db_status(db: Session = Depends(get_db)):
    """Check database connection status"""
    try:
        # First check if the users table exists using proper SQLAlchemy text()
        table_exists = db.execute(text("SHOW TABLES LIKE 'users'")).first()
        if not table_exists:
            return {
                "status": "disconnected",
                "message": "Database table 'users' does not exist"
            }
        
        # Test database connection by querying User table
        user_count = db.query(User).count()
        return {
            "status": "connected",
            "message": "Database connection successful",
            "user_count": user_count
        }
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        return {
            "status": "disconnected",
            "error": str(e)
        }

@app.get("/monitor/db")
async def monitor_db(db: Session = Depends(get_db)):
    """Monitor database health and performance"""
    try:
        # Check basic connection
        connection_check = db.execute(text("SELECT 1")).scalar()
        
        # Get database status
        db_status = db.execute(text("SHOW STATUS LIKE 'Threads_connected'")).first()
        threads_connected = db_status[1] if db_status else 0
        
        # Get direct user count
        user_count = db.execute(text("SELECT COUNT(*) FROM users")).scalar()
        
        # Get table sizes
        table_sizes = db.execute(text("""
            SELECT table_name, table_rows, data_length, index_length 
            FROM information_schema.tables 
            WHERE table_schema = DATABASE()
        """)).fetchall()
        
        # Format table sizes
        tables = []
        for table in table_sizes:
            tables.append({
                "name": table[0],
                "rows": table[1],
                "size_mb": round((table[2] + table[3]) / 1024 / 1024, 2)
            })
        
        return {
            "status": "healthy",
            "connection": "active",
            "threads_connected": threads_connected,
            "user_count": user_count,
            "tables": tables,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Database monitoring failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@app.get("/monitor/users")
async def monitor_users(db: Session = Depends(get_db)):
    """List all users in the database"""
    try:
        users = db.execute(text("SELECT id, username, email, created_at FROM users")).fetchall()
        return {
            "status": "success",
            "count": len(users),
            "users": [
                {
                    "id": user[0],
                    "username": user[1],
                    "email": user[2],
                    "created_at": user[3].isoformat() if user[3] else None
                }
                for user in users
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching users: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        } 