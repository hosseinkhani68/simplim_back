from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import os
import shutil
from datetime import datetime
from models.user import PDFDocument, PDFDocumentCreate
from database.database import get_db
from database.models import PDFDocument as DBPDFDocument
from routers.auth import oauth2_scheme
from jose import jwt
from utils.auth_utils import SECRET_KEY, ALGORITHM
import magic

router = APIRouter()

# Create uploads directory if it doesn't exist
UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

@router.post("/upload", response_model=PDFDocument)
async def upload_pdf(
    file: UploadFile = File(...),
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    try:
        # Verify user
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        user = db.query(DBUser).filter(DBUser.email == email).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")

        # Create user-specific directory
        user_dir = os.path.join(UPLOAD_DIR, str(user.id))
        if not os.path.exists(user_dir):
            os.makedirs(user_dir)

        # Save file
        file_path = os.path.join(user_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Get file size
        file_size = os.path.getsize(file_path)

        # Create database entry
        db_pdf = DBPDFDocument(
            user_id=user.id,
            filename=file.filename,
            file_path=file_path,
            size=file_size
        )
        db.add(db_pdf)
        db.commit()
        db.refresh(db_pdf)

        return db_pdf

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list", response_model=List[PDFDocument])
async def list_pdfs(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    try:
        # Verify user
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        user = db.query(DBUser).filter(DBUser.email == email).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Get user's PDFs
        pdfs = db.query(DBPDFDocument).filter(
            DBPDFDocument.user_id == user.id
        ).order_by(DBPDFDocument.upload_date.desc()).all()

        return pdfs

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{pdf_id}")
async def delete_pdf(
    pdf_id: int,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    try:
        # Verify user
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        user = db.query(DBUser).filter(DBUser.email == email).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Get PDF
        pdf = db.query(DBPDFDocument).filter(
            DBPDFDocument.id == pdf_id,
            DBPDFDocument.user_id == user.id
        ).first()

        if not pdf:
            raise HTTPException(status_code=404, detail="PDF not found")

        # Delete file
        if os.path.exists(pdf.file_path):
            os.remove(pdf.file_path)

        # Delete database entry
        db.delete(pdf)
        db.commit()

        return {"message": "PDF deleted successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 