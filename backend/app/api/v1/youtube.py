"""
YouTube API Endpoints
Feature: 005-frontend-processing / User Story 4

提供 YouTube 影片資訊查詢和下載代理功能
"""
import os
import logging
import tempfile
import subprocess
from typing import Optional
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel

from app.services.youtube import get_youtube_downloader
from app.core.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/youtube", tags=["youtube"])
settings = get_settings()


class YouTubeDownloadRequest(BaseModel):
    """YouTube 下載請求"""
    url: str


class YouTubeInfoResponse(BaseModel):
    """YouTube 影片資訊回應"""
    title: str
    duration: int
    thumbnail: Optional[str] = None
    uploader: Optional[str] = None


def extract_audio_from_video(video_path: str) -> bytes:
    """
    使用 FFmpeg 從影片提取 WAV 音訊

    Args:
        video_path: 影片檔案路徑

    Returns:
        WAV 音訊資料
    """
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
        output_path = tmp.name

    try:
        # 使用 FFmpeg 提取音訊並轉換為 44.1kHz 立體聲 16-bit PCM WAV
        cmd = [
            'ffmpeg', '-y',
            '-i', video_path,
            '-vn',
            '-acodec', 'pcm_s16le',
            '-ar', '44100',
            '-ac', '2',
            output_path
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=300  # 5 分鐘超時
        )

        if result.returncode != 0:
            logger.error(f"FFmpeg error: {result.stderr.decode()}")
            raise RuntimeError("音訊提取失敗")

        with open(output_path, 'rb') as f:
            return f.read()
    finally:
        if os.path.exists(output_path):
            os.remove(output_path)


@router.get("/info", response_model=YouTubeInfoResponse)
async def get_video_info(url: str = Query(..., description="YouTube 影片網址")):
    """
    取得 YouTube 影片資訊

    Args:
        url: YouTube 影片網址

    Returns:
        影片標題、時長、縮圖等資訊
    """
    downloader = get_youtube_downloader()

    if not downloader.is_valid_url(url):
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_URL", "message": "無效的 YouTube 網址"}
        )

    try:
        info = downloader.get_video_info(url)
        return YouTubeInfoResponse(
            title=info.get('title', 'Unknown'),
            duration=info.get('duration', 0),
            thumbnail=info.get('thumbnail'),
            uploader=info.get('uploader'),
        )
    except Exception as e:
        logger.error(f"取得影片資訊失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail={"code": "INFO_ERROR", "message": f"無法取得影片資訊: {str(e)}"}
        )


@router.post("/download")
async def download_video(request: YouTubeDownloadRequest):
    """
    下載 YouTube 影片並提取音訊

    Args:
        request: 包含 YouTube 網址的請求

    Returns:
        WAV 音訊資料，並在 headers 中包含影片元資料
    """
    downloader = get_youtube_downloader()

    if not downloader.is_valid_url(request.url):
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_URL", "message": "無效的 YouTube 網址"}
        )

    # 檢查時長限制
    try:
        info = downloader.get_video_info(request.url)
        duration = info.get('duration', 0)
        title = info.get('title', 'Unknown')
        thumbnail = info.get('thumbnail', '')

        if duration > settings.max_video_duration:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "DURATION_EXCEEDED",
                    "message": f"影片時長 {duration} 秒超過限制 {settings.max_video_duration} 秒"
                }
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"無法取得影片資訊: {e}")
        duration = 0
        title = 'Unknown'
        thumbnail = ''

    # 下載影片
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            video_path = downloader.download(request.url, tmpdir)
            logger.info(f"影片已下載: {video_path}")

            # 提取音訊
            wav_data = extract_audio_from_video(video_path)

            # 回傳 WAV 資料，並在 headers 中包含元資料
            return Response(
                content=wav_data,
                media_type="audio/wav",
                headers={
                    "X-Video-Title": quote(title),
                    "X-Video-Duration": str(duration),
                    "X-Video-Thumbnail": thumbnail or "",
                }
            )
        except HTTPException:
            raise
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail={"code": "DOWNLOAD_ERROR", "message": str(e)}
            )
        except Exception as e:
            logger.error(f"下載失敗: {e}")
            raise HTTPException(
                status_code=500,
                detail={"code": "DOWNLOAD_ERROR", "message": f"下載失敗: {str(e)}"}
            )
