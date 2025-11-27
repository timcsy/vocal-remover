# 資料模型：人聲去除服務

**日期**: 2025-11-27
**功能**: 001-vocal-remover-k8s

## 實體定義

### Job（任務）

代表一次影片處理請求。

| 欄位 | 型別 | 說明 | 必填 |
|------|------|------|------|
| id | UUID | 唯一識別碼 | 是 |
| source_type | Enum | 來源類型：`youtube` 或 `upload` | 是 |
| source_url | String | YouTube 網址（source_type=youtube 時） | 條件 |
| source_filename | String | 上傳檔名（source_type=upload 時） | 條件 |
| status | Enum | 任務狀態 | 是 |
| progress | Integer | 進度百分比（0-100） | 是 |
| current_stage | String | 目前階段描述 | 否 |
| error_message | String | 錯誤訊息（失敗時） | 否 |
| client_ip | String | 請求者 IP（限流用） | 是 |
| created_at | DateTime | 建立時間 | 是 |
| updated_at | DateTime | 更新時間 | 是 |
| completed_at | DateTime | 完成時間 | 否 |
| expires_at | DateTime | 過期時間（created_at + 24hr） | 是 |

**狀態轉換**：
```
pending → downloading → separating → merging → completed
                ↓            ↓           ↓
              failed      failed      failed
```

**狀態說明**：
- `pending`：等待處理
- `downloading`：下載影片中（YouTube 來源）
- `separating`：人聲分離中
- `merging`：合併影片中
- `completed`：處理完成
- `failed`：處理失敗

### Result（處理結果）

代表處理完成的輸出。

| 欄位 | 型別 | 說明 | 必填 |
|------|------|------|------|
| id | UUID | 唯一識別碼 | 是 |
| job_id | UUID | 關聯任務 ID | 是 |
| original_duration | Integer | 原始影片長度（秒） | 是 |
| original_size | Integer | 原始檔案大小（bytes） | 是 |
| output_path | String | 輸出檔案在儲存系統的路徑 | 是 |
| output_size | Integer | 輸出檔案大小（bytes） | 是 |
| download_url | String | 下載連結（帶簽名的臨時 URL） | 是 |
| created_at | DateTime | 建立時間 | 是 |
| expires_at | DateTime | 過期時間 | 是 |

### RateLimit（限流記錄）

追蹤 IP 請求次數。

| 欄位 | 型別 | 說明 | 必填 |
|------|------|------|------|
| client_ip | String | 客戶端 IP | 是 |
| request_count | Integer | 目前小時內請求次數 | 是 |
| window_start | DateTime | 計數視窗開始時間 | 是 |

## 關係圖

```
┌─────────────┐       ┌─────────────┐
│    Job      │ 1───1 │   Result    │
│             │       │             │
│ id          │       │ id          │
│ source_type │       │ job_id (FK) │
│ status      │       │ output_path │
│ progress    │       │ download_url│
│ ...         │       │ ...         │
└─────────────┘       └─────────────┘
       │
       │ 多 Job 可來自同一 IP
       ▼
┌─────────────┐
│  RateLimit  │
│             │
│ client_ip   │
│ request_cnt │
│ window_start│
└─────────────┘
```

## 驗證規則

### Job 建立時

1. `source_type=youtube` 時：
   - `source_url` 必須是有效的 YouTube 網址
   - 格式：`https://www.youtube.com/watch?v=*` 或 `https://youtu.be/*`

2. `source_type=upload` 時：
   - 檔案大小 ≤ 500MB
   - 格式必須是 MP4、MOV、AVI、MKV
   - 影片長度 ≤ 10 分鐘

3. 限流檢查：
   - 同一 IP 每小時最多 12 次請求
   - 超過限制回傳 429 Too Many Requests

## 生命週期

1. **Job 建立** → status=`pending`，expires_at=now+24hr
2. **處理開始** → status 依序更新，progress 遞增
3. **處理完成** → 建立 Result，status=`completed`
4. **過期清理** → expires_at 到期後，刪除 Job、Result 和相關檔案
