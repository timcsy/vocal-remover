"""
FFmpeg API Endpoints
Feature: 005-frontend-processing / User Story 4

提供 FFmpeg 音訊提取和影音合併代理功能
"""
import os
import logging
import tempfile
import subprocess
from typing import Literal

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import Response

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ffmpeg", tags=["ffmpeg"])


def extract_audio_ffmpeg(video_data: bytes) -> tuple[bytes, float]:
    """
    使用 FFmpeg 從影片提取 WAV 音訊

    Args:
        video_data: 影片檔案資料

    Returns:
        (WAV 音訊資料, 時長秒數)
    """
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as video_tmp:
        video_tmp.write(video_data)
        video_path = video_tmp.name

    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as wav_tmp:
        wav_path = wav_tmp.name

    try:
        # 使用 FFmpeg 提取音訊
        cmd = [
            'ffmpeg', '-y',
            '-i', video_path,
            '-vn',
            '-acodec', 'pcm_s16le',
            '-ar', '44100',
            '-ac', '2',
            wav_path
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=300
        )

        if result.returncode != 0:
            error_msg = result.stderr.decode()
            logger.error(f"FFmpeg error: {error_msg}")
            raise ValueError(f"音訊提取失敗: {error_msg[:200]}")

        # 取得時長
        duration = get_video_duration(video_path)

        with open(wav_path, 'rb') as f:
            return f.read(), duration
    finally:
        for path in [video_path, wav_path]:
            if os.path.exists(path):
                os.remove(path)


def merge_video_audio_ffmpeg(
    video_data: bytes,
    audio_data: bytes,
    output_format: Literal['mp4', 'm4a']
) -> bytes:
    """
    使用 FFmpeg 合併影片與音訊

    Args:
        video_data: 影片檔案資料
        audio_data: WAV 音訊資料
        output_format: 輸出格式 ('mp4' 或 'm4a')

    Returns:
        合併後的檔案資料
    """
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as video_tmp:
        video_tmp.write(video_data)
        video_path = video_tmp.name

    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as audio_tmp:
        audio_tmp.write(audio_data)
        audio_path = audio_tmp.name

    with tempfile.NamedTemporaryFile(suffix=f'.{output_format}', delete=False) as output_tmp:
        output_path = output_tmp.name

    try:
        if output_format == 'mp4':
            # 合併影片與音訊
            cmd = [
                'ffmpeg', '-y',
                '-i', video_path,
                '-i', audio_path,
                '-c:v', 'copy',
                '-c:a', 'aac',
                '-b:a', '192k',
                '-map', '0:v:0',
                '-map', '1:a:0',
                '-shortest',
                output_path
            ]
        else:
            # 僅編碼音訊為 M4A
            cmd = [
                'ffmpeg', '-y',
                '-i', audio_path,
                '-c:a', 'aac',
                '-b:a', '192k',
                output_path
            ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=600
        )

        if result.returncode != 0:
            error_msg = result.stderr.decode()
            logger.error(f"FFmpeg merge error: {error_msg}")
            raise ValueError(f"合併失敗: {error_msg[:200]}")

        with open(output_path, 'rb') as f:
            return f.read()
    finally:
        for path in [video_path, audio_path, output_path]:
            if os.path.exists(path):
                os.remove(path)


def get_video_duration(video_path: str) -> float:
    """取得影片時長"""
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        video_path
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=30
        )
        if result.returncode == 0:
            return float(result.stdout.decode().strip())
    except Exception as e:
        logger.warning(f"無法取得影片時長: {e}")

    return 0.0


@router.post("/extract-audio")
async def extract_audio(video: UploadFile = File(..., description="影片檔案")):
    """
    從影片提取 WAV 音訊

    Args:
        video: 上傳的影片檔案

    Returns:
        44.1kHz 立體聲 16-bit PCM WAV 音訊
    """
    try:
        video_data = await video.read()
        wav_data, duration = extract_audio_ffmpeg(video_data)

        return Response(
            content=wav_data,
            media_type="audio/wav",
            headers={
                "X-Video-Duration": str(duration),
            }
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={"code": "EXTRACT_ERROR", "message": str(e)}
        )
    except Exception as e:
        logger.error(f"音訊提取失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail={"code": "EXTRACT_ERROR", "message": f"音訊提取失敗: {str(e)}"}
        )


@router.post("/merge")
async def merge(
    video: UploadFile = File(..., description="影片檔案"),
    audio: UploadFile = File(..., description="WAV 音訊檔案"),
    format: Literal['mp4', 'm4a'] = Form('mp4', description="輸出格式")
):
    """
    合併影片與音訊

    Args:
        video: 原始影片檔案
        audio: 混音後的 WAV 音訊
        format: 輸出格式 ('mp4' 或 'm4a')

    Returns:
        合併後的 MP4 或 M4A 檔案
    """
    if format not in ('mp4', 'm4a'):
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_FORMAT", "message": f"不支援的格式: {format}"}
        )

    try:
        video_data = await video.read()
        audio_data = await audio.read()

        output_data = merge_video_audio_ffmpeg(video_data, audio_data, format)

        media_type = 'video/mp4' if format == 'mp4' else 'audio/mp4'
        return Response(
            content=output_data,
            media_type=media_type,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={"code": "MERGE_ERROR", "message": str(e)}
        )
    except Exception as e:
        logger.error(f"合併失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail={"code": "MERGE_ERROR", "message": f"合併失敗: {str(e)}"}
        )
