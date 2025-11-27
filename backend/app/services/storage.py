import boto3
from botocore.client import Config
from datetime import timedelta
from typing import Optional
import os

from app.core.config import get_settings


class StorageService:
    """MinIO 儲存服務"""

    def __init__(self):
        settings = get_settings()
        self.bucket = settings.minio_bucket
        self.client = boto3.client(
            "s3",
            endpoint_url=f"{'https' if settings.minio_secure else 'http'}://{settings.minio_endpoint}",
            aws_access_key_id=settings.minio_access_key,
            aws_secret_access_key=settings.minio_secret_key,
            config=Config(signature_version="s3v4"),
            region_name="us-east-1"
        )
        self._ensure_bucket()

    def _ensure_bucket(self):
        """確保 bucket 存在"""
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except:
            self.client.create_bucket(Bucket=self.bucket)

    def upload_file(self, file_path: str, object_name: str) -> str:
        """
        上傳檔案到儲存

        Args:
            file_path: 本地檔案路徑
            object_name: 儲存中的物件名稱

        Returns:
            物件的 key
        """
        self.client.upload_file(file_path, self.bucket, object_name)
        return object_name

    def download_file(self, object_name: str, file_path: str) -> str:
        """
        從儲存下載檔案

        Args:
            object_name: 儲存中的物件名稱
            file_path: 本地檔案路徑

        Returns:
            本地檔案路徑
        """
        self.client.download_file(self.bucket, object_name, file_path)
        return file_path

    def get_presigned_url(self, object_name: str, expires_in: int = 3600) -> str:
        """
        取得預簽名下載 URL

        Args:
            object_name: 儲存中的物件名稱
            expires_in: URL 有效期（秒），預設 1 小時

        Returns:
            預簽名 URL
        """
        url = self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": object_name},
            ExpiresIn=expires_in
        )
        return url

    def delete_file(self, object_name: str):
        """
        刪除檔案

        Args:
            object_name: 儲存中的物件名稱
        """
        self.client.delete_object(Bucket=self.bucket, Key=object_name)

    def file_exists(self, object_name: str) -> bool:
        """
        檢查檔案是否存在

        Args:
            object_name: 儲存中的物件名稱

        Returns:
            是否存在
        """
        try:
            self.client.head_object(Bucket=self.bucket, Key=object_name)
            return True
        except:
            return False

    def get_file_size(self, object_name: str) -> Optional[int]:
        """
        取得檔案大小

        Args:
            object_name: 儲存中的物件名稱

        Returns:
            檔案大小（bytes）或 None
        """
        try:
            response = self.client.head_object(Bucket=self.bucket, Key=object_name)
            return response["ContentLength"]
        except:
            return None


# Global instance
_storage_service: Optional[StorageService] = None


def get_storage_service() -> StorageService:
    """取得儲存服務實例"""
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service
