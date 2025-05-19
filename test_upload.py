import asyncio
import os
from dotenv import load_dotenv
from services.supabase_storage_service import SupabaseStorageService
from starlette.datastructures import UploadFile
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

async def test_upload():
    # Initialize the storage service
    storage_service = SupabaseStorageService()
    
    # Test file path - replace with your test PDF file path
    test_file_path = "test.pdf"  # Put your test PDF file in the project root
    
    try:
        # Create a mock UploadFile
        with open(test_file_path, "rb") as f:
            file_content = f.read()
        
        # Create UploadFile object
        upload_file = UploadFile(
            filename=test_file_path,
            file=open(test_file_path, "rb")
        )
        
        # Test upload
        logger.info("Starting upload test...")
        result = await storage_service.upload_file(upload_file, user_id=1)
        
        if result:
            logger.info("Upload successful!")
            logger.info(f"File info: {result}")
            logger.info(f"File URL: {result['url']}")
        else:
            logger.error("Upload failed - no result returned")
            
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
    finally:
        # Clean up
        if 'upload_file' in locals():
            await upload_file.close()

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_upload()) 