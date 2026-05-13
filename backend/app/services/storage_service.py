import aioboto3
from typing import Optional
from app.core.config import settings
from loguru import logger

class StorageService:
    def __init__(self):
        self.session = aioboto3.Session()
        self.bucket_name = settings.S3_BUCKET_NAME
        self.region = settings.AWS_REGION

    async def upload_file(self, file_content: bytes, file_name: str, content_type: str) -> Optional[str]:
        """
        Upload a file to S3 and return its URL.
        """
        try:
            async with self.session.client(
                "s3",
                region_name=self.region,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            ) as s3:
                await s3.put_object(
                    Bucket=self.bucket_name,
                    Key=file_name,
                    Body=file_content,
                    ContentType=content_type,
                )
                url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{file_name}"
                return url
        except Exception as e:
            logger.error(f"S3 upload failed: {e}")
            return None

    async def delete_file(self, file_name: str) -> bool:
        """
        Delete a file from S3.
        """
        try:
            async with self.session.client(
                "s3",
                region_name=self.region,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            ) as s3:
                await s3.delete_object(Bucket=self.bucket_name, Key=file_name)
                return True
        except Exception as e:
            logger.error(f"S3 deletion failed: {e}")
            return False
