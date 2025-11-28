import os
import re
from datetime import datetime
from typing import Optional
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Header
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel

from app.core.config import get_settings
from app.models.job import Job, JobStatus, SourceType, MixSettings, OutputFormat
from app.services.youtube import get_youtube_downloader
from app.services.local_storage import get_local_storage
from app.services.job_manager import get_job_manager
from app.services.processor import process_job_async
from app.services.mixer import get_mixer
from app.services.exporter import get_exporter
from app.services.importer import get_importer


router = APIRouter()
settings = get_settings()


class CreateJobRequest(BaseModel):
    """建立任務請求"""
    source_type: SourceType
    source_url: Optional[str] = None


class JobResponse(BaseModel):
    """任務回應"""
    id: str
    source_type: SourceType
    status: JobStatus
    progress: int
    current_stage: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ResultResponse(BaseModel):
    """結果回應"""
    original_duration: Optional[int] = None
    output_size: Optional[int] = None
    download_url: Optional[str] = None


class JobWithResultResponse(JobResponse):
    """包含結果的任務回應"""
    result: Optional[ResultResponse] = None


class ErrorResponse(BaseModel):
    """錯誤回應"""
    code: str
    message: str


# ========== Video Mixer API 新增 ==========

class CompletedJobResponse(BaseModel):
    """已完成任務回應"""
    id: str
    source_title: Optional[str]
    source_type: SourceType
    status: str
    original_duration: Optional[int] = None
    created_at: datetime


class ProcessingJobResponse(BaseModel):
    """處理中任務回應"""
    id: str
    source_title: Optional[str] = None
    status: str
    progress: int
    current_stage: Optional[str] = None


class JobsListResponse(BaseModel):
    """任務列表回應"""
    jobs: list[CompletedJobResponse]
    processing: list[ProcessingJobResponse]


class ExportRequest(BaseModel):
    """匯出請求"""
    job_ids: list[str]


class ExportResponse(BaseModel):
    """匯出回應"""
    download_url: str


class ImportConflict(BaseModel):
    """匯入衝突"""
    conflict_id: str
    source_title: str
    existing_job_id: str


class ImportedJob(BaseModel):
    """匯入的歌曲"""
    id: str
    source_title: Optional[str]


class ImportResponse(BaseModel):
    """匯入回應"""
    imported: list[ImportedJob]
    conflicts: list[ImportConflict]
    errors: list[str]


class ResolveConflictRequest(BaseModel):
    """解決衝突請求"""
    action: str  # 'overwrite' or 'rename'
    new_title: Optional[str] = None


class ResolveConflictResponse(BaseModel):
    """解決衝突回應"""
    job: Optional[ImportedJob] = None
    error: Optional[str] = None


