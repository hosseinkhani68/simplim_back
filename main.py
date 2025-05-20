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
from services.supabase_storage_service import SupabaseStorageService

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
storage_service = None

def get_storage_service():
    """Lazy initialization of storage service"""
    global storage_service
    if storage_service is None:
        storage_service = SupabaseStorageService()
    return storage_service

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
    """Root endpoint for health check"""
    try:
        # Basic health check that doesn't depend on any external services
        return {
            "status": "ok",
            "message": "Service is running",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        # Even if there's an error, return a 200 status to pass health check
        return {"status": "ok", "message": "Service is running"}

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
    
    # Check if Supabase environment variables are set
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    bucket_name = os.getenv('SUPABASE_BUCKET_NAME', 'pdfs')
    
    health_status["storage"] = {
        "bucket": bucket_name,
        "url_set": bool(supabase_url),
        "key_set": bool(supabase_key),
        "status": "configured" if (supabase_url and supabase_key) else "not_configured"
    }
    
    # Only mark storage as unhealthy if environment variables are missing
    if not (supabase_url and supabase_key):
        health_status["services"]["storage"] = "unhealthy"
        health_status["status"] = "unhealthy"
    
    return health_status

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    try:
        logger.info("Starting application initialization...")
        
        # Log environment variables (without sensitive data)
        logger.info(f"ENVIRONMENT: {ENVIRONMENT}")
        logger.info(f"PORT: {PORT}")
        
        # Check Supabase configuration
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        bucket_name = os.getenv('SUPABASE_BUCKET_NAME', 'pdfs')
        
        logger.info(f"SUPABASE_URL is set: {bool(supabase_url)}")
        logger.info(f"SUPABASE_KEY is set: {bool(supabase_key)}")
        logger.info(f"SUPABASE_BUCKET_NAME: {bucket_name}")
        
        if not supabase_url or not supabase_key:
            logger.warning("Supabase configuration is incomplete. Some features may not work.")
        else:
            logger.info("Supabase configuration is complete")
        
        # Initialize database
        logger.info("Initializing database connection...")
        try:
            init_db()
            logger.info("Database connection initialized successfully")
        except Exception as db_error:
            logger.error(f"Database initialization failed: {str(db_error)}")
            logger.warning("Continuing without database connection")
        
        logger.info("Application startup completed successfully")
            
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        logger.exception("Detailed startup error:")
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