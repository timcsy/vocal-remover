"""
Tests for JobManager service
"""
import pytest
from datetime import datetime

from app.models.job import Job, JobStatus, SourceType
from app.services.job_manager import JobManager


class TestJobManager:
    """JobManager 測試"""

    @pytest.fixture
    def job_manager(self):
        """建立新的 JobManager 實例"""
        return JobManager()

    @pytest.fixture
    def sample_job(self) -> Job:
        """建立範例任務"""
        return Job(
            source_type=SourceType.YOUTUBE,
            source_url="https://www.youtube.com/watch?v=test",
            source_title="Test Song",
            client_ip="127.0.0.1"
        )

    @pytest.fixture
    def completed_job(self) -> Job:
        """建立已完成的任務"""
        job = Job(
            source_type=SourceType.UPLOAD,
            source_title="Completed Song",
            client_ip="127.0.0.1"
        )
        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.utcnow()
        return job

    def test_create_job(self, job_manager: JobManager, sample_job: Job):
        """測試建立任務"""
        created = job_manager.create_job(sample_job)
        assert created.id == sample_job.id
        assert created.source_type == SourceType.YOUTUBE

    def test_get_job(self, job_manager: JobManager, sample_job: Job):
        """測試取得任務"""
        job_manager.create_job(sample_job)
        retrieved = job_manager.get_job(sample_job.id)
        assert retrieved is not None
        assert retrieved.id == sample_job.id

    def test_get_job_not_found(self, job_manager: JobManager):
        """測試取得不存在的任務"""
        result = job_manager.get_job("non-existent-id")
        assert result is None

    def test_delete_job(self, job_manager: JobManager, sample_job: Job):
        """測試刪除任務"""
        job_manager.create_job(sample_job)
        result = job_manager.delete_job(sample_job.id)
        assert result is True
        assert job_manager.get_job(sample_job.id) is None

    def test_delete_job_not_found(self, job_manager: JobManager):
        """測試刪除不存在的任務"""
        result = job_manager.delete_job("non-existent-id")
        assert result is False

    def test_get_all_jobs_empty(self, job_manager: JobManager):
        """測試取得空任務列表"""
        completed, processing = job_manager.get_all_jobs()
        assert completed == []
        assert processing == []

    def test_get_all_jobs_with_completed(self, job_manager: JobManager, completed_job: Job):
        """測試取得已完成任務列表"""
        job_manager.create_job(completed_job)
        completed, processing = job_manager.get_all_jobs()
        assert len(completed) == 1
        assert completed[0].id == completed_job.id
        assert len(processing) == 0

    def test_get_all_jobs_with_processing(self, job_manager: JobManager, sample_job: Job):
        """測試取得處理中任務列表"""
        sample_job.status = JobStatus.SEPARATING
        sample_job.progress = 50
        job_manager.create_job(sample_job)
        completed, processing = job_manager.get_all_jobs()
        assert len(completed) == 0
        assert len(processing) == 1
        assert processing[0].id == sample_job.id

    def test_get_all_jobs_mixed(self, job_manager: JobManager, sample_job: Job, completed_job: Job):
        """測試取得混合任務列表"""
        sample_job.status = JobStatus.DOWNLOADING
        job_manager.create_job(sample_job)
        job_manager.create_job(completed_job)

        completed, processing = job_manager.get_all_jobs()
        assert len(completed) == 1
        assert len(processing) == 1

    def test_update_progress(self, job_manager: JobManager, sample_job: Job):
        """測試更新進度"""
        job_manager.create_job(sample_job)
        job_manager.update_progress(sample_job.id, 50, "處理中", JobStatus.SEPARATING)

        job = job_manager.get_job(sample_job.id)
        assert job.progress == 50
        assert job.current_stage == "處理中"
        assert job.status == JobStatus.SEPARATING

    def test_complete_job(self, job_manager: JobManager, sample_job: Job):
        """測試完成任務"""
        job_manager.create_job(sample_job)
        job_manager.complete_job(sample_job.id, "/path/to/result.mp4")

        job = job_manager.get_job(sample_job.id)
        assert job.status == JobStatus.COMPLETED
        assert job.progress == 100
        assert job.result_key == "/path/to/result.mp4"

    def test_fail_job(self, job_manager: JobManager, sample_job: Job):
        """測試任務失敗"""
        job_manager.create_job(sample_job)
        job_manager.fail_job(sample_job.id, "處理失敗")

        job = job_manager.get_job(sample_job.id)
        assert job.status == JobStatus.FAILED
        assert job.error_message == "處理失敗"
