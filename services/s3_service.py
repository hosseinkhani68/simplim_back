import boto3
import os
from botocore.exceptions import ClientError
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class S3Service:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        self.bucket_name = os.getenv('AWS_BUCKET_NAME')
        
    async def upload_file(self, file_data: bytes, file_name: str, user_id: int) -> Optional[str]:
        """
        Upload a file to S3
        Returns the S3 URL if successful, None if failed
        """
        try:
            # Create a unique key for the file
            s3_key = f"users/{user_id}/{file_name}"
            
            # Upload the file
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_data
            )
            
            # Generate the URL
            url = f"https://{self.bucket_name}.s3.amazonaws.com/{s3_key}"
            logger.info(f"File uploaded successfully to {url}")
            return url
            
        except ClientError as e:
            logger.error(f"Error uploading file to S3: {str(e)}")
            return None
            
    async def delete_file(self, file_name: str, user_id: int) -> bool:
        """
        Delete a file from S3
        Returns True if successful, False if failed
        """
        try:
            s3_key = f"users/{user_id}/{file_name}"
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            logger.info(f"File deleted successfully from S3: {s3_key}")
            return True
            
        except ClientError as e:
            logger.error(f"Error deleting file from S3: {str(e)}")
            return False
            
    async def get_file_url(self, file_name: str, user_id: int) -> Optional[str]:
        """
        Get a pre-signed URL for downloading a file
        Returns the URL if successful, None if failed
        """
        try:
            s3_key = f"users/{user_id}/{file_name}"
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': s3_key
                },
                ExpiresIn=3600  # URL expires in 1 hour
            )
            return url
            
        except ClientError as e:
            logger.error(f"Error generating pre-signed URL: {str(e)}")
            return None 