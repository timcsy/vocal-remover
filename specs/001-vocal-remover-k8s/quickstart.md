# 快速開始：人聲去除服務

## 系統需求

- Python 3.11+
- Node.js 18+
- Docker
- NVIDIA GPU（推薦，用於加速處理）
- Kubernetes 集群（生產環境）

## 本地開發

### 1. 啟動依賴服務

```bash
# 啟動 Redis
docker run -d --name redis -p 6379:6379 redis:7-alpine

# 啟動 MinIO
docker run -d --name minio -p 9000:9000 -p 9001:9001 \
  -e MINIO_ROOT_USER=minioadmin \
  -e MINIO_ROOT_PASSWORD=minioadmin \
  minio/minio server /data --console-address ":9001"
```

### 2. 後端設定

```bash
# 建立虛擬環境
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安裝依賴
pip install -r requirements.txt

# 設定環境變數
cp .env.example .env
# 編輯 .env 填入正確的配置

# 啟動 API 伺服器
uvicorn main:app --reload --port 8000

# 另開終端，啟動 Worker
rq worker default
```

### 3. 前端設定

```bash
cd frontend
npm install
npm run dev
```

### 4. 存取服務

- 前端：http://localhost:5173
- API 文檔：http://localhost:8000/docs
- MinIO Console：http://localhost:9001

## 驗證流程

### 測試 YouTube 網址處理

```bash
# 建立任務
curl -X POST http://localhost:8000/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{"source_type": "youtube", "source_url": "https://www.youtube.com/watch?v=TEST_ID"}'

# 查詢狀態（用回傳的 job_id）
curl http://localhost:8000/api/v1/jobs/{job_id}

# 下載結果（處理完成後）
curl -L http://localhost:8000/api/v1/jobs/{job_id}/download -o output.mp4
```

### 測試檔案上傳

```bash
curl -X POST http://localhost:8000/api/v1/jobs \
  -F "source_type=upload" \
  -F "file=@test_video.mp4"
```

## Kubernetes 部署

```bash
# 建立命名空間
kubectl create namespace vocal

# 套用配置
kubectl apply -f k8s/ -n vocal

# 確認 Pod 狀態
kubectl get pods -n vocal

# 取得 Ingress IP
kubectl get ingress -n vocal
```

## 故障排除

### 常見問題

1. **GPU 未被偵測**
   - 確認已安裝 NVIDIA Container Toolkit
   - 檢查 `nvidia-smi` 是否正常

2. **Redis 連線失敗**
   - 確認 Redis 容器正在運行
   - 檢查 REDIS_URL 環境變數

3. **MinIO 上傳失敗**
   - 確認 MinIO 容器正在運行
   - 檢查 bucket 是否已建立

4. **處理時間過長**
   - 確認使用 GPU（DEVICE=cuda）
   - 檢查影片長度是否超過限制
