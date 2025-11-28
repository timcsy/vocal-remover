import logging
import os
import re
import tempfile
from pathlib import Path
from typing import Callable, Optional

import requests
import yt_dlp

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class YouTubeDownloader:
    """yt-dlp YouTube 下載服務，支援 cobalt.tools fallback"""

    YOUTUBE_URL_PATTERN = re.compile(
        r'^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/)[a-zA-Z0-9_-]{11}'
    )

    # Cobalt API 端點
    COBALT_API_URL = "https://api.cobalt.tools/api/json"

    def __init__(self):
        settings = get_settings()
        self.max_duration = settings.max_video_duration

    def is_valid_url(self, url: str) -> bool:
        """
        驗證是否為有效的 YouTube 網址

        Args:
            url: YouTube 網址

        Returns:
            是否有效
        """
        return bool(self.YOUTUBE_URL_PATTERN.match(url))

    def get_video_info(self, url: str) -> dict:
        """
        取得影片資訊

        Args:
            url: YouTube 網址

        Returns:
            dict: 包含 title, duration, thumbnail
        """
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                'title': info.get('title', 'Unknown'),
                'duration': info.get('duration', 0),
                'thumbnail': info.get('thumbnail', None),
                'video_id': info.get('id', None)
            }

    def download(
        self,
        url: str,
        output_dir: str,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> str:
        """
        下載 YouTube 影片（支援 fallback 機制）

        先嘗試使用 yt-dlp 直接下載，如果失敗則切換到 cobalt.tools

        Args:
            url: YouTube 網址
            output_dir: 輸出目錄
            progress_callback: 進度回調函數 (progress, stage)

        Returns:
            下載的檔案路徑

        Raises:
            ValueError: 網址無效或影片過長
            RuntimeError: 下載失敗
        """
        if not self.is_valid_url(url):
            raise ValueError("無效的 YouTube 網址")

        # 取得影片資訊檢查時長
        if progress_callback:
            progress_callback(0, "取得影片資訊中...")

        try:
            info = self.get_video_info(url)
            duration = info.get('duration', 0)

            if duration > self.max_duration:
                raise ValueError(f"影片長度 {duration} 秒超過限制 {self.max_duration} 秒")
        except Exception as e:
            logger.warning(f"無法取得影片資訊: {e}，繼續嘗試下載")

        # 先嘗試 yt-dlp
        try:
            logger.info(f"嘗試使用 yt-dlp 下載: {url}")
            return self._download_with_ytdlp(url, output_dir, progress_callback)
        except Exception as e:
            logger.warning(f"yt-dlp 下載失敗: {e}，嘗試 cobalt.tools")
            if progress_callback:
                progress_callback(5, "切換備用下載方式...")

        # Fallback 到 cobalt.tools
        try:
            logger.info(f"嘗試使用 cobalt.tools 下載: {url}")
            return self._download_with_cobalt(url, output_dir, progress_callback)
        except Exception as e:
            logger.error(f"cobalt.tools 下載也失敗: {e}")
            raise RuntimeError(f"所有下載方式都失敗: {str(e)}")

    def _download_with_ytdlp(
        self,
        url: str,
        output_dir: str,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> str:
        """使用 yt-dlp 下載影片"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        output_template = str(output_path / '%(id)s.%(ext)s')

        def progress_hook(d):
            if progress_callback:
                if d['status'] == 'downloading':
                    total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                    downloaded = d.get('downloaded_bytes', 0)
                    speed = d.get('speed', 0)

                    if total > 0:
                        percent = int((downloaded / total) * 100)
                        dl_mb = downloaded / (1024 * 1024)
                        total_mb = total / (1024 * 1024)
                        if speed:
                            speed_mb = speed / (1024 * 1024)
                            stage = f"下載中 {dl_mb:.1f}/{total_mb:.1f}MB ({speed_mb:.1f}MB/s)"
                        else:
                            stage = f"下載中 {dl_mb:.1f}/{total_mb:.1f}MB"
                        progress_callback(percent, stage)
                elif d['status'] == 'finished':
                    progress_callback(95, "下載完成，處理中...")

        ydl_opts = {
            'format': 'bestvideo[ext=mp4][vcodec^=avc]+bestaudio[ext=m4a]/bestvideo[vcodec^=avc]+bestaudio/bestvideo+bestaudio/best',
            'outtmpl': output_template,
            'quiet': False,
            'no_warnings': False,
            'progress_hooks': [progress_hook],
            'merge_output_format': 'mp4',
            'ignore_no_formats_error': False,
        }

        if progress_callback:
            progress_callback(5, "開始下載...")

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_id = info['id']

            # 方法 1: 直接從 info 取得檔案路徑
            if 'requested_downloads' in info and info['requested_downloads']:
                filepath = info['requested_downloads'][0].get('filepath')
                if filepath and os.path.exists(filepath):
                    if progress_callback:
                        progress_callback(100, "下載完成")
                    return filepath

            # 方法 2: 搜尋輸出目錄中的檔案
            for ext in ['mp4', 'mkv', 'webm', 'm4a', 'mp3']:
                filepath = output_path / f"{video_id}.{ext}"
                if filepath.exists():
                    if progress_callback:
                        progress_callback(100, "下載完成")
                    return str(filepath)

            # 方法 3: 列出目錄中所有檔案找到最新的
            files = list(output_path.glob('*.*'))
            if files:
                newest = max(files, key=lambda f: f.stat().st_mtime)
                if progress_callback:
                    progress_callback(100, "下載完成")
                return str(newest)

            raise RuntimeError(f"下載後找不到檔案，目錄: {output_path}")

    def _download_with_cobalt(
        self,
        url: str,
        output_dir: str,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> str:
        """使用 cobalt.tools API 下載影片"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        if progress_callback:
            progress_callback(5, "透過備用服務下載中...")

        # 呼叫 Cobalt API
        try:
            response = requests.post(
                self.COBALT_API_URL,
                json={
                    "url": url,
                    "vCodec": "h264",
                    "vQuality": "720",
                    "aFormat": "mp3",
                    "filenamePattern": "basic",
                },
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            raise RuntimeError(f"Cobalt API 請求失敗: {e}")

        # 檢查回應狀態
        status = data.get("status")
        if status == "error":
            error_msg = data.get("text", "未知錯誤")
            raise RuntimeError(f"Cobalt API 錯誤: {error_msg}")

        # 取得下載 URL
        download_url = data.get("url")
        if not download_url:
            # 如果是 picker 類型，取第一個
            picker = data.get("picker")
            if picker and len(picker) > 0:
                download_url = picker[0].get("url")

        if not download_url:
            raise RuntimeError(f"Cobalt API 未返回下載連結: {data}")

        # 下載檔案
        if progress_callback:
            progress_callback(10, "開始下載影片...")

        try:
            dl_response = requests.get(download_url, stream=True, timeout=300)
            dl_response.raise_for_status()

            # 產生檔案名稱
            video_id = self._extract_video_id(url)
            output_file = output_path / f"{video_id}.mp4"

            # 取得檔案大小
            total_size = int(dl_response.headers.get('content-length', 0))
            downloaded = 0

            with open(output_file, 'wb') as f:
                for chunk in dl_response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

                        if progress_callback and total_size > 0:
                            percent = int((downloaded / total_size) * 90) + 5
                            dl_mb = downloaded / (1024 * 1024)
                            total_mb = total_size / (1024 * 1024)
                            progress_callback(percent, f"下載中 {dl_mb:.1f}/{total_mb:.1f}MB")

            if progress_callback:
                progress_callback(100, "下載完成")

            return str(output_file)

        except requests.RequestException as e:
            raise RuntimeError(f"下載檔案失敗: {e}")

    def _extract_video_id(self, url: str) -> str:
        """從 URL 提取影片 ID"""
        patterns = [
            r'youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
            r'youtu\.be/([a-zA-Z0-9_-]{11})',
            r'youtube\.com/shorts/([a-zA-Z0-9_-]{11})',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return "video"


# Global instance
_downloader: Optional[YouTubeDownloader] = None


def get_youtube_downloader() -> YouTubeDownloader:
    """取得下載器實例"""
    global _downloader
    if _downloader is None:
        _downloader = YouTubeDownloader()
    return _downloader
