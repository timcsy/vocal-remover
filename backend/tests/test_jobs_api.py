"""
Tests for Jobs API endpoints
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.job import Job, JobStatus, SourceType
from app.services.job_manager import get_job_manager


@pytest.fixture
def client():
    """建立測試客戶端"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_jobs():
    """每個測試前清空任務列表"""
    job_manager = get_job_manager()
    job_manager._jobs.clear()
    yield
    job_manager._jobs.clear()


class TestGetJobs:
    """GET /jobs 端點測試"""

    def test_get_jobs_empty(self, client: TestClient):
        """測試取得空任務列表"""
        response = client.get("/api/v1/jobs")
        assert response.status_code == 200
        data = response.json()
        assert "jobs" in data
        assert "processing" in data
        assert data["jobs"] == []
        assert data["processing"] == []

    def test_get_jobs_with_completed(self, client: TestClient):
        """測試取得已完成任務"""
        job_manager = get_job_manager()
        job = Job(
            source_type=SourceType.YOUTUBE,
            source_title="Test Song",
            client_ip="127.0.0.1"
        )
        job.status = JobStatus.COMPLETED
        job_manager.create_job(job)

        response = client.get("/api/v1/jobs")
        assert response.status_code == 200
        data = response.json()
        assert len(data["jobs"]) == 1
        assert data["jobs"][0]["id"] == job.id
        assert data["jobs"][0]["source_title"] == "Test Song"
        assert data["jobs"][0]["status"] == "completed"

    def test_get_jobs_with_processing(self, client: TestClient):
        """測試取得處理中任務"""
        job_manager = get_job_manager()
        job = Job(
            source_type=SourceType.UPLOAD,
            source_title="Processing Song",
            client_ip="127.0.0.1"
        )
        job.status = JobStatus.SEPARATING
        job.progress = 45
        job_manager.create_job(job)

        response = client.get("/api/v1/jobs")
        assert response.status_code == 200
        data = response.json()
        assert len(data["processing"]) == 1
        assert data["processing"][0]["id"] == job.id
        assert data["processing"][0]["status"] == "separating"
        assert data["processing"][0]["progress"] == 45

    def test_get_jobs_mixed(self, client: TestClient):
        """測試取得混合任務列表"""
        job_manager = get_job_manager()

        # 已完成任務
        completed_job = Job(
            source_type=SourceType.YOUTUBE,
            source_title="Completed Song",
            client_ip="127.0.0.1"
        )
        completed_job.status = JobStatus.COMPLETED
        job_manager.create_job(completed_job)

        # 處理中任務
        processing_job = Job(
            source_type=SourceType.UPLOAD,
            source_title="Processing Song",
            client_ip="127.0.0.1"
        )
        processing_job.status = JobStatus.DOWNLOADING
        processing_job.progress = 20
        job_manager.create_job(processing_job)

        response = client.get("/api/v1/jobs")
        assert response.status_code == 200
        data = response.json()
        assert len(data["jobs"]) == 1
        assert len(data["processing"]) == 1


class TestDeleteJob:
    """DELETE /jobs/{job_id} 端點測試"""

    def test_delete_job_success(self, client: TestClient):
        """測試成功刪除任務"""
        job_manager = get_job_manager()
        job = Job(
            source_type=SourceType.YOUTUBE,
            source_title="To Delete",
            client_ip="127.0.0.1"
        )
        job.status = JobStatus.COMPLETED
        job_manager.create_job(job)

        response = client.delete(f"/api/v1/jobs/{job.id}")
        assert response.status_code == 204

        # 確認已刪除
        assert job_manager.get_job(job.id) is None

    def test_delete_job_not_found(self, client: TestClient):
        """測試刪除不存在的任務"""
        response = client.delete("/api/v1/jobs/non-existent-id")
        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["code"] == "JOB_NOT_FOUND"
