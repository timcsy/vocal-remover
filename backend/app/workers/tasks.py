import os
import tempfile
import shutil
from datetime import datetime
from typing import Optional

import redis
from rq import Queue, get_current_job

from app.core.config import get_settings
from app.models.job import Job, JobStatus, SourceType
from app.services.storage import get_storage_service


settings = get_settings()

# Redis connection
redis_conn = redis.from_url(settings.redis_url)

# RQ Queue
task_queue = Queue("default", connection=redis_conn)


def get_job_from_redis(job_id: str) -> Optional[Job]:
    """從 Redis 取得 Job"""
    data = redis_conn.get(f"job:{job_id}")
    if data:
        return Job.model_validate_json(data)
    return None


def save_job_to_redis(job: Job):
    """儲存 Job 到 Redis"""
    redis_conn.setex(
        f"job:{job.id}",
        settings.result_expiry_hours * 3600,
        job.model_dump_json()
    )


def update_job_progress(job_id: str, progress: int, stage: str, status: Optional[JobStatus] = None):
    """更新 Job 進度"""
    job = get_job_from_redis(job_id)
    if job:
        job.progress = progress
        job.current_stage = stage
        if status:
            job.status = status
        job.updated_at = datetime.utcnow()
        save_job_to_redis(job)


def fail_job(job_id: str, error_message: str):
    """標記 Job 失敗"""
    job = get_job_from_redis(job_id)
    if job:
        job.status = JobStatus.FAILED
        job.error_message = error_message
        job.updated_at = datetime.utcnow()
        save_job_to_redis(job)


def complete_job(job_id: str, result_key: str):
    """標記 Job 完成"""
    job = get_job_from_redis(job_id)
    if job:
        job.status = JobStatus.COMPLETED
        job.progress = 100
        job.current_stage = "完成"
        job.result_key = result_key
        job.updated_at = datetime.utcnow()
        save_job_to_redis(job)


def enqueue_job(job: Job):
    """將 Job 加入佇列"""
    save_job_to_redis(job)

    if job.source_type == SourceType.YOUTUBE:
        task_queue.enqueue(
            process_youtube_job,
            job.id,
            job_timeout=settings.job_timeout_minutes * 60
        )
    else:
        task_queue.enqueue(
            process_upload_job,
            job.id,
            job_timeout=settings.job_timeout_minutes * 60
        )


def process_youtube_job(job_id: str):
    """
    處理 YouTube 任務

    流程：下載 → 分離人聲 → 合併 → 上傳結果
    """
    # 將在 Phase 3 (US1) 中實作完整邏輯
    pass


def process_upload_job(job_id: str):
    """
    處理上傳任務

    流程：分離人聲 → 合併 → 上傳結果
    """
    # 將在 Phase 4 (US2) 中實作完整邏輯
    pass
