from supabase import create_client, Client
import os
from datetime import datetime
import logging
from typing import Optional, List, Dict
from fastapi import UploadFile
import mimetypes
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SupabaseStorageService:
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        self.bucket_name = os.getenv('SUPABASE_BUCKET_NAME', 'pdfs')
        self._client = None
        
        # Log configuration (without sensitive data)
        logger.info(f"Initializing Supabase storage service with URL: {bool(self.supabase_url)}")
        logger.info(f"Using bucket: {self.bucket_name}")
        
        if not self.supabase_url or not self.supabase_key:
            logger.warning("Supabase URL or key not set in environment variables")
        else:
            # Try to initialize the client, but don't fail if it doesn't work
            try:
                self._client = create_client(self.supabase_url, self.supabase_key)
                logger.info("Successfully initialized Supabase client")
            except Exception as e:
                logger.warning(f"Failed to initialize Supabase client: {str(e)}")
                self._client = None
    
    @property
    def client(self) -> Client:
        """Lazy initialization of Supabase client"""
        if self._client is None:
            if not self.supabase_url or not self.supabase_key:
                raise ValueError("Supabase URL and key must be set in environment variables")
            try:
                self._client = create_client(self.supabase_url, self.supabase_key)
                logger.info("Successfully initialized Supabase client")
            except Exception as e:
                logger.error(f"Failed to initialize Supabase client: {str(e)}")
                raise ValueError(f"Failed to initialize Supabase client: {str(e)}")
        return self._client

    async def upload_file(self, file: UploadFile, user_id: int) -> Optional[dict]:
        """Upload a file to Supabase Storage"""
        try:
            # Verify client is initialized
            if not self._client:
                logger.error("Supabase client not initialized")
                raise ValueError("Supabase client not initialized")

            # Log configuration status
            logger.info(f"Attempting to upload file for user {user_id}")
            logger.info(f"Supabase URL configured: {bool(self.supabase_url)}")
            logger.info(f"Supabase Key configured: {bool(self.supabase_key)}")
            logger.info(f"Using bucket: {self.bucket_name}")

            # Verify bucket exists
            try:
                buckets = self._client.storage.list_buckets()
                bucket_names = [bucket['name'] for bucket in buckets]
                if self.bucket_name not in bucket_names:
                    logger.error(f"Bucket '{self.bucket_name}' not found in Supabase. Available buckets: {bucket_names}")
                    raise ValueError(f"Bucket '{self.bucket_name}' not found in Supabase")
                logger.info(f"Verified bucket '{self.bucket_name}' exists")
            except Exception as bucket_error:
                logger.error(f"Error checking bucket existence: {str(bucket_error)}")
                raise ValueError(f"Error checking bucket existence: {str(bucket_error)}")

            # Read file content
            content = await file.read()
            logger.info(f"Successfully read file content, size: {len(content)} bytes")
            
            # Generate unique filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_filename = f"{timestamp}_{file.filename}"
            file_path = f"users/{user_id}/{safe_filename}"
            logger.info(f"Generated file path: {file_path}")
            
            try:
                # Upload to Supabase Storage
                logger.info("Attempting to upload to Supabase Storage...")
                response = self._client.storage.from_(self.bucket_name).upload(
                    file_path,
                    content,
                    {"content-type": "application/pdf"}
                )
                logger.info("Successfully uploaded to Supabase Storage")
                
                # Get public URL
                url = self._client.storage.from_(self.bucket_name).get_public_url(file_path)
                logger.info(f"Generated public URL: {url}")
                
                file_info = {
                    "filename": safe_filename,
                    "original_name": file.filename,
                    "path": file_path,
                    "size": len(content),
                    "content_type": "application/pdf",
                    "url": url,
                    "upload_date": datetime.now().isoformat()
                }
                
                logger.info(f"File uploaded successfully to Supabase: {file_info}")
                return file_info
                
            except Exception as supabase_error:
                logger.error(f"Supabase storage error: {str(supabase_error)}")
                raise Exception(f"Supabase storage error: {str(supabase_error)}")
            
        except Exception as e:
            logger.error(f"Error uploading file to Supabase: {str(e)}")
            return None

    async def delete_file(self, filename: str, user_id: int) -> bool:
        """Delete a file from Supabase Storage"""
        try:
            file_path = f"users/{user_id}/{filename}"
            self.client.storage.from_(self.bucket_name).remove([file_path])
            logger.info(f"File deleted successfully from Supabase: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting file from Supabase: {str(e)}")
            return False

    async def get_file_url(self, filename: str, user_id: int) -> Optional[str]:
        """Get the public URL for a file"""
        try:
            file_path = f"users/{user_id}/{filename}"
            url = self.client.storage.from_(self.bucket_name).get_public_url(file_path)
            return url
            
        except Exception as e:
            logger.error(f"Error getting file URL from Supabase: {str(e)}")
            return None

    async def list_user_files(self, user_id: int) -> List[Dict]:
        """List all files for a specific user"""
        try:
            prefix = f"users/{user_id}/"
            response = self.client.storage.from_(self.bucket_name).list(prefix)
            
            files = []
            for item in response:
                files.append({
                    "filename": item["name"].split("/")[-1],
                    "size": item["metadata"]["size"],
                    "created": item["created_at"],
                    "updated": item["updated_at"],
                    "url": self.client.storage.from_(self.bucket_name).get_public_url(item["name"])
                })
            
            return files
            
        except Exception as e:
            logger.error(f"Error listing user files from Supabase: {str(e)}")
            return []

    async def get_file_metadata(self, filename: str, user_id: int) -> Optional[dict]:
        """Get metadata for a specific file"""
        try:
            file_path = f"users/{user_id}/{filename}"
            response = self.client.storage.from_(self.bucket_name).get_public_url(file_path)
            
            if response:
                return {
                    "filename": filename,
                    "url": response,
                    "path": file_path
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting file metadata from Supabase: {str(e)}")
            return None 