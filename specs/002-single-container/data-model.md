# Data Model: 單一 Docker 容器架構

## 實體定義

### Job（任務）

代表一次人聲分離處理請求。

| 屬性 | 類型 | 說明 |
|------|------|------|
| id | string | 唯一識別碼 (UUID) |
| status | JobStatus | 任務狀態 |
| progress | int | 進度 (0-100) |
| current_stage | string | 目前階段說明 |
| source_type | SourceType | 來源類型 |
| source_url | string | YouTube URL 或上傳檔案路徑 |
| source_filename | string? | 上傳檔案的原始名稱 |
| source_title | string? | 影片標題 |
| original_duration | int? | 原始影片時長（秒） |
| result_path | string? | 結果檔案路徑 |
| error_message | string? | 錯誤訊息 |
| created_at | datetime | 建立時間 |
| updated_at | datetime | 更新時間 |

### JobStatus（任務狀態）

```
PENDING → DOWNLOADING → SEPARATING → MERGING → COMPLETED
                ↓            ↓           ↓
              FAILED       FAILED      FAILED
```

| 值 | 說明 |
|------|------|
| PENDING | 等待處理 |
| DOWNLOADING | 下載中（YouTube 或上傳檔案） |
| SEPARATING | 人聲分離中 |
| MERGING | 合併影片中 |
| COMPLETED | 完成 |
| FAILED | 失敗 |

### SourceType（來源類型）

| 值 | 說明 |
|------|------|
| YOUTUBE | YouTube 網址 |
| UPLOAD | 上傳檔案 |

## 儲存結構

### 記憶體儲存（JobManager）

```python
{
    "job_id_1": Job(...),
    "job_id_2": Job(...),
    ...
}
```

- 使用 Python dict 儲存
- threading.Lock 確保執行緒安全
- 容器重啟後自動清空

### 檔案儲存

```
/data/
├── uploads/
│   └── {job_id}/
│       └── input.{ext}     # 上傳的原始檔案
└── results/
    └── {job_id}/
        └── output.mp4      # 處理結果
```

## 狀態轉換規則

1. 建立任務 → PENDING
2. 開始下載 → DOWNLOADING
3. 下載完成，開始分離 → SEPARATING
4. 分離完成，開始合併 → MERGING
5. 合併完成 → COMPLETED
6. 任何階段發生錯誤 → FAILED（記錄 error_message）

## 資料清理

- 任務完成後，結果保留至容器停止
- 容器重啟時，/data/ 目錄內容自動清空（無 volume mount）
- 無需實作定期清理機制
