from fastapi import APIRouter
import redis

from app.core.config import get_settings

router = APIRouter()
settings = get_settings()


@router.get("/health")
async def health_check():
    """
    健康檢查

    檢查服務及其依賴項是否正常運作
    """
    redis_ok = False
    storage_ok = False

    # Check Redis
    try:
        r = redis.from_url(settings.redis_url)
        r.ping()
        redis_ok = True
    except:
        pass

    # Check MinIO (basic connectivity)
    try:
        import boto3
        from botocore.client import Config

        client = boto3.client(
            "s3",
            endpoint_url=f"{'https' if settings.minio_secure else 'http'}://{settings.minio_endpoint}",
            aws_access_key_id=settings.minio_access_key,
            aws_secret_access_key=settings.minio_secret_key,
            config=Config(signature_version="s3v4"),
            region_name="us-east-1"
        )
        client.list_buckets()
        storage_ok = True
    except:
        pass

    status = "healthy" if (redis_ok and storage_ok) else "unhealthy"

    return {
        "status": status,
        "redis": redis_ok,
        "storage": storage_ok,
        "version": "1.0.0"
    }
