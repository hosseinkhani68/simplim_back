from supabase import create_client, Client
import os
from datetime import datetime
import logging
from typing import Optional, List, Dict, Any
from fastapi import UploadFile
import mimetypes
import requests
import io

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SupabaseStorageService:
    def __init__(self):
        """Initialize the storage service with lazy loading"""
        self._client = None
        self._initialized = False
        self._bucket_name = os.getenv('SUPABASE_BUCKET_NAME', 'pdfs')
        logger.info(f"SupabaseStorageService initialized with bucket: {self._bucket_name}")

    def _ensure_initialized(self):
        """Ensure the client is initialized"""
        if not self._initialized:
            try:
                supabase_url = os.getenv('SUPABASE_URL')
                supabase_key = os.getenv('SUPABASE_KEY')
                
                if not supabase_url or not supabase_key:
                    logger.warning("Supabase credentials not found. Storage operations will fail.")
                    return False
                
                self._client = create_client(supabase_url, supabase_key)
                self._initialized = True
                logger.info("Supabase client initialized successfully")
                return True
            except Exception as e:
                logger.error(f"Failed to initialize Supabase client: {str(e)}")
                return False
        return True

    async def upload_file(self, file: UploadFile, filename: str = None) -> Optional[Dict[str, Any]]:
        """Upload a file to Supabase Storage"""
        try:
            if not self._ensure_initialized():
                logger.error("Cannot upload file: Supabase client not initialized")
                return None

            # Verify client is initialized
            if not self._client:
                logger.error("Supabase client not initialized")
                raise ValueError("Supabase client not initialized")

            # Log configuration status
            logger.info(f"Attempting to upload file for user {filename}")
            logger.info(f"Supabase URL configured: {bool(os.getenv('SUPABASE_URL'))}")
            logger.info(f"Supabase Key configured: {bool(os.getenv('SUPABASE_KEY'))}")
            logger.info(f"Using bucket: {self._bucket_name}")

            # Verify bucket exists
            try:
                buckets = self._client.storage.list_buckets()
                bucket_names = [bucket.name for bucket in buckets]
                if self._bucket_name not in bucket_names:
                    logger.error(f"Bucket '{self._bucket_name}' not found in Supabase. Available buckets: {bucket_names}")
                    raise ValueError(f"Bucket '{self._bucket_name}' not found in Supabase")
                logger.info(f"Verified bucket '{self._bucket_name}' exists")
            except Exception as bucket_error:
                logger.error(f"Error checking bucket existence: {str(bucket_error)}")
                raise ValueError(f"Error checking bucket existence: {str(bucket_error)}")

            # Read file content
            try:
                content = await file.read()
                if not content:
                    logger.error("File content is empty")
                    raise ValueError("File content is empty")
                logger.info(f"Successfully read file content, size: {len(content)} bytes")
            except Exception as read_error:
                logger.error(f"Error reading file: {str(read_error)}")
                raise ValueError(f"Error reading file: {str(read_error)}")
            
            # Generate unique filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_filename = f"{timestamp}_{file.filename}"
            file_path = f"users/{filename}/{safe_filename}"
            logger.info(f"Generated file path: {file_path}")
            
            try:
                # Upload to Supabase Storage using direct HTTP request
                logger.info("Attempting to upload to Supabase Storage...")
                try:
                    # Construct the upload URL
                    upload_url = f"{os.getenv('SUPABASE_URL')}/storage/v1/object/{self._bucket_name}/{file_path}"
                    logger.info(f"Upload URL: {upload_url}")

                    # Set up headers
                    headers = {
                        "Authorization": f"Bearer {os.getenv('SUPABASE_KEY')}",
                        "Content-Type": file.content_type or "application/pdf",
                        "x-upsert": "true"  # Enable upsert
                    }
                    logger.info(f"Request headers: {headers}")

                    # Make the upload request
                    logger.info("Sending upload request...")
                    res = requests.post(upload_url, headers=headers, data=content)
                    logger.info(f"Response status code: {res.status_code}")
                    logger.info(f"Response headers: {res.headers}")
                    logger.info(f"Response body: {res.text}")
                    
                    if res.status_code not in [200, 201]:
                        error_msg = f"HTTP Upload Failed: {res.status_code} - {res.text}"
                        logger.error(error_msg)
                        raise ValueError(error_msg)
                    
                    # Parse the response
                    try:
                        response_data = res.json()
                        logger.info(f"Parsed response data: {response_data}")
                    except Exception as json_error:
                        logger.warning(f"Could not parse response as JSON: {str(json_error)}")
                        response_data = {}

                    logger.info(f"Upload successful: {res.status_code}")
                except requests.exceptions.RequestException as req_error:
                    logger.error(f"Request error: {str(req_error)}")
                    raise ValueError(f"Request error: {str(req_error)}")
                except Exception as upload_error:
                    logger.error(f"Error during upload: {str(upload_error)}")
                    raise ValueError(f"Error during upload: {str(upload_error)}")

                # Get public URL
                try:
                    url = self._client.storage.from_(self._bucket_name).get_public_url(file_path)
                    logger.info(f"Generated public URL: {url}")
                except Exception as url_error:
                    logger.error(f"Error getting public URL: {str(url_error)}")
                    raise ValueError(f"Error getting public URL: {str(url_error)}")
                
                file_info = {
                    "filename": safe_filename,
                    "original_name": file.filename,
                    "path": file_path,
                    "size": len(content),
                    "content_type": file.content_type or "application/pdf",
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

    async def delete_file(self, filename: str) -> bool:
        """Delete a file from Supabase Storage"""
        try:
            if not self._ensure_initialized():
                logger.error("Cannot delete file: Supabase client not initialized")
                return False

            file_path = f"users/{filename}/{filename}"
            self._client.storage.from_(self._bucket_name).remove([file_path])
            logger.info(f"File deleted successfully from Supabase: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting file from Supabase: {str(e)}")
            return False

    async def get_file_url(self, filename: str) -> Optional[str]:
        """Get the public URL for a file"""
        try:
            if not self._ensure_initialized():
                logger.error("Cannot get file URL: Supabase client not initialized")
                return None

            file_path = f"users/{filename}/{filename}"
            url = self._client.storage.from_(self._bucket_name).get_public_url(file_path)
            return url
            
        except Exception as e:
            logger.error(f"Error getting file URL from Supabase: {str(e)}")
            return None

    async def list_user_files(self, user_id: int) -> List[Dict]:
        """List all files for a specific user"""
        try:
            prefix = f"users/{user_id}/"
            response = self._client.storage.from_(self._bucket_name).list(prefix)
            
            files = []
            for item in response:
                files.append({
                    "filename": item["name"].split("/")[-1],
                    "size": item["metadata"]["size"],
                    "created": item["created_at"],
                    "updated": item["updated_at"],
                    "url": self._client.storage.from_(self._bucket_name).get_public_url(item["name"])
                })
            
            return files
            
        except Exception as e:
            logger.error(f"Error listing user files from Supabase: {str(e)}")
            return []

    async def get_file_metadata(self, filename: str, user_id: int) -> Optional[dict]:
        """Get metadata for a specific file"""
        try:
            file_path = f"users/{user_id}/{filename}"
            response = self._client.storage.from_(self._bucket_name).get_public_url(file_path)
            
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