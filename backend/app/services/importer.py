"""
ZIP 匯入服務

提供從 ZIP 檔案匯入歌曲的功能。
"""
import json
import os
import shutil
import uuid
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from app.core.config import get_settings
from app.models.job import Job, JobStatus, SourceType, TrackPaths
from app.services.job_manager import get_job_manager


class ImportResult:
    """匯入結果"""
    def __init__(self):
        self.imported: List[Job] = []
        self.conflicts: List[Dict] = []
        self.errors: List[str] = []


class Importer:
    """ZIP 匯入服務"""

    def __init__(self):
        settings = get_settings()
        self.results_dir = Path(settings.results_dir)
        self.imports_dir = self.results_dir / "imports"
        self.imports_dir.mkdir(parents=True, exist_ok=True)
        # 暫存待解決衝突的匯入資料
        self._pending_imports: Dict[str, Dict] = {}

    def import_zip(self, zip_path: str) -> ImportResult:
        """
        匯入 ZIP 檔案

        支援兩種格式：
        1. 單首歌曲 ZIP（直接包含 metadata.json 和音軌）
        2. 多首歌曲 ZIP（包含多個巢狀 ZIP）

        Returns:
            ImportResult 包含匯入結果、衝突和錯誤
        """
        result = ImportResult()

        if not os.path.exists(zip_path):
            result.errors.append(f"檔案不存在: {zip_path}")
            return result

        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                names = zf.namelist()

                # 檢查是否為巢狀 ZIP（多首歌曲）
                inner_zips = [n for n in names if n.endswith('.zip')]

                if inner_zips:
                    # 多首歌曲格式
                    for inner_zip_name in inner_zips:
                        inner_result = self._import_inner_zip(zf, inner_zip_name)
                        result.imported.extend(inner_result.imported)
                        result.conflicts.extend(inner_result.conflicts)
                        result.errors.extend(inner_result.errors)
                elif 'metadata.json' in names:
                    # 單首歌曲格式
                    single_result = self._import_single_song(zf)
                    result.imported.extend(single_result.imported)
                    result.conflicts.extend(single_result.conflicts)
                    result.errors.extend(single_result.errors)
                else:
                    result.errors.append("無效的 ZIP 格式：缺少 metadata.json")

        except zipfile.BadZipFile:
            result.errors.append("無效的 ZIP 檔案")
        except Exception as e:
            result.errors.append(f"匯入失敗: {str(e)}")

        return result

    def _import_inner_zip(self, outer_zf: zipfile.ZipFile, inner_zip_name: str) -> ImportResult:
        """匯入巢狀 ZIP 中的單首歌曲"""
        result = ImportResult()

        try:
            # 讀取內層 ZIP 到記憶體
            from io import BytesIO
            inner_data = outer_zf.read(inner_zip_name)
            inner_buffer = BytesIO(inner_data)

            with zipfile.ZipFile(inner_buffer, 'r') as inner_zf:
                single_result = self._import_single_song(inner_zf)
                result.imported = single_result.imported
                result.conflicts = single_result.conflicts
                result.errors = single_result.errors

        except Exception as e:
            result.errors.append(f"匯入 {inner_zip_name} 失敗: {str(e)}")

        return result

    def _import_single_song(self, zf: zipfile.ZipFile) -> ImportResult:
        """匯入單首歌曲"""
        result = ImportResult()

        try:
            # 讀取 metadata
            metadata_str = zf.read('metadata.json').decode('utf-8')
            metadata = json.loads(metadata_str)

            source_title = metadata.get('source_title', 'Untitled')

            # 檢查是否有同名歌曲
            job_manager = get_job_manager()
            existing_job = job_manager.find_job_by_title(source_title)

            if existing_job:
                # 產生衝突 ID 並暫存資料
                conflict_id = str(uuid.uuid4())
                self._pending_imports[conflict_id] = {
                    'zip_data': zf,
                    'metadata': metadata,
                    'existing_job_id': existing_job.id,
                }
                # 我們需要重新讀取 ZIP 資料，因為 ZipFile 物件可能在之後被關閉
                # 所以這裡改為暫存所有需要的檔案資料
                files_data = {}
                for name in zf.namelist():
                    files_data[name] = zf.read(name)
                self._pending_imports[conflict_id] = {
                    'files_data': files_data,
                    'metadata': metadata,
                    'existing_job_id': existing_job.id,
                }

                result.conflicts.append({
                    'conflict_id': conflict_id,
                    'source_title': source_title,
                    'existing_job_id': existing_job.id,
                })
            else:
                # 直接匯入
                job = self._create_job_from_zip(zf, metadata)
                if job:
                    result.imported.append(job)

        except json.JSONDecodeError:
            result.errors.append("metadata.json 格式錯誤")
        except Exception as e:
            result.errors.append(f"匯入歌曲失敗: {str(e)}")

        return result

    def _create_job_from_zip(
        self,
        zf: zipfile.ZipFile,
        metadata: dict,
        new_title: Optional[str] = None
    ) -> Optional[Job]:
        """從 ZIP 建立 Job"""
        job_id = str(uuid.uuid4())
        job_dir = self.results_dir / job_id
        job_dir.mkdir(parents=True, exist_ok=True)

        try:
            track_paths = TrackPaths()
            video_path = None

            # 解壓音軌檔案
            for track_name in ['drums', 'bass', 'other', 'vocals']:
                filename = f'{track_name}.wav'
                if filename in zf.namelist():
                    track_path = job_dir / filename
                    with open(track_path, 'wb') as f:
                        f.write(zf.read(filename))
                    setattr(track_paths, track_name, str(track_path))

            # 解壓影片（如果存在）- 這是原始影片（含人聲）
            if 'video.mp4' in zf.namelist():
                video_path = job_dir / 'original.mp4'
                with open(video_path, 'wb') as f:
                    f.write(zf.read('video.mp4'))

            # 建立 Job
            source_type_str = metadata.get('source_type', 'upload')
            try:
                source_type = SourceType(source_type_str)
            except ValueError:
                source_type = SourceType.UPLOAD

            job = Job(
                id=job_id,
                source_title=new_title or metadata.get('source_title', 'Untitled'),
                source_type=source_type,
                source_url=metadata.get('source_url'),
                original_duration=metadata.get('original_duration'),
                sample_rate=metadata.get('sample_rate', 44100),
                status=JobStatus.COMPLETED,
                progress=100,
                created_at=datetime.now(),
                completed_at=datetime.now(),
                track_paths=track_paths,
                original_video_path=str(video_path) if video_path else None,
                client_ip='imported',
            )

            # 加入 JobManager
            job_manager = get_job_manager()
            job_manager.add_imported_job(job)

            return job

        except Exception as e:
            # 清理失敗的目錄
            shutil.rmtree(job_dir, ignore_errors=True)
            raise e

    def _create_job_from_files_data(
        self,
        files_data: Dict[str, bytes],
        metadata: dict,
        new_title: Optional[str] = None
    ) -> Optional[Job]:
        """從暫存的檔案資料建立 Job"""
        job_id = str(uuid.uuid4())
        job_dir = self.results_dir / job_id
        job_dir.mkdir(parents=True, exist_ok=True)

        try:
            track_paths = TrackPaths()
            video_path = None

            # 寫入音軌檔案
            for track_name in ['drums', 'bass', 'other', 'vocals']:
                filename = f'{track_name}.wav'
                if filename in files_data:
                    track_path = job_dir / filename
                    with open(track_path, 'wb') as f:
                        f.write(files_data[filename])
                    setattr(track_paths, track_name, str(track_path))

            # 寫入影片（如果存在）- 這是原始影片（含人聲）
            if 'video.mp4' in files_data:
                video_path = job_dir / 'original.mp4'
                with open(video_path, 'wb') as f:
                    f.write(files_data['video.mp4'])

            # 建立 Job
            source_type_str = metadata.get('source_type', 'upload')
            try:
                source_type = SourceType(source_type_str)
            except ValueError:
                source_type = SourceType.UPLOAD

            job = Job(
                id=job_id,
                source_title=new_title or metadata.get('source_title', 'Untitled'),
                source_type=source_type,
                source_url=metadata.get('source_url'),
                original_duration=metadata.get('original_duration'),
                sample_rate=metadata.get('sample_rate', 44100),
                status=JobStatus.COMPLETED,
                progress=100,
                created_at=datetime.now(),
                completed_at=datetime.now(),
                track_paths=track_paths,
                original_video_path=str(video_path) if video_path else None,
                client_ip='imported',
            )

            # 加入 JobManager
            job_manager = get_job_manager()
            job_manager.add_imported_job(job)

            return job

        except Exception as e:
            # 清理失敗的目錄
            shutil.rmtree(job_dir, ignore_errors=True)
            raise e

    def resolve_conflict(
        self,
        conflict_id: str,
        action: str,
        new_title: Optional[str] = None
    ) -> Tuple[Optional[Job], Optional[str]]:
        """
        解決匯入衝突

        Args:
            conflict_id: 衝突 ID
            action: 'overwrite' 或 'rename'
            new_title: 新名稱（action='rename' 時需要）

        Returns:
            (Job, None) 成功時
            (None, error_message) 失敗時
        """
        if conflict_id not in self._pending_imports:
            return None, "找不到此衝突記錄"

        pending = self._pending_imports[conflict_id]
        metadata = pending['metadata']
        files_data = pending['files_data']
        existing_job_id = pending['existing_job_id']

        try:
            if action == 'overwrite':
                # 刪除舊的 Job
                job_manager = get_job_manager()
                job_manager.delete_job(existing_job_id)

                # 匯入新的
                job = self._create_job_from_files_data(files_data, metadata)
                del self._pending_imports[conflict_id]
                return job, None

            elif action == 'rename':
                if not new_title:
                    return None, "重新命名需要提供新名稱"

                # 檢查新名稱是否也衝突
                job_manager = get_job_manager()
                if job_manager.find_job_by_title(new_title):
                    return None, f"名稱 '{new_title}' 已存在"

                # 用新名稱匯入
                job = self._create_job_from_files_data(files_data, metadata, new_title)
                del self._pending_imports[conflict_id]
                return job, None

            else:
                return None, f"無效的操作: {action}"

        except Exception as e:
            return None, str(e)

    def cancel_conflict(self, conflict_id: str):
        """取消衝突處理"""
        if conflict_id in self._pending_imports:
            del self._pending_imports[conflict_id]


# Global instance
_importer: Optional[Importer] = None


def get_importer() -> Importer:
    """取得匯入服務實例"""
    global _importer
    if _importer is None:
        _importer = Importer()
    return _importer
