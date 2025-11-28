# Data Model: Video Mixer 影片混音器

## 實體關係圖

```
┌─────────────────┐         ┌─────────────────┐
│      Job        │         │   TrackPaths    │
│  (已完成歌曲)    │────────►│   (音軌路徑)     │
│                 │   1:1   │                 │
└────────┬────────┘         └─────────────────┘
         │
         │ 1:N
         ▼
┌─────────────────┐
│  ExportPackage  │
│   (匯出包)       │
└─────────────────┘
```

## 後端資料模型

### Job（任務/歌曲）

擴展既有 `Job` 模型，新增匯出相關欄位。

| 欄位 | 類型 | 說明 | 驗證規則 |
|------|------|------|----------|
| id | str | 唯一識別碼 | UUID 格式 |
| source_type | SourceType | 來源類型 | youtube / upload |
| source_url | str | 來源網址（YouTube）或本地路徑 | 可選 |
| source_filename | str | 原始檔案名稱 | 可選 |
| source_title | str | 歌曲標題 | 必填（完成後） |
| status | JobStatus | 任務狀態 | pending/downloading/separating/merging/mixing/completed/failed |
| progress | int | 處理進度 | 0-100 |
| current_stage | str | 當前處理階段描述 | 可選 |
| error_message | str | 錯誤訊息 | 可選 |
| result_key | str | 結果影片路徑 | 可選 |
| original_duration | int | 原始影片時長（秒） | 可選 |
| track_paths | TrackPaths | 分離後音軌路徑 | 可選 |
| sample_rate | int | 取樣率 | 預設 44100 |
| client_ip | str | 客戶端 IP | 必填 |
| created_at | datetime | 建立時間 | 自動設定 |
| updated_at | datetime | 更新時間 | 自動更新 |
| completed_at | datetime | 完成時間 | 可選 |
| expires_at | datetime | 過期時間 | 預設 24 小時後 |

### TrackPaths（音軌路徑）

| 欄位 | 類型 | 說明 |
|------|------|------|
| drums | str | 鼓聲音軌 WAV 路徑 |
| bass | str | 低音音軌 WAV 路徑 |
| other | str | 其他音軌 WAV 路徑 |
| vocals | str | 人聲音軌 WAV 路徑 |

### ExportMetadata（匯出 metadata.json）

| 欄位 | 類型 | 說明 |
|------|------|------|
| version | str | 格式版本 | "1.0" |
| source_title | str | 歌曲標題 |
| source_type | str | 來源類型 |
| source_url | str | 來源網址（可選） |
| original_duration | int | 原始時長（秒） |
| created_at | str | 建立時間（ISO 8601） |
| sample_rate | int | 取樣率 |

## 前端資料模型

### CompletedJob（已完成歌曲）

```typescript
interface CompletedJob {
  id: string;
  source_title: string;
  source_type: 'youtube' | 'upload';
  original_duration: number;
  created_at: string;
  selected: boolean;  // 前端狀態：是否勾選
}
```

### ProcessingJob（處理中任務）

```typescript
interface ProcessingJob {
  id: string;
  source_title: string;
  status: 'pending' | 'downloading' | 'separating' | 'merging' | 'mixing';
  progress: number;
  current_stage?: string;
}
```

### JobManagerState（全域狀態）

```typescript
interface JobManagerState {
  completedJobs: CompletedJob[];
  processingJobs: ProcessingJob[];
  selectedJobId: string | null;
  drawerOpen: boolean;
}
```

### ImportConflict（匯入衝突）

```typescript
interface ImportConflict {
  existingJobId: string;
  importTitle: string;
  resolution: 'overwrite' | 'rename' | 'skip' | null;
}
```

## 狀態轉換

### Job 狀態機

```
                    ┌──────────────┐
                    │   pending    │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
              ┌─────│ downloading  │─────┐
              │     └──────┬───────┘     │
              │            │             │
              │     ┌──────▼───────┐     │
              │     │  separating  │     │
              │     └──────┬───────┘     │
              │            │             │
              │     ┌──────▼───────┐     │
              │     │   merging    │     │
              │     └──────┬───────┘     │
              │            │             │
              │     ┌──────▼───────┐     │
              │     │   mixing     │     │
              │     └──────┬───────┘     │
              │            │             │
    ┌─────────▼────────────▼─────────────▼───┐
    │              completed                  │
    └─────────────────────────────────────────┘
              │
    ┌─────────▼─────────┐
    │      failed       │ (任何階段都可能失敗)
    └───────────────────┘
```

### Drawer 狀態

- `open`: 抽屜展開（桌面預設）
- `closed`: 抽屜收合（手機預設）

## 驗證規則

### 匯入驗證

1. ZIP 檔案必須包含 `metadata.json`
2. `metadata.json` 必須有 `version` 欄位
3. 必須包含至少一個 WAV 音軌
4. 單次匯入不超過 10 首歌曲

### 匯出驗證

1. 至少勾選一首歌曲
2. 所有勾選的歌曲必須為 completed 狀態
3. 音軌檔案必須存在

## 儲存說明

- 所有資料儲存於記憶體（`job_manager.py` 中的 dict）
- 音軌和影片檔案儲存於本地檔案系統 (`/data/jobs/{job_id}/`)
- 匯出的 ZIP 暫存於 `/data/exports/`
- 伺服器重啟後所有任務狀態將遺失
