# Implementation Plan: 單一 Docker 容器架構

**Branch**: `002-single-container` | **Date**: 2025-11-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-single-container/spec.md`

## Summary

將現有多容器架構（API + Worker + Frontend + Redis + MinIO）重構為單一 Docker 容器，適合個人桌面使用。移除外部依賴，改用記憶體任務追蹤與本地檔案儲存。

## Technical Context

**Language/Version**: Python 3.11, TypeScript/Vue 3
**Primary Dependencies**: FastAPI, Demucs, FFmpeg, yt-dlp, Nginx, Supervisor
**Storage**: 本地檔案系統（/data/uploads, /data/results）
**Testing**: pytest, 手動整合測試
**Target Platform**: Docker（Linux 容器），個人桌面環境
**Project Type**: Web 應用（前端 + 後端整合至單一容器）
**Performance Goals**: 啟動時間 <60 秒，處理效能與原架構相當
**Constraints**: 閒置記憶體 <500MB，無外部服務依賴
**Scale/Scope**: 單一使用者，1-2 並發任務

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原則 | 狀態 | 說明 |
|------|------|------|
| I. 繁體中文優先 | ✅ PASS | 規格與計畫文件皆使用繁體中文 |
| II. 簡潔設計 | ✅ PASS | 移除不必要的外部服務，簡化架構 |
| III. 最小文件產出 | ✅ PASS | 僅產生必要的 specs/ 文件 |
| IV. Git 版本控制紀律 | ⏳ PENDING | 待實作階段執行 |
| V. 任務追蹤完整性 | ⏳ PENDING | 待實作階段執行 |
| VI. 規格文件保護 | ✅ PASS | 不會覆蓋 /specs/ 目錄 |

## Project Structure

### Documentation (this feature)

```text
specs/002-single-container/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── api/v1/          # API endpoints（保留）
│   ├── core/
│   │   └── config.py    # 簡化設定（移除 Redis/MinIO）
│   ├── models/
│   │   └── job.py       # 任務模型（保留）
│   └── services/
│       ├── storage.py   # 改為本地檔案系統
│       ├── job_manager.py  # 新增：記憶體任務管理
│       ├── processor.py    # 新增：同步處理（取代 RQ）
│       ├── separator.py    # 保留
│       ├── merger.py       # 保留
│       └── youtube.py      # 保留（移除 cobalt fallback）
├── requirements.txt     # 移除 redis, boto3, rq
└── Dockerfile           # 更新為整合版

frontend/
├── src/                 # 保留不變
└── Dockerfile           # 刪除（整合至根目錄）

docker/                  # 新增目錄
├── nginx.conf           # Nginx 設定
└── supervisord.conf     # Supervisor 設定

Dockerfile               # 新增：多階段建置整合容器
docker-compose.yml       # 簡化為單一服務
```

**Structure Decision**: 保留現有 backend/frontend 結構，新增 docker/ 目錄存放容器設定，根目錄新增整合用 Dockerfile。

## Complexity Tracking

無違反需要記錄。
