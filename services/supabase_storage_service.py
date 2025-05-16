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
        try:
            # Initialize Supabase client
            self.supabase_url = os.getenv('SUPABASE_URL')
            self.supabase_key = os.getenv('SUPABASE_KEY')
            self.bucket_name = os.getenv('SUPABASE_BUCKET_NAME', 'pdfs')
            
            # Log configuration (without sensitive data)
            logger.info(f"Initializing Supabase storage service with URL: {self.supabase_url}")
            logger.info(f"Using bucket: {self.bucket_name}")
            
            if not self.supabase_url or not self.supabase_key:
                error_msg = "Supabase URL and key must be set in environment variables"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # Test Supabase URL accessibility
            try:
                response = requests.get(self.supabase_url)
                if response.status_code != 200:
                    logger.error(f"Supabase URL not accessible. Status code: {response.status_code}")
                    raise ConnectionError(f"Supabase URL not accessible. Status code: {response.status_code}")
                logger.info("Supabase URL is accessible")
            except requests.exceptions.RequestException as e:
                logger.error(f"Failed to connect to Supabase URL: {str(e)}")
                raise ConnectionError(f"Failed to connect to Supabase URL: {str(e)}")
                
            # Test connection
            self.client: Client = create_client(self.supabase_url, self.supabase_key)
            
            # Verify bucket exists
            try:
                self.client.storage.get_bucket(self.bucket_name)
                logger.info(f"Successfully connected to Supabase and verified bucket: {self.bucket_name}")
            except Exception as e:
                logger.error(f"Failed to verify bucket existence: {str(e)}")
                # Try to create the bucket if it doesn't exist
                try:
                    self.client.storage.create_bucket(self.bucket_name, {"public": True})
                    logger.info(f"Created new bucket: {self.bucket_name}")
                except Exception as create_error:
                    logger.error(f"Failed to create bucket: {str(create_error)}")
                    raise
                
        except Exception as e:
            logger.error(f"Failed to initialize Supabase storage service: {str(e)}")
            raise

    async def test_connection(self) -> Dict:
        """Test the connection to Supabase and return detailed status"""
        try:
            # Test basic connection
            response = requests.get(self.supabase_url)
            connection_status = {
                "url_accessible": response.status_code == 200,
                "status_code": response.status_code,
                "bucket_exists": False,
                "bucket_public": False,
                "error": None
            }
            
            # Test bucket access
            try:
                bucket = self.client.storage.get_bucket(self.bucket_name)
                connection_status["bucket_exists"] = True
                connection_status["bucket_public"] = bucket.get("public", False)
            except Exception as e:
                connection_status["error"] = str(e)
                
            return connection_status
            
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return {
                "url_accessible": False,
                "status_code": None,
                "bucket_exists": False,
                "bucket_public": False,
                "error": str(e)
            }

    async def upload_file(self, file: UploadFile, user_id: int) -> Optional[dict]:
        """
        Upload a file to Supabase Storage
        Returns file info if successful, None if failed
        """
        try:
            # Read file content
            content = await file.read()
            
            # Generate unique filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_filename = f"{timestamp}_{file.filename}"
            file_path = f"users/{user_id}/{safe_filename}"
            
            # Upload to Supabase Storage
            response = self.client.storage.from_(self.bucket_name).upload(
                file_path,
                content,
                {"content-type": "application/pdf"}
            )
            
            # Get public URL
            url = self.client.storage.from_(self.bucket_name).get_public_url(file_path)
            
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
            
        except Exception as e:
            logger.error(f"Error uploading file to Supabase: {str(e)}")
            return None
            
    async def delete_file(self, filename: str, user_id: int) -> bool:
        """
        Delete a file from Supabase Storage
        Returns True if successful, False if failed
        """
        try:
            file_path = f"users/{user_id}/{filename}"
            self.client.storage.from_(self.bucket_name).remove([file_path])
            logger.info(f"File deleted successfully from Supabase: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting file from Supabase: {str(e)}")
            return False
            
    async def get_file_url(self, filename: str, user_id: int) -> Optional[str]:
        """
        Get the public URL for a file
        Returns the URL if successful, None if failed
        """
        try:
            file_path = f"users/{user_id}/{filename}"
            url = self.client.storage.from_(self.bucket_name).get_public_url(file_path)
            return url
            
        except Exception as e:
            logger.error(f"Error getting file URL from Supabase: {str(e)}")
            return None
            
    async def list_user_files(self, user_id: int) -> List[Dict]:
        """
        List all files for a specific user
        Returns a list of file information
        """
        try:
            prefix = f"users/{user_id}/"
            logger.info(f"Listing files for user {user_id} with prefix: {prefix}")
            
            response = self.client.storage.from_(self.bucket_name).list(prefix)
            logger.info(f"Successfully listed files for user {user_id}")
            
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
            raise  # Re-raise the exception to be handled by the caller
            
    async def get_file_metadata(self, filename: str, user_id: int) -> Optional[dict]:
        """
        Get metadata for a specific file
        Returns file metadata if successful, None if failed
        """
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