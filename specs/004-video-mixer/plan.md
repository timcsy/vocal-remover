# Implementation Plan: Video Mixer 影片混音器

**Branch**: `004-video-mixer` | **Date**: 2025-01-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/004-video-mixer/spec.md`

## Summary

將現有的人聲去除服務重構為影片混音器，新增左側抽屜歌曲列表、底部任務佇列、ZIP 匯出/匯入功能，以及模態視窗新增歌曲介面。擴展現有的 Vue 3 + FastAPI 架構，新增全域狀態管理和 ZIP 處理服務。

## Technical Context

**Language/Version**: Python 3.11 (Backend) + TypeScript 5.3 (Frontend)
**Primary Dependencies**: FastAPI, Pydantic, Vue 3, Vite, Tone.js
**Storage**: 本地檔案系統 + 記憶體狀態（無資料庫）
**Testing**: 手動測試（既有專案無測試框架）
**Target Platform**: Web 應用（Docker 容器部署）
**Project Type**: Web 應用（frontend + backend）
**Performance Goals**: 歌曲切換 < 3 秒，進度更新延遲 < 3 秒
**Constraints**: 記憶體儲存、單一任務處理、匯入上限 10 首
**Scale/Scope**: 支援 100 首歌曲列表、10 個佇列任務

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原則 | 狀態 | 說明 |
|------|------|------|
| I. 繁體中文優先 | ✅ 通過 | 所有規格與計畫文件使用繁體中文 |
| II. 簡潔設計 | ✅ 通過 | 僅實作規格要求的功能，無過度抽象 |
| III. 最小文件產出 | ✅ 通過 | 僅建立必要的規格文件 |
| IV. Git 版本控制紀律 | ⏳ 待執行 | 將於每階段完成後提交 |
| V. 任務追蹤完整性 | ⏳ 待執行 | 將於 implement 階段即時更新 |
| VI. 規格文件保護 | ✅ 通過 | 不會覆蓋 /specs/ 目錄 |

## Project Structure

### Documentation (this feature)

```text
specs/004-video-mixer/
├── plan.md              # 本文件
├── research.md          # Phase 0 研究輸出
├── data-model.md        # Phase 1 資料模型
├── quickstart.md        # Phase 1 快速開始指南
├── contracts/           # Phase 1 API 合約
│   └── api.yaml
└── tasks.md             # Phase 2 任務清單
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── api/v1/
│   │   └── jobs.py          # 修改：新增列表、匯出、匯入、刪除 API
│   ├── models/
│   │   └── job.py           # 修改：新增匯出相關欄位
│   └── services/
│       ├── exporter.py      # 新增：ZIP 匯出服務
│       ├── importer.py      # 新增：ZIP 匯入服務
│       └── job_manager.py   # 修改：新增查詢和刪除方法

frontend/
├── src/
│   ├── App.vue              # 重構：新佈局容器
│   ├── components/
│   │   ├── AppDrawer.vue    # 新增：左側抽屜
│   │   ├── SongList.vue     # 新增：歌曲列表
│   │   ├── SongItem.vue     # 新增：歌曲項目
│   │   ├── TaskQueue.vue    # 新增：任務佇列
│   │   ├── TaskItem.vue     # 新增：任務項目
│   │   ├── AddSongModal.vue # 新增：新增歌曲模態
│   │   ├── TaskDetailModal.vue # 新增：任務詳情模態
│   │   ├── ImportConflictModal.vue # 新增：匯入衝突確認
│   │   ├── MainView.vue     # 新增：主頁面內容
│   │   └── EmptyState.vue   # 新增：空狀態
│   ├── composables/
│   │   └── useJobManager.ts # 新增：全域任務狀態管理
│   └── services/
│       └── api.ts           # 修改：新增 API 方法
```

**Structure Decision**: 採用現有的 Web 應用結構（backend/ + frontend/），在既有架構上擴展功能。

## Complexity Tracking

> 無違反憲法原則的複雜度，無需記錄。