def get_client_ip(request: Request) -> str:
    """取得客戶端 IP"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


ALLOWED_EXTENSIONS = {'.mp4', '.mov', '.avi', '.mkv', '.webm'}


def validate_file_extension(filename: str) -> bool:
    """驗證檔案副檔名"""
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_EXTENSIONS


# ========== Video Mixer: 任務列表 API ==========

@router.get("/jobs", response_model=JobsListResponse)
async def get_jobs():
    """
    取得所有任務列表

    返回已完成和處理中的任務列表，用於左側抽屜和任務佇列顯示
    """
    job_manager = get_job_manager()
    completed, processing = job_manager.get_all_jobs()

    return JobsListResponse(
        jobs=[
            CompletedJobResponse(
                id=job.id,
                source_title=job.source_title,
                source_type=job.source_type,
                status=job.status.value,
                original_duration=job.original_duration,
                created_at=job.created_at
            )
            for job in completed
        ],
        processing=[
            ProcessingJobResponse(
                id=job.id,
                source_title=job.source_title,
                status=job.status.value,
                progress=job.progress,
                current_stage=job.current_stage
            )
            for job in processing
        ]
    )


@router.post("/jobs", response_model=JobResponse, status_code=201)
async def create_job(request: Request, body: CreateJobRequest):
    """
    建立處理任務（JSON 格式）

    支援 YouTube 網址提交
    """
    client_ip = get_client_ip(request)
    job_manager = get_job_manager()

    # 檢查並發限制
    if not job_manager.can_accept_job():
        raise HTTPException(
            status_code=503,
            detail={"code": "SERVICE_BUSY", "message": "伺服器忙碌中，請稍後再試"}
        )

    # YouTube 任務
    if body.source_type != SourceType.YOUTUBE:
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_SOURCE_TYPE", "message": "JSON 格式僅支援 YouTube 網址"}
        )

    if not body.source_url:
        raise HTTPException(
            status_code=400,
            detail={"code": "MISSING_URL", "message": "請提供 YouTube 網址"}
        )

    # 驗證 YouTube 網址
    downloader = get_youtube_downloader()
    if not downloader.is_valid_url(body.source_url):
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_URL", "message": "無效的 YouTube 網址格式"}
        )

    # 建立任務
    job = Job(
        source_type=body.source_type,
        source_url=body.source_url,
        client_ip=client_ip
    )

    # 儲存任務狀態
    job_manager.create_job(job)

    # 啟動背景處理
    process_job_async(job)

    return JobResponse(
        id=job.id,
        source_type=job.source_type,
        status=job.status,
        progress=job.progress,
        current_stage=job.current_stage,
        error_message=job.error_message,
        created_at=job.created_at,
        updated_at=job.updated_at
    )


@router.post("/jobs/upload", response_model=JobResponse, status_code=201)
async def create_upload_job(
    request: Request,
    file: UploadFile = File(...)
):
    """
    建立上傳任務（multipart/form-data 格式）

    支援本地影片檔案上傳
    """
    client_ip = get_client_ip(request)
    job_manager = get_job_manager()
    storage = get_local_storage()

    # 檢查並發限制
    if not job_manager.can_accept_job():
        raise HTTPException(
            status_code=503,
            detail={"code": "SERVICE_BUSY", "message": "伺服器忙碌中，請稍後再試"}
        )

    # 驗證檔案
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail={"code": "MISSING_FILE", "message": "請選擇檔案"}
        )

    if not validate_file_extension(file.filename):
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_FILE_TYPE", "message": f"不支援的檔案格式，支援: {', '.join(ALLOWED_EXTENSIONS)}"}
        )

    # 建立任務
    job = Job(
        source_type=SourceType.UPLOAD,
        source_filename=file.filename,
        client_ip=client_ip
    )

    # 讀取檔案內容
    content = await file.read()

    # 儲存上傳檔案到本地
    ext = os.path.splitext(file.filename)[1]
    upload_path = storage.save_upload(job.id, f"input{ext}", content)

    # 記錄上傳路徑
    job.source_url = upload_path
    job.source_title = os.path.splitext(file.filename)[0]

    # 儲存任務狀態
    job_manager.create_job(job)

    # 啟動背景處理
    process_job_async(job)

    return JobResponse(
        id=job.id,
        source_type=job.source_type,
        status=job.status,
        progress=job.progress,
        current_stage=job.current_stage,
        error_message=job.error_message,
        created_at=job.created_at,
        updated_at=job.updated_at
    )


@router.get("/jobs/{job_id}", response_model=JobWithResultResponse)
async def get_job(job_id: str):
    """
    查詢任務狀態

    取得指定任務的處理狀態和進度
    """
    job_manager = get_job_manager()
    job = job_manager.get_job(job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail={"code": "JOB_NOT_FOUND", "message": "任務不存在或已過期"}
        )

    result_response = None
    if job.status == JobStatus.COMPLETED and job.result_key:
        # 取得檔案大小
        if os.path.exists(job.result_key):
            file_size = os.path.getsize(job.result_key)
            result_response = ResultResponse(
                original_duration=job.original_duration,
                output_size=file_size,
                download_url=f"/api/v1/jobs/{job_id}/download"
            )

    return JobWithResultResponse(
        id=job.id,
        source_type=job.source_type,
        status=job.status,
        progress=job.progress,
        current_stage=job.current_stage,
        error_message=job.error_message,
        created_at=job.created_at,
        updated_at=job.updated_at,
        result=result_response
    )


@router.delete("/jobs/{job_id}", status_code=204)
async def delete_job(job_id: str):
    """
    刪除任務

    刪除指定任務及其相關檔案
    """
    job_manager = get_job_manager()
    storage = get_local_storage()

    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=404,
            detail={"code": "JOB_NOT_FOUND", "message": "任務不存在"}
        )

    # 刪除相關檔案
    storage.delete_job_files(job_id)

    # 從記憶體中刪除任務
    job_manager.delete_job(job_id)

    return None


@router.get("/jobs/{job_id}/download")
async def download_result(job_id: str):
    """
    下載處理結果

    直接串流檔案給用戶下載
    """
    job_manager = get_job_manager()
    job = job_manager.get_job(job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail={"code": "JOB_NOT_FOUND", "message": "任務不存在或已過期"}
        )

    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail={"code": "JOB_NOT_COMPLETED", "message": "任務尚未完成"}
        )

    # 優先使用原始影片（含人聲），否則使用 result_key
    file_path = None
    if job.original_video_path and os.path.exists(job.original_video_path):
        file_path = job.original_video_path
    elif job.result_key and os.path.exists(job.result_key):
        file_path = job.result_key

    if not file_path:
        raise HTTPException(
            status_code=400,
            detail={"code": "NO_RESULT", "message": "找不到結果檔案"}
        )

    # 設定檔案名稱 - 使用原始標題
    if job.source_title:
        # 清理檔名中的特殊字元
        safe_title = re.sub(r'[<>:"/\\|?*]', '_', job.source_title)
        safe_title = safe_title.strip()[:100]  # 限制長度
        filename = f"{safe_title}.mp4"
    else:
        filename = f"video_{job_id}.mp4"

    # 使用 RFC 5987 編碼處理非 ASCII 字元
    filename_encoded = quote(filename, safe='')

    return FileResponse(
        path=file_path,
        media_type="video/mp4",
        filename=filename,
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{filename_encoded}"
        }
    )


@router.get("/jobs/{job_id}/stream")
async def stream_result(job_id: str, range: Optional[str] = Header(None)):
    """
    串流播放處理結果（支援 Range 請求）

    用於影片預覽播放，支援跳轉播放位置
    """
    job_manager = get_job_manager()
    job = job_manager.get_job(job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail={"code": "JOB_NOT_FOUND", "message": "任務不存在或已過期"}
        )

    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail={"code": "JOB_NOT_COMPLETED", "message": "任務尚未完成"}
        )

    # 優先使用原始影片（含人聲），否則使用 result_key
    file_path = None
    if job.original_video_path and os.path.exists(job.original_video_path):
        file_path = job.original_video_path
    elif job.result_key and os.path.exists(job.result_key):
        file_path = job.result_key

    if not file_path:
        raise HTTPException(
            status_code=400,
            detail={"code": "NO_RESULT", "message": "找不到結果檔案"}
        )
    file_size = os.path.getsize(file_path)

    # 解析 Range header
    start = 0
    end = file_size - 1

    if range:
        # 格式: bytes=start-end
        range_match = re.match(r'bytes=(\d+)-(\d*)', range)
        if range_match:
            start = int(range_match.group(1))
            if range_match.group(2):
                end = int(range_match.group(2))

    # 限制範圍
    if start >= file_size:
        raise HTTPException(status_code=416, detail="Range not satisfiable")

    end = min(end, file_size - 1)
    content_length = end - start + 1

    # 從本地檔案取得指定範圍的資料
    def range_file_iterator():
        with open(file_path, 'rb') as f:
            f.seek(start)
            remaining = content_length
            chunk_size = 64 * 1024  # 64KB chunks
            while remaining > 0:
                read_size = min(chunk_size, remaining)
                data = f.read(read_size)
                if not data:
                    break
                remaining -= len(data)
                yield data

    headers = {
        "Content-Range": f"bytes {start}-{end}/{file_size}",
        "Accept-Ranges": "bytes",
        "Content-Length": str(content_length),
        "Content-Type": "video/mp4",
    }

    # 如果有 Range 請求，返回 206 Partial Content
    status_code = 206 if range else 200

    return StreamingResponse(
        range_file_iterator(),
        status_code=status_code,
        media_type="video/mp4",
        headers=headers
    )


# ========== 進階音軌控制 API ==========

class TracksInfoResponse(BaseModel):
    """音軌資訊回應"""
    tracks: list[str]
    sample_rate: int
    duration: float


@router.get("/jobs/{job_id}/tracks", response_model=TracksInfoResponse)
async def get_tracks_info(job_id: str):
    """
    取得可用音軌列表

    返回分離後的音軌資訊
    """
    job_manager = get_job_manager()
    job = job_manager.get_job(job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail={"code": "JOB_NOT_FOUND", "message": "任務不存在或已過期"}
        )

    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail={"code": "JOB_NOT_COMPLETED", "message": "任務尚未完成"}
        )

    if not job.track_paths:
        raise HTTPException(
            status_code=400,
            detail={"code": "NO_TRACKS", "message": "音軌資料不存在"}
        )

    # 取得可用的音軌列表
    available_tracks = []
    for track_name in ["drums", "bass", "other", "vocals"]:
        track_path = getattr(job.track_paths, track_name, None)
        if track_path and os.path.exists(track_path):
            available_tracks.append(track_name)

    # 取得音頻時長
    import soundfile as sf
    duration = 0.0
    sample_rate = job.sample_rate or 44100

    first_track_path = getattr(job.track_paths, available_tracks[0], None) if available_tracks else None
    if first_track_path and os.path.exists(first_track_path):
        info = sf.info(first_track_path)
        duration = info.duration
        sample_rate = info.samplerate

    return TracksInfoResponse(
        tracks=available_tracks,
        sample_rate=sample_rate,
        duration=duration
    )


@router.api_route("/jobs/{job_id}/tracks/{track_name}", methods=["GET", "HEAD"])
async def stream_track(
    request: Request,
    job_id: str,
    track_name: str,
    range: Optional[str] = Header(None)
):
    """
    串流單一音軌

    支援 HTTP Range 請求和 HEAD 請求（供瀏覽器預載檢查）
    """
    if track_name not in ["drums", "bass", "other", "vocals"]:
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_TRACK", "message": "無效的音軌名稱"}
        )

    job_manager = get_job_manager()
    job = job_manager.get_job(job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail={"code": "JOB_NOT_FOUND", "message": "任務不存在或已過期"}
        )

    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail={"code": "JOB_NOT_COMPLETED", "message": "任務尚未完成"}
        )

    if not job.track_paths:
        raise HTTPException(
            status_code=400,
            detail={"code": "NO_TRACKS", "message": "音軌資料不存在"}
        )

    track_path = getattr(job.track_paths, track_name, None)
    if not track_path or not os.path.exists(track_path):
        raise HTTPException(
            status_code=404,
            detail={"code": "TRACK_NOT_FOUND", "message": f"找不到 {track_name} 音軌"}
        )

    file_size = os.path.getsize(track_path)

    # 解析 Range header
    start = 0
    end = file_size - 1

    if range:
        range_match = re.match(r'bytes=(\d+)-(\d*)', range)
        if range_match:
            start = int(range_match.group(1))
            if range_match.group(2):
                end = int(range_match.group(2))

    if start >= file_size:
        raise HTTPException(status_code=416, detail="Range not satisfiable")

    end = min(end, file_size - 1)
    content_length = end - start + 1

    headers = {
        "Content-Range": f"bytes {start}-{end}/{file_size}",
        "Accept-Ranges": "bytes",
        "Content-Length": str(content_length),
        "Content-Type": "audio/wav",
    }

    # HEAD 請求只回傳 headers，不回傳 body
    if request.method == "HEAD":
        from fastapi.responses import Response
        return Response(
            status_code=200,
            headers=headers,
            media_type="audio/wav",
        )

    def range_file_iterator():
        with open(track_path, 'rb') as f:
            f.seek(start)
            remaining = content_length
            chunk_size = 64 * 1024
            while remaining > 0:
                read_size = min(chunk_size, remaining)
                data = f.read(read_size)
                if not data:
                    break
                remaining -= len(data)
                yield data

    status_code = 206 if range else 200

    return StreamingResponse(
        range_file_iterator(),
        status_code=status_code,
        media_type="audio/wav",
        headers=headers
    )


# ========== 自訂混音下載 API ==========

class CreateMixRequest(BaseModel):
    """建立混音請求"""
    drums_volume: float = 1.0
    bass_volume: float = 1.0
    other_volume: float = 1.0
    vocals_volume: float = 0.0
    pitch_shift: int = 0
    output_format: OutputFormat = OutputFormat.MP4


class MixStatusResponse(BaseModel):
    """混音狀態回應"""
    mix_id: str
    status: str  # processing, completed, failed
    progress: int
    download_url: Optional[str] = None
    cached: bool = False
    error_message: Optional[str] = None


# 混音任務狀態存儲（簡單的記憶體快取）
_mix_tasks: dict = {}


@router.post("/jobs/{job_id}/mix", response_model=MixStatusResponse, status_code=202)
async def create_mix(job_id: str, body: CreateMixRequest):
    """
    建立自訂混音任務

    根據使用者設定的音量和音調進行混音
    """
    job_manager = get_job_manager()
    storage = get_local_storage()
    mixer = get_mixer()

    job = job_manager.get_job(job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail={"code": "JOB_NOT_FOUND", "message": "任務不存在或已過期"}
        )

    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail={"code": "JOB_NOT_COMPLETED", "message": "任務尚未完成"}
        )

    if not job.track_paths:
        raise HTTPException(
            status_code=400,
            detail={"code": "NO_TRACKS", "message": "音軌資料不存在"}
        )

    # 建立混音設定
    settings = MixSettings(
        drums_volume=body.drums_volume,
        bass_volume=body.bass_volume,
        other_volume=body.other_volume,
        vocals_volume=body.vocals_volume,
        pitch_shift=body.pitch_shift,
        output_format=body.output_format,
    )

    # 計算快取鍵
    mix_id = mixer.get_cache_key(job_id, settings)

    # 檢查快取
    ext = mixer.get_output_extension(body.output_format)
    output_path = storage.get_result_path(job_id, f"mix_{mix_id}.{ext}")

    if os.path.exists(str(output_path)):
        return MixStatusResponse(
            mix_id=mix_id,
            status="completed",
            progress=100,
            download_url=f"/api/v1/jobs/{job_id}/mix/{mix_id}/download",
            cached=True,
        )

    # 檢查是否已有相同任務在處理中
    task_key = f"{job_id}:{mix_id}"
    if task_key in _mix_tasks and _mix_tasks[task_key]["status"] == "processing":
        return MixStatusResponse(
            mix_id=mix_id,
            status="processing",
            progress=_mix_tasks[task_key].get("progress", 0),
        )

    # 建立新任務
    _mix_tasks[task_key] = {
        "status": "processing",
        "progress": 0,
        "job_id": job_id,
        "settings": settings,
        "output_path": str(output_path),
    }

    # 在背景執行混音
    import threading

    def run_mix():
        try:
            track_paths = {
                "drums": job.track_paths.drums,
                "bass": job.track_paths.bass,
                "other": job.track_paths.other,
                "vocals": job.track_paths.vocals,
            }

            # 取得原始影片路徑（用於 MP4 格式）
            video_path = None
            if body.output_format == OutputFormat.MP4 and job.result_key:
                video_path = job.result_key

            def progress_callback(progress, stage):
                _mix_tasks[task_key]["progress"] = progress

            mixer.mix_tracks(
                track_paths=track_paths,
                settings=settings,
                output_path=str(output_path),
                video_path=video_path,
                progress_callback=progress_callback,
            )

            _mix_tasks[task_key]["status"] = "completed"
            _mix_tasks[task_key]["progress"] = 100

        except Exception as e:
            _mix_tasks[task_key]["status"] = "failed"
            _mix_tasks[task_key]["error"] = str(e)

    thread = threading.Thread(target=run_mix, daemon=True)
    thread.start()

    return MixStatusResponse(
        mix_id=mix_id,
        status="processing",
        progress=0,
    )


@router.get("/jobs/{job_id}/mix/{mix_id}", response_model=MixStatusResponse)
async def get_mix_status(job_id: str, mix_id: str):
    """
    查詢混音任務狀態
    """
    task_key = f"{job_id}:{mix_id}"

    # 先檢查檔案是否存在（可能是快取）
    storage = get_local_storage()
    for ext in ["mp4", "mp3", "m4a", "wav"]:
        output_path = storage.get_result_path(job_id, f"mix_{mix_id}.{ext}")
        if os.path.exists(str(output_path)):
            return MixStatusResponse(
                mix_id=mix_id,
                status="completed",
                progress=100,
                download_url=f"/api/v1/jobs/{job_id}/mix/{mix_id}/download",
                cached=True,
            )

    # 檢查任務狀態
    if task_key not in _mix_tasks:
        raise HTTPException(
            status_code=404,
            detail={"code": "MIX_NOT_FOUND", "message": "混音任務不存在"}
        )

    task = _mix_tasks[task_key]

    if task["status"] == "completed":
        return MixStatusResponse(
            mix_id=mix_id,
            status="completed",
            progress=100,
            download_url=f"/api/v1/jobs/{job_id}/mix/{mix_id}/download",
        )
    elif task["status"] == "failed":
        return MixStatusResponse(
            mix_id=mix_id,
            status="failed",
            progress=task.get("progress", 0),
            error_message=task.get("error"),
        )
    else:
        return MixStatusResponse(
            mix_id=mix_id,
            status="processing",
            progress=task.get("progress", 0),
        )


@router.get("/jobs/{job_id}/mix/{mix_id}/download")
async def download_mix(job_id: str, mix_id: str):
    """
    下載混音結果
    """
    job_manager = get_job_manager()
    storage = get_local_storage()

    job = job_manager.get_job(job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail={"code": "JOB_NOT_FOUND", "message": "任務不存在或已過期"}
        )

    # 找到混音檔案
    output_path = None
    file_ext = None
    for ext in ["mp4", "mp3", "m4a", "wav"]:
        path = storage.get_result_path(job_id, f"mix_{mix_id}.{ext}")
        if os.path.exists(str(path)):
            output_path = str(path)
            file_ext = ext
            break

    if not output_path:
        raise HTTPException(
            status_code=404,
            detail={"code": "MIX_NOT_FOUND", "message": "混音檔案不存在"}
        )

    # 設定檔案名稱
    if job.source_title:
        safe_title = re.sub(r'[<>:"/\\|?*]', '_', job.source_title)
        safe_title = safe_title.strip()[:100]
        filename = f"{safe_title}_自訂混音.{file_ext}"
    else:
        filename = f"custom_mix_{job_id}.{file_ext}"

    filename_encoded = quote(filename, safe='')

    # 設定 MIME 類型
    mime_types = {
        "mp4": "video/mp4",
        "mp3": "audio/mpeg",
        "m4a": "audio/mp4",
        "wav": "audio/wav",
    }
    media_type = mime_types.get(file_ext, "application/octet-stream")

    return FileResponse(
        path=output_path,
        media_type=media_type,
        filename=filename,
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{filename_encoded}"
        }
    )


# ========== Video Mixer: 匯出 API ==========

@router.post("/jobs/export", response_model=ExportResponse)
async def export_jobs(body: ExportRequest):
    """
    匯出歌曲

    將選定的歌曲打包為 ZIP 檔案下載
    """
    if not body.job_ids:
        raise HTTPException(
            status_code=400,
            detail={"code": "NO_JOBS_SELECTED", "message": "請選擇要匯出的歌曲"}
        )

    job_manager = get_job_manager()
    exporter = get_exporter()

    # 取得所有選取的任務
    jobs = []
    for job_id in body.job_ids:
        job = job_manager.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=404,
                detail={"code": "JOB_NOT_FOUND", "message": f"任務 {job_id} 不存在"}
            )
        if job.status != JobStatus.COMPLETED:
            raise HTTPException(
                status_code=400,
                detail={"code": "JOB_NOT_COMPLETED", "message": f"任務 {job_id} 尚未完成"}
            )
        jobs.append(job)

    # 建立 ZIP
    if len(jobs) == 1:
        zip_path = exporter.create_single_zip(jobs[0])
    else:
        zip_path = exporter.create_multi_zip(jobs)

    if not zip_path:
        raise HTTPException(
            status_code=500,
            detail={"code": "EXPORT_FAILED", "message": "匯出失敗"}
        )

    # 從路徑取得 export_id
    from pathlib import Path
    export_id = Path(zip_path).parent.name

    return ExportResponse(
        download_url=f"/api/v1/jobs/export/download/{export_id}"
    )


@router.get("/jobs/export/download/{export_id}")
async def download_export(export_id: str):
    """
    下載匯出的 ZIP

    下載已打包完成的 ZIP 檔案
    """
    exporter = get_exporter()
    zip_path = exporter.get_export_path(export_id)

    if not zip_path or not os.path.exists(zip_path):
        raise HTTPException(
            status_code=404,
            detail={"code": "EXPORT_NOT_FOUND", "message": "匯出檔案不存在"}
        )

    filename = os.path.basename(zip_path)
    filename_encoded = quote(filename, safe='')

    return FileResponse(
        path=zip_path,
        media_type="application/zip",
        filename=filename,
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{filename_encoded}"
        }
    )


# ========== Video Mixer: 匯入 API ==========

@router.post("/jobs/import", response_model=ImportResponse)
async def import_jobs(file: UploadFile = File(...)):
    """
    匯入歌曲

    從 ZIP 檔案匯入歌曲
    """
    if not file.filename or not file.filename.endswith('.zip'):
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_FILE", "message": "請選擇 ZIP 檔案"}
        )

    importer = get_importer()
    storage = get_local_storage()

    # 儲存上傳的 ZIP 檔案到暫存目錄
    content = await file.read()
    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # 執行匯入
        result = importer.import_zip(tmp_path)

        return ImportResponse(
            imported=[
                ImportedJob(id=job.id, source_title=job.source_title)
                for job in result.imported
            ],
            conflicts=[
                ImportConflict(
                    conflict_id=c['conflict_id'],
                    source_title=c['source_title'],
                    existing_job_id=c['existing_job_id']
                )
                for c in result.conflicts
            ],
            errors=result.errors
        )
    finally:
        # 清理暫存檔案
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@router.post("/jobs/import/resolve/{conflict_id}", response_model=ResolveConflictResponse)
async def resolve_import_conflict(conflict_id: str, body: ResolveConflictRequest):
    """
    解決匯入衝突

    當匯入的歌曲與現有歌曲同名時，選擇覆蓋或重新命名
    """
    if body.action not in ('overwrite', 'rename'):
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_ACTION", "message": "操作必須是 'overwrite' 或 'rename'"}
        )

    if body.action == 'rename' and not body.new_title:
        raise HTTPException(
            status_code=400,
            detail={"code": "MISSING_TITLE", "message": "重新命名需要提供新名稱"}
        )

    importer = get_importer()
    job, error = importer.resolve_conflict(conflict_id, body.action, body.new_title)

    if error:
        return ResolveConflictResponse(error=error)

    return ResolveConflictResponse(
        job=ImportedJob(id=job.id, source_title=job.source_title) if job else None
    )
