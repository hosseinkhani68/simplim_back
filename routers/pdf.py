from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import os
import boto3
from datetime import datetime
from models.user import PDFDocument, PDFDocumentCreate
from database.database import get_db
from database.models import PDFDocument as DBPDFDocument, User as DBUser
from routers.auth import oauth2_scheme
from jose import jwt
from utils.auth_utils import SECRET_KEY, ALGORITHM
import magic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize S3 client
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION', 'us-east-1')
)

BUCKET_NAME = os.getenv('AWS_BUCKET_NAME')

router = APIRouter()

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

        # Create S3 key (path) for the file
        s3_key = f"users/{user.id}/{file.filename}"

        # Upload to S3
        file_content = await file.read()
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=s3_key,
            Body=file_content,
            ContentType='application/pdf'
        )

        # Get file size
        file_size = len(file_content)

        # Create database entry
        db_pdf = DBPDFDocument(
            user_id=user.id,
            filename=file.filename,
            file_path=s3_key,  # Store S3 key instead of local path
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

        # Delete from S3
        s3_client.delete_object(
            Bucket=BUCKET_NAME,
            Key=pdf.file_path
        )

        # Delete database entry
        db.delete(pdf)
        db.commit()

        return {"message": "PDF deleted successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 