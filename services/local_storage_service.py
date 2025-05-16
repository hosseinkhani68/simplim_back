import os
import shutil
from datetime import datetime
import logging
from typing import Optional
import aiofiles
from fastapi import UploadFile
import mimetypes
from pathlib import Path

logger = logging.getLogger(__name__)

class LocalStorageService:
    def __init__(self):
        # Base directory for all uploads
        self.base_dir = os.getenv('UPLOAD_DIR', '/app/uploads')
        # Ensure base directory exists
        os.makedirs(self.base_dir, exist_ok=True)
        logger.info(f"Using upload directory: {self.base_dir}")
        
    async def upload_file(self, file: UploadFile, user_id: int) -> Optional[dict]:
        """
        Upload a file to local storage
        Returns file info if successful, None if failed
        """
        try:
            # Create user directory
            user_dir = os.path.join(self.base_dir, str(user_id))
            os.makedirs(user_dir, exist_ok=True)
            
            # Generate unique filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_filename = f"{timestamp}_{file.filename}"
            file_path = os.path.join(user_dir, safe_filename)
            
            # Save file
            async with aiofiles.open(file_path, 'wb') as out_file:
                content = await file.read()
                await out_file.write(content)
            
            # Get file info
            file_size = os.path.getsize(file_path)
            content_type = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
            
            file_info = {
                "filename": safe_filename,
                "original_name": file.filename,
                "path": file_path,
                "size": file_size,
                "content_type": content_type,
                "upload_date": datetime.now().isoformat()
            }
            
            logger.info(f"File uploaded successfully: {file_info}")
            return file_info
            
        except Exception as e:
            logger.error(f"Error uploading file: {str(e)}")
            return None
            
    async def delete_file(self, filename: str, user_id: int) -> bool:
        """
        Delete a file from local storage
        Returns True if successful, False if failed
        """
        try:
            file_path = os.path.join(self.base_dir, str(user_id), filename)
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"File deleted successfully: {file_path}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error deleting file: {str(e)}")
            return False
            
    async def get_file_path(self, filename: str, user_id: int) -> Optional[str]:
        """
        Get the full path of a file
        Returns the path if file exists, None if not found
        """
        try:
            file_path = os.path.join(self.base_dir, str(user_id), filename)
            if os.path.exists(file_path):
                return file_path
            return None
            
        except Exception as e:
            logger.error(f"Error getting file path: {str(e)}")
            return None
            
    async def list_user_files(self, user_id: int) -> list:
        """
        List all files for a specific user
        Returns a list of file information
        """
        try:
            user_dir = os.path.join(self.base_dir, str(user_id))
            if not os.path.exists(user_dir):
                return []
                
            files = []
            for filename in os.listdir(user_dir):
                file_path = os.path.join(user_dir, filename)
                if os.path.isfile(file_path):
                    stat = os.stat(file_path)
                    files.append({
                        "filename": filename,
                        "size": stat.st_size,
                        "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "path": file_path
                    })
            
            return files
            
        except Exception as e:
            logger.error(f"Error listing user files: {str(e)}")
            return []
            
    async def get_file_metadata(self, filename: str, user_id: int) -> Optional[dict]:
        """
        Get metadata for a specific file
        Returns file metadata if successful, None if failed
        """
        try:
            file_path = os.path.join(self.base_dir, str(user_id), filename)
            if not os.path.exists(file_path):
                return None
                
            stat = os.stat(file_path)
            return {
                "filename": filename,
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "content_type": mimetypes.guess_type(file_path)[0] or 'application/octet-stream',
                "path": file_path
            }
            
        except Exception as e:
            logger.error(f"Error getting file metadata: {str(e)}")
            return None
            
    async def cleanup_old_files(self, days: int = 30) -> int:
        """
        Clean up files older than specified days
        Returns number of files deleted
        """
        try:
            count = 0
            cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
            
            for user_dir in os.listdir(self.base_dir):
                user_path = os.path.join(self.base_dir, user_dir)
                if os.path.isdir(user_path):
                    for filename in os.listdir(user_path):
                        file_path = os.path.join(user_path, filename)
                        if os.path.isfile(file_path):
                            if os.path.getmtime(file_path) < cutoff_date:
                                os.remove(file_path)
                                count += 1
                                
            logger.info(f"Cleaned up {count} old files")
            return count
            
        except Exception as e:
            logger.error(f"Error cleaning up old files: {str(e)}")
            return 0 