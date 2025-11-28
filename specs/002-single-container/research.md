# Research: 單一 Docker 容器架構

## 1. 背景任務處理方案

**Decision**: 使用 Python threading + FastAPI BackgroundTasks

**Rationale**:
- 個人桌面環境，1-2 並發任務，不需要分散式任務佇列
- FastAPI 原生支援 BackgroundTasks，無需額外依賴
- threading 足以處理 CPU 密集型任務（Demucs 分離）
- 避免引入 Celery/RQ 等額外元件

**Alternatives considered**:
- RQ (Redis Queue)：需要 Redis，增加複雜度
- Celery：過於龐大，不適合單容器場景
- asyncio：Demucs 是同步阻塞操作，asyncio 無法優化

## 2. 任務狀態管理方案

**Decision**: 使用 Python dict + threading.Lock

**Rationale**:
- 單一程序內執行，記憶體狀態足夠
- 容器重啟後任務自然清除（符合規格「暫時性」需求）
- 實作簡單，無外部依賴
- Lock 確保多執行緒安全

**Alternatives considered**:
- SQLite：增加持久化複雜度，不符合「暫時性」需求
- Redis：需要額外容器或內嵌 Redis，增加複雜度

## 3. 檔案儲存方案

**Decision**: 本地檔案系統 + 直接檔案路徑

**Rationale**:
- 上傳檔案存放於 /data/uploads/{job_id}/
- 處理結果存放於 /data/results/{job_id}/
- API 直接讀取檔案回傳，無需 presigned URL
- 容器停止後自動清除（無持久化 volume）

**Alternatives considered**:
- 內嵌 MinIO：增加容器複雜度和記憶體使用
- 臨時目錄 /tmp：可能因系統清理而遺失處理中的檔案

## 4. 容器程序管理方案

**Decision**: Supervisor 管理 Nginx + Uvicorn

**Rationale**:
- Supervisor 成熟穩定，適合管理多程序
- Nginx 提供靜態檔案服務和反向代理
- Uvicorn 執行 FastAPI 應用
- 容器內兩個程序，Supervisor 確保重啟恢復

**Alternatives considered**:
- 只用 Uvicorn：無法高效服務靜態檔案
- Docker 多程序腳本：不如 Supervisor 可靠

## 5. YouTube 下載方案

**Decision**: 僅使用 yt-dlp

**Rationale**:
- Cobalt API 需要 JWT 認證，公共 API 已關閉
- 個人桌面使用，yt-dlp 的 bot 偵測風險較低
- 保持架構簡潔

**Alternatives considered**:
- Cobalt fallback：需要自架 Cobalt 服務或取得 JWT
- Invidious API：穩定性不佳

## 6. 多階段 Docker 建置

**Decision**: 三階段建置（frontend-builder → backend → final）

**Rationale**:
- 第一階段：Node.js 建置前端
- 第二階段：Python 安裝後端依賴
- 第三階段：整合並安裝 Nginx/Supervisor
- 最小化最終映像大小

## 7. 並發任務處理

**Decision**: 簡單計數器限制 + 佇列等待

**Rationale**:
- 使用原子計數器追蹤處理中任務數量
- 超過限制時拒絕新任務並回傳明確訊息
- 個人使用情境下，簡單計數器足夠

**Alternatives considered**:
- Semaphore：Python threading.Semaphore 可用，但計數器更直觀
