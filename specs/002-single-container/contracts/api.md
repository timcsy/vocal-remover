# API Contracts: 單一 Docker 容器架構

保持與現有 API 相容，僅調整實作細節。

## Base URL

```
http://localhost:8080/api/v1
```

## Endpoints

### Health Check

```
GET /health
```

**Response** `200 OK`
```json
{
  "status": "ok",
  "service": "人聲去除服務"
}
```

---

### 建立 YouTube 任務

```
POST /jobs/youtube
```

**Request Body**
```json
{
  "url": "https://www.youtube.com/watch?v=..."
}
```

**Response** `201 Created`
```json
{
  "id": "uuid",
  "status": "pending",
  "progress": 0,
  "current_stage": "等待處理",
  "source_type": "youtube",
  "source_url": "https://www.youtube.com/watch?v=...",
  "created_at": "2025-11-28T12:00:00Z"
}
```

**Error** `400 Bad Request` - 無效的 YouTube URL
**Error** `503 Service Unavailable` - 系統繁忙（超過並發限制）

---

### 上傳檔案建立任務

```
POST /jobs/upload
Content-Type: multipart/form-data
```

**Request Body**
- `file`: 影片檔案 (MP4, MKV, WebM 等)

**Response** `201 Created`
```json
{
  "id": "uuid",
  "status": "pending",
  "progress": 0,
  "current_stage": "等待處理",
  "source_type": "upload",
  "source_filename": "video.mp4",
  "created_at": "2025-11-28T12:00:00Z"
}
```

**Error** `400 Bad Request` - 不支援的檔案格式
**Error** `503 Service Unavailable` - 系統繁忙

---

### 查詢任務狀態

```
GET /jobs/{job_id}
```

**Response** `200 OK`
```json
{
  "id": "uuid",
  "status": "separating",
  "progress": 45,
  "current_stage": "分離人聲中...",
  "source_type": "youtube",
  "source_url": "...",
  "source_title": "影片標題",
  "original_duration": 180,
  "created_at": "2025-11-28T12:00:00Z",
  "updated_at": "2025-11-28T12:02:00Z"
}
```

**Error** `404 Not Found` - 任務不存在

---

### 下載結果

```
GET /jobs/{job_id}/download
```

**Response** `200 OK`
- Content-Type: video/mp4
- Content-Disposition: attachment; filename="output.mp4"

**Error** `404 Not Found` - 任務不存在或未完成

---

### 串流結果（支援 Range 請求）

```
GET /jobs/{job_id}/stream
```

**Headers**
- `Range: bytes=0-1000` (可選)

**Response** `200 OK` 或 `206 Partial Content`
- Content-Type: video/mp4
- Accept-Ranges: bytes

**Error** `404 Not Found` - 任務不存在或未完成

---

## Error Response Format

```json
{
  "detail": "錯誤描述"
}
```

## 變更說明

相較於原多容器架構：
- 移除 presigned URL（改為直接檔案下載）
- 移除速率限制（個人使用無需限制）
- 新增並發限制錯誤 (503)
