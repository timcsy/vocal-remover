# 實作計畫：人聲去除服務

**分支**: `001-vocal-remover-k8s` | **日期**: 2025-11-27 | **規格**: [spec.md](./spec.md)
**輸入**: 功能規格 `/specs/001-vocal-remover-k8s/spec.md`

## 摘要

建立一個 Kubernetes 服務，讓使用者可以輸入 YouTube 網址或上傳影片，系統自動去除人聲並將伴奏合併回原始影片，提供下載功能。採用 Demucs 進行人聲分離，FastAPI 作為後端框架，Vue 3 作為前端，RQ 處理非同步任務。

## 技術背景

**語言/版本**: Python 3.11、TypeScript 5.x
**主要依賴**: FastAPI、Demucs、yt-dlp、FFmpeg、Vue 3、RQ
**儲存**: MinIO（S3 相容物件儲存）、Redis（任務佇列）
**測試**: pytest、Vitest
**目標平台**: Kubernetes（支援 GPU 節點）
**專案類型**: Web 應用（前後端分離）
**效能目標**: 3 分鐘影片在 5 分鐘內完成處理、同時處理 10 個任務
**限制**: 影片 ≤10 分鐘、檔案 ≤500MB、每 IP 每小時 ≤12 次請求
**規模**: 10 個並行任務

## 憲法檢查

*閘門：Phase 0 研究前必須通過。Phase 1 設計後重新檢查。*

| 原則 | 狀態 | 說明 |
|------|------|------|
| I. 繁體中文優先 | ✅ 通過 | 所有文件使用繁體中文 |
| II. 簡潔設計 | ✅ 通過 | 選用最簡單的技術棧（RQ 而非 Celery） |
| III. 最小文件產出 | ✅ 通過 | 僅產生必要的規格文件 |
| IV. Git 版本控制紀律 | ✅ 通過 | 每階段正確提交 |
| V. 任務追蹤完整性 | ⏳ 待驗證 | implement 階段驗證 |
| VI. 規格文件保護 | ⏳ 待驗證 | implement 階段驗證 |

## 專案結構

### 文件（本功能）

```text
specs/001-vocal-remover-k8s/
├── spec.md              # 功能規格
├── plan.md              # 本檔案
├── research.md          # 技術研究
├── data-model.md        # 資料模型
├── quickstart.md        # 快速開始指南
├── contracts/           # API 合約
│   └── openapi.yaml     # OpenAPI 規格
└── tasks.md             # 任務清單（由 /speckit.tasks 產生）
```

### 原始碼（專案根目錄）

```text
backend/
├── app/
│   ├── main.py          # FastAPI 應用程式入口
│   ├── api/
│   │   └── v1/
│   │       ├── jobs.py      # 任務相關 API
│   │       └── health.py    # 健康檢查
│   ├── models/
│   │   └── job.py       # Job、Result 資料模型
│   ├── services/
│   │   ├── youtube.py   # YouTube 下載服務
│   │   ├── separator.py # 人聲分離服務
│   │   ├── merger.py    # 影片合併服務
│   │   └── storage.py   # MinIO 儲存服務
│   ├── workers/
│   │   └── tasks.py     # RQ 任務定義
│   └── core/
│       ├── config.py    # 配置管理
│       └── rate_limit.py # 限流邏輯
├── requirements.txt
├── Dockerfile
└── tests/

frontend/
├── src/
│   ├── App.vue
│   ├── components/
│   │   ├── UrlInput.vue     # YouTube 網址輸入
│   │   ├── FileUpload.vue   # 檔案上傳
│   │   ├── ProgressBar.vue  # 進度條
│   │   └── ResultView.vue   # 結果顯示與下載
│   ├── services/
│   │   └── api.ts       # API 呼叫封裝
│   └── main.ts
├── package.json
├── vite.config.ts
└── Dockerfile

k8s/
├── namespace.yaml
├── configmap.yaml
├── secrets.yaml
├── redis/
│   ├── statefulset.yaml
│   └── service.yaml
├── minio/
│   ├── statefulset.yaml
│   └── service.yaml
├── api/
│   ├── deployment.yaml
│   └── service.yaml
├── worker/
│   ├── deployment.yaml
│   └── keda-scaler.yaml
├── frontend/
│   ├── deployment.yaml
│   └── service.yaml
└── ingress.yaml
```

**結構決策**: 採用 Web 應用架構（Option 2），前後端分離。後端包含 API 和 Worker 兩個部署單元，Worker 處理 GPU 密集的人聲分離任務。

## 複雜度追蹤

> **僅當憲法檢查有需要正當化的違規時填寫**

無違規。所有設計決策符合簡潔設計原則。
