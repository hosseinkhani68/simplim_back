from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import os
from datetime import datetime
import logging
from services.supabase_storage_service import SupabaseStorageService

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Initialize storage service
storage_service = SupabaseStorageService()

# Add a test endpoint
@router.get("/test")
async def test_pdf():
    """Test endpoint to verify PDF router is working"""
    return {"message": "PDF router is working"}

@router.post("/upload")
async def test_upload_pdf(file: UploadFile = File(...)):
    """Test endpoint for uploading PDF files without authentication"""
    try:
        # Log the incoming file details
        logger.info(f"Attempting to upload file: {file.filename}")
        
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")

        # Log Supabase configuration
        logger.info(f"Supabase URL configured: {bool(os.getenv('SUPABASE_URL'))}")
        logger.info(f"Supabase Key configured: {bool(os.getenv('SUPABASE_KEY'))}")
        logger.info(f"Supabase Bucket: {os.getenv('SUPABASE_BUCKET_NAME', 'pdfs')}")

        # Upload file using storage service (using a test user ID of 1)
        try:
            file_info = await storage_service.upload_file(file, 1)
            if not file_info:
                logger.error("Storage service returned None for file_info")
                raise HTTPException(
                    status_code=500,
                    detail="Failed to upload file - storage service returned no file info"
                )
            return {
                "message": "File uploaded successfully",
                "file_info": file_info
            }
        except ValueError as ve:
            logger.error(f"Validation error: {str(ve)}")
            raise HTTPException(status_code=400, detail=str(ve))
        except Exception as storage_error:
            logger.error(f"Storage service error: {str(storage_error)}")
            raise HTTPException(
                status_code=500,
                detail=f"Storage service error: {str(storage_error)}"
            )

    except HTTPException as he:
        # Re-raise HTTP exceptions as they are already properly formatted
        raise he
    except Exception as e:
        logger.error(f"Unexpected error in test_upload_pdf: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )

# Import dependencies
# from database.database import get_db
# from database.models import PDFDocument as DBPDFDocument, User as DBUser
# from routers.auth import oauth2_scheme
# from jose import jwt
# from utils.auth_utils import SECRET_KEY, ALGORITHM

# @router.post("/upload")
# async def upload_pdf(
#     file: UploadFile = File(...),
#     token: str = Depends(oauth2_scheme),
#     db: Session = Depends(get_db)
# ):
#     try:
#         # Verify user
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         email: str = payload.get("sub")
#         user = db.query(DBUser).filter(DBUser.email == email).first()
        
#         if not user:
#             raise HTTPException(status_code=404, detail="User not found")

#         # Validate file type
#         if not file.filename.lower().endswith('.pdf'):
#             raise HTTPException(status_code=400, detail="Only PDF files are allowed")

#         # Upload file using storage service
#         file_info = await storage_service.upload_file(file, user.id)
#         if not file_info:
#             raise HTTPException(status_code=500, detail="Failed to upload file")

#         # Create database entry
#         db_pdf = DBPDFDocument(
#             user_id=user.id,
#             filename=file_info["filename"],
#             file_path=file_info["url"],  # Store Supabase URL
#             size=file_info["size"]
#         )
#         db.add(db_pdf)
#         db.commit()
#         db.refresh(db_pdf)
#         logger.info(f"Created database entry for file: {file_info['filename']}")

#         return {
#             "id": db_pdf.id,
#             "filename": db_pdf.filename,
#             "size": db_pdf.size,
#             "upload_date": db_pdf.upload_date,
#             "url": file_info["url"],
#             "original_name": file_info["original_name"]
#         }

#     except Exception as e:
#         logger.error(f"Error in upload_pdf: {str(e)}")
#         raise HTTPException(status_code=500, detail=str(e))

# @router.get("/list")
# async def list_pdfs(
#     token: str = Depends(oauth2_scheme),
#     db: Session = Depends(get_db)
# ):
#     try:
#         # Verify user
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         email: str = payload.get("sub")
#         user = db.query(DBUser).filter(DBUser.email == email).first()
        
#         if not user:
#             raise HTTPException(status_code=404, detail="User not found")

#         # Get user's PDFs from storage
#         files = await storage_service.list_user_files(user.id)
        
#         # Get database entries
#         db_pdfs = db.query(DBPDFDocument).filter(
#             DBPDFDocument.user_id == user.id
#         ).order_by(DBPDFDocument.upload_date.desc()).all()
        
#         # Combine storage and database info
#         pdf_list = []
#         for db_pdf in db_pdfs:
#             file_info = next((f for f in files if f["filename"] == db_pdf.filename), None)
#             if file_info:
#                 pdf_list.append({
#                     "id": db_pdf.id,
#                     "filename": db_pdf.filename,
#                     "size": db_pdf.size,
#                     "upload_date": db_pdf.upload_date,
#                     "url": file_info["url"]
#                 })

#         return pdf_list

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @router.delete("/{pdf_id}")
# async def delete_pdf(
#     pdf_id: int,
#     token: str = Depends(oauth2_scheme),
#     db: Session = Depends(get_db)
# ):
#     try:
#         # Verify user
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         email: str = payload.get("sub")
#         user = db.query(DBUser).filter(DBUser.email == email).first()
        
#         if not user:
#             raise HTTPException(status_code=404, detail="User not found")

#         # Get PDF
#         pdf = db.query(DBPDFDocument).filter(
#             DBPDFDocument.id == pdf_id,
#             DBPDFDocument.user_id == user.id
#         ).first()

#         if not pdf:
#             raise HTTPException(status_code=404, detail="PDF not found")

#         # Delete from storage
#         success = await storage_service.delete_file(pdf.filename, user.id)
#         if not success:
#             raise HTTPException(status_code=500, detail="Failed to delete file from storage")

#         # Delete database entry
#         db.delete(pdf)
#         db.commit()

#         return {"message": "PDF deleted successfully"}

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e)) 