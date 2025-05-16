from google.cloud import storage
import os
from datetime import datetime, timedelta
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class GCSService:
    def __init__(self):
        self.storage_client = storage.Client()
        self.bucket_name = os.getenv('GCS_BUCKET_NAME')
        self.bucket = self.storage_client.bucket(self.bucket_name)
        
    async def upload_file(self, file_data: bytes, file_name: str, user_id: int) -> Optional[str]:
        """
        Upload a file to Google Cloud Storage
        Returns the GCS URL if successful, None if failed
        """
        try:
            # Create a unique blob name
            blob_name = f"users/{user_id}/{file_name}"
            blob = self.bucket.blob(blob_name)
            
            # Upload the file
            blob.upload_from_string(
                file_data,
                content_type='application/pdf'
            )
            
            # Make the blob publicly accessible
            blob.make_public()
            
            # Get the public URL
            url = blob.public_url
            logger.info(f"File uploaded successfully to {url}")
            return url
            
        except Exception as e:
            logger.error(f"Error uploading file to GCS: {str(e)}")
            return None
            
    async def delete_file(self, file_name: str, user_id: int) -> bool:
        """
        Delete a file from Google Cloud Storage
        Returns True if successful, False if failed
        """
        try:
            blob_name = f"users/{user_id}/{file_name}"
            blob = self.bucket.blob(blob_name)
            blob.delete()
            logger.info(f"File deleted successfully from GCS: {blob_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting file from GCS: {str(e)}")
            return False
            
    async def get_file_url(self, file_name: str, user_id: int) -> Optional[str]:
        """
        Get a signed URL for downloading a file
        Returns the URL if successful, None if failed
        """
        try:
            blob_name = f"users/{user_id}/{file_name}"
            blob = self.bucket.blob(blob_name)
            
            # Generate a signed URL that expires in 1 hour
            url = blob.generate_signed_url(
                version="v4",
                expiration=datetime.utcnow() + timedelta(hours=1),
                method="GET"
            )
            return url
            
        except Exception as e:
            logger.error(f"Error generating signed URL: {str(e)}")
            return None
            
    async def list_user_files(self, user_id: int) -> list:
        """
        List all files for a specific user
        Returns a list of file information
        """
        try:
            prefix = f"users/{user_id}/"
            blobs = self.bucket.list_blobs(prefix=prefix)
            
            files = []
            for blob in blobs:
                files.append({
                    "name": blob.name.split("/")[-1],
                    "size": blob.size,
                    "created": blob.time_created,
                    "url": blob.public_url
                })
            
            return files
            
        except Exception as e:
            logger.error(f"Error listing user files: {str(e)}")
            return []
            
    async def get_file_metadata(self, file_name: str, user_id: int) -> Optional[dict]:
        """
        Get metadata for a specific file
        Returns file metadata if successful, None if failed
        """
        try:
            blob_name = f"users/{user_id}/{file_name}"
            blob = self.bucket.get_blob(blob_name)
            
            if blob:
                return {
                    "name": blob.name.split("/")[-1],
                    "size": blob.size,
                    "created": blob.time_created,
                    "updated": blob.updated,
                    "content_type": blob.content_type,
                    "url": blob.public_url
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting file metadata: {str(e)}")
            return None 