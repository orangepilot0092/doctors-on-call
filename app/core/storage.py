import uuid
from io import BytesIO
from datetime import timedelta
from minio import Minio
from app.core.config import settings

class StorageClient:
    def __init__(self):
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )
        self.bucket = settings.MINIO_BUCKET_NAME
        self._ensure_bucket()

    def _ensure_bucket(self):
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)

    def upload_file(self, file_bytes: bytes, file_name: str, content_type: str) -> str:
        ext = file_name.split('.')[-1] if '.' in file_name else 'bin'
        object_name = f"doctors/{uuid.uuid4()}.{ext}"
        
        data = BytesIO(file_bytes)
        self.client.put_object(
            self.bucket, object_name, data,
            length=len(file_bytes), content_type=content_type
        )
        return object_name

    def get_presigned_url(self, object_name: str) -> str:
        """Generates a secure, temporary URL to view the document (valid for 1 hour)."""
        return self.client.presigned_get_object(
            self.bucket, 
            object_name, 
            expires=timedelta(hours=1)
        )

storage_client = StorageClient()
