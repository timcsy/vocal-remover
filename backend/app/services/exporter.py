"""
ZIP 匯出服務

提供歌曲匯出為 ZIP 檔案的功能。
"""
import json
import os
import uuid
import zipfile
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from app.core.config import get_settings
from app.models.job import Job


class Exporter:
    """ZIP 匯出服務"""

    def __init__(self):
        settings = get_settings()
        self.exports_dir = Path(settings.results_dir) / "exports"
        self.exports_dir.mkdir(parents=True, exist_ok=True)

    def create_metadata(self, job: Job) -> dict:
        """建立匯出的 metadata.json 內容"""
        return {
            "version": "1.0",
            "source_title": job.source_title,
            "source_type": job.source_type.value,
            "source_url": job.source_url,
            "original_duration": job.original_duration,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "sample_rate": job.sample_rate or 44100,
        }

    def create_single_zip(self, job: Job) -> Optional[str]:
        """
        建立單首歌曲的 ZIP 檔案

        Returns:
            ZIP 檔案路徑，或 None（如果失敗）
        """
        if not job.track_paths:
            return None

        # 產生唯一的 export ID
        export_id = str(uuid.uuid4())
        safe_title = self._safe_filename(job.source_title or "untitled")
        zip_filename = f"{safe_title}.zip"
        zip_path = self.exports_dir / export_id / zip_filename
        zip_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                # 加入音軌
                for track_name in ["drums", "bass", "other", "vocals"]:
                    track_path = getattr(job.track_paths, track_name, None)
                    if track_path and os.path.exists(track_path):
                        zf.write(track_path, f"{track_name}.wav")

                # 加入原始影片（如果存在）
                if job.original_video_path and os.path.exists(job.original_video_path):
                    zf.write(job.original_video_path, "video.mp4")

                # 加入 metadata.json
                metadata = self.create_metadata(job)
                zf.writestr("metadata.json", json.dumps(metadata, ensure_ascii=False, indent=2))

            return str(zip_path)
        except Exception as e:
            print(f"Failed to create ZIP: {e}")
            return None

    def create_multi_zip(self, jobs: List[Job]) -> Optional[str]:
        """
        建立多首歌曲的 ZIP 檔案（巢狀 ZIP 結構）

        Returns:
            ZIP 檔案路徑，或 None（如果失敗）
        """
        if not jobs:
            return None

        # 產生唯一的 export ID
        export_id = str(uuid.uuid4())
        date_str = datetime.now().strftime("%Y%m%d")
        zip_filename = f"export_{date_str}.zip"
        zip_path = self.exports_dir / export_id / zip_filename
        zip_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as outer_zf:
                for job in jobs:
                    if not job.track_paths:
                        continue

                    safe_title = self._safe_filename(job.source_title or f"song_{job.id[:8]}")
                    inner_zip_name = f"{safe_title}.zip"

                    # 建立內層 ZIP 在記憶體中
                    from io import BytesIO
                    inner_buffer = BytesIO()

                    with zipfile.ZipFile(inner_buffer, 'w', zipfile.ZIP_DEFLATED) as inner_zf:
                        # 加入音軌
                        for track_name in ["drums", "bass", "other", "vocals"]:
                            track_path = getattr(job.track_paths, track_name, None)
                            if track_path and os.path.exists(track_path):
                                inner_zf.write(track_path, f"{track_name}.wav")

                        # 加入原始影片
                        if job.original_video_path and os.path.exists(job.original_video_path):
                            inner_zf.write(job.original_video_path, "video.mp4")

                        # 加入 metadata.json
                        metadata = self.create_metadata(job)
                        inner_zf.writestr("metadata.json", json.dumps(metadata, ensure_ascii=False, indent=2))

                    # 將內層 ZIP 加入外層
                    inner_buffer.seek(0)
                    outer_zf.writestr(inner_zip_name, inner_buffer.read())

            return str(zip_path)
        except Exception as e:
            print(f"Failed to create multi ZIP: {e}")
            return None

    def get_export_path(self, export_id: str) -> Optional[str]:
        """取得匯出檔案路徑"""
        export_dir = self.exports_dir / export_id
        if not export_dir.exists():
            return None

        # 找到該目錄下的 ZIP 檔案
        for f in export_dir.iterdir():
            if f.suffix == ".zip":
                return str(f)

        return None

    def delete_export(self, export_id: str):
        """刪除匯出檔案"""
        import shutil
        export_dir = self.exports_dir / export_id
        if export_dir.exists():
            shutil.rmtree(export_dir, ignore_errors=True)

    def _safe_filename(self, name: str) -> str:
        """轉換為安全的檔案名稱"""
        import re
        # 移除或替換不安全的字元
        safe = re.sub(r'[<>:"/\\|?*]', '_', name)
        safe = safe.strip()[:100]  # 限制長度
        return safe or "untitled"


# Global instance
_exporter: Optional[Exporter] = None


def get_exporter() -> Exporter:
    """取得匯出服務實例"""
    global _exporter
    if _exporter is None:
        _exporter = Exporter()
    return _exporter
