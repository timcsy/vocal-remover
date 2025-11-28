# Quickstart: Video Mixer 影片混音器

## 開發環境設定

### 前置需求

- Docker 與 Docker Compose
- Node.js 18+ (僅開發時需要)
- Python 3.11+ (僅開發時需要)

### 啟動服務

```bash
# 在專案根目錄執行
docker-compose up -d
```

服務將在以下位址啟動：
- 前端：http://localhost:5173
- 後端 API：http://localhost:8000/api/v1

## 功能驗證流程

### 1. 新增歌曲

```bash
# 方法一：YouTube URL
curl -X POST http://localhost:8000/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{"source_type": "youtube", "source_url": "https://www.youtube.com/watch?v=..."}'

# 方法二：上傳檔案
curl -X POST http://localhost:8000/api/v1/jobs/upload \
  -F "file=@/path/to/video.mp4"
```

### 2. 查詢任務列表

```bash
# 取得所有任務（已完成 + 處理中）
curl http://localhost:8000/api/v1/jobs
```

預期回應：
```json
{
  "jobs": [
    {
      "id": "uuid",
      "source_title": "歌曲名稱",
      "source_type": "youtube",
      "status": "completed",
      "original_duration": 180,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "processing": [
    {
      "id": "uuid",
      "source_title": "處理中",
      "status": "separating",
      "progress": 45
    }
  ]
}
```

### 3. 匯出歌曲

```bash
# 匯出單首或多首歌曲
curl -X POST http://localhost:8000/api/v1/jobs/export \
  -H "Content-Type: application/json" \
  -d '{"job_ids": ["uuid1", "uuid2"]}'

# 回應
{"download_url": "/api/v1/jobs/export/download/export_id"}

# 下載 ZIP
curl -O http://localhost:8000/api/v1/jobs/export/download/export_id
```

### 4. 匯入歌曲

```bash
# 匯入 ZIP
curl -X POST http://localhost:8000/api/v1/jobs/import \
  -F "file=@export.zip"

# 如有衝突，解決衝突
curl -X POST http://localhost:8000/api/v1/jobs/import/resolve \
  -H "Content-Type: application/json" \
  -d '{"temp_id": "temp_uuid", "resolution": "rename"}'
```

### 5. 刪除歌曲

```bash
curl -X DELETE http://localhost:8000/api/v1/jobs/uuid
```

## 前端組件層級

```
App.vue
├── AppDrawer.vue (左側抽屜)
│   ├── SongList.vue
│   │   └── SongItem.vue (多個)
│   └── [匯入/匯出 按鈕]
│
├── MainView.vue (主內容區)
│   ├── EmptyState.vue (無選中歌曲時)
│   └── ResultView.vue (選中歌曲時)
│       └── AudioMixer/ (既有組件)
│
├── TaskQueue.vue (底部佇列)
│   └── TaskItem.vue (多個)
│
├── AddSongModal.vue (新增歌曲模態)
├── TaskDetailModal.vue (任務詳情模態)
└── ImportConflictModal.vue (匯入衝突確認)
```

## 關鍵 Composable

### useJobManager.ts

```typescript
// 使用方式
import { useJobManager } from '@/composables/useJobManager';

const {
  completedJobs,      // 已完成歌曲列表
  processingJobs,     // 處理中任務列表
  selectedJobId,      // 當前選中的歌曲 ID
  drawerOpen,         // 抽屜開關狀態
  selectJob,          // 選擇歌曲
  toggleDrawer,       // 切換抽屜
  refreshJobs,        // 手動刷新
  startPolling,       // 開始輪詢
  stopPolling,        // 停止輪詢
} = useJobManager();
```

## 測試要點

1. **左側抽屜**
   - 桌面版預設開啟
   - 手機版預設收合
   - 動畫流暢無卡頓

2. **任務佇列**
   - 進度每 2 秒更新
   - 完成後移到歌曲列表
   - 點擊可查看詳情

3. **匯出**
   - 單首：`{title}.zip`
   - 多首：`export_YYYYMMDD.zip`
   - 內含 4 軌 WAV + video.mp4 + metadata.json

4. **匯入**
   - 驗證 ZIP 格式
   - 名稱衝突彈出確認
   - 上限 10 首
