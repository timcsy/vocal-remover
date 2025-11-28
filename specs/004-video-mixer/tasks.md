# Tasks: Video Mixer 影片混音器

**Input**: Design documents from `/specs/004-video-mixer/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api.yaml

**Tests**: ✅ 自動化測試（Backend: pytest, Frontend: Vitest）

**Organization**: 任務按使用者故事分組，以支援獨立實作和測試

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 可以並行執行（不同檔案，無依賴）
- **[Story]**: 任務所屬的使用者故事（US1, US2, US3, US4, US5）
- 描述中包含確切的檔案路徑

## Path Conventions

- **Backend**: `backend/app/`, `backend/tests/`
- **Frontend**: `frontend/src/`, `frontend/tests/`

---

## Phase 1: Setup（基礎設施）

**Purpose**: 擴展現有專案結構，新增必要的基礎組件和測試框架

- [x] T001 在 backend/app/services/ 目錄下建立 exporter.py 和 importer.py 空檔案
- [x] T002 [P] 在 frontend/src/composables/ 目錄下建立 useJobManager.ts 空檔案
- [x] T003 [P] 在 frontend/src/components/ 目錄下建立新組件空檔案（AppDrawer.vue, SongList.vue, SongItem.vue, TaskQueue.vue, TaskItem.vue, AddSongModal.vue, TaskDetailModal.vue, ImportConflictModal.vue, MainView.vue, EmptyState.vue）
- [x] T004 [P] 設置 Backend 測試框架：安裝 pytest, pytest-asyncio 於 backend/requirements.txt，建立 backend/tests/ 目錄和 conftest.py
- [x] T005 [P] 設置 Frontend 測試框架：安裝 vitest, @vue/test-utils, happy-dom 於 frontend/package.json，建立 frontend/vitest.config.ts 和 frontend/tests/ 目錄

---

## Phase 2: Foundational（阻塞性前置任務）

**Purpose**: 所有使用者故事都需要的核心基礎設施

**⚠️ CRITICAL**: 此階段必須完成後才能開始任何使用者故事

### Tests for Foundational

- [x] T006 [P] 撰寫 backend/tests/test_job_manager.py 測試 get_all_jobs(), delete_job() 方法
- [x] T007 [P] 撰寫 backend/tests/test_jobs_api.py 測試 GET /jobs 端點

### Implementation for Foundational

- [x] T008 擴展 backend/app/services/job_manager.py 新增 get_all_jobs(), delete_job() 方法
- [x] T009 [P] 擴展 backend/app/api/v1/jobs.py 新增 GET /jobs 端點回傳所有任務列表
- [x] T010 [P] 擴展 frontend/src/services/api.ts 新增 getJobs(), deleteJob() API 方法
- [x] T011 實作 frontend/src/composables/useJobManager.ts 全域狀態管理（completedJobs, processingJobs, selectedJobId, drawerOpen, 輪詢邏輯）
- [x] T012 [P] 撰寫 frontend/tests/composables/useJobManager.test.ts 測試全域狀態管理邏輯

**Checkpoint**: 基礎設施就緒 - 可以開始使用者故事實作

---

## Phase 3: User Story 1 - 管理已完成歌曲 (Priority: P1) 🎯 MVP

**Goal**: 使用者可以在左側抽屜中查看已完成歌曲列表，點擊切換主頁面顯示

**Independent Test**: 處理一首歌曲後，在左側抽屜中看到該歌曲並點擊切換來測試

### Tests for User Story 1

- [x] T013 [P] [US1] 撰寫 frontend/tests/components/SongItem.test.ts 測試歌曲項目組件
- [x] T014 [P] [US1] 撰寫 frontend/tests/components/AppDrawer.test.ts 測試抽屜開關和響應式行為
- [x] T015 [P] [US1] 撰寫 backend/tests/test_jobs_api.py 新增 DELETE /jobs/{job_id} 測試

### Implementation for User Story 1

- [x] T016 [P] [US1] 實作 frontend/src/components/SongItem.vue 歌曲項目組件（checkbox, 名稱, 點擊選取）
- [x] T017 [P] [US1] 實作 frontend/src/components/EmptyState.vue 空狀態組件
- [x] T018 [US1] 實作 frontend/src/components/SongList.vue 歌曲列表組件（整合 SongItem, 批次選取邏輯）
- [x] T019 [US1] 實作 frontend/src/components/AppDrawer.vue 左側抽屜組件（CSS transform 動畫, 響應式斷點 768px）
- [x] T020 [US1] 實作 frontend/src/components/MainView.vue 主頁面內容組件（顯示選中歌曲的 ResultView 或 EmptyState）
- [x] T021 [US1] 重構 frontend/src/App.vue 整合新佈局（AppDrawer + MainView + 底部預留空間）
- [x] T022 [US1] 擴展 backend/app/api/v1/jobs.py 新增 DELETE /jobs/{job_id} 端點

**Checkpoint**: User Story 1 完成 - 左側抽屜歌曲列表可正常運作

---

## Phase 4: User Story 2 - 新增歌曲處理 (Priority: P1)

**Goal**: 使用者可以透過模態視窗新增歌曲（YouTube URL 或上傳）

**Independent Test**: 點擊新增按鈕、輸入 YouTube URL、提交後看到任務進入佇列

### Tests for User Story 2

- [x] T023 [P] [US2] 撰寫 frontend/tests/components/AddSongModal.test.ts 測試模態視窗開關和表單驗證

### Implementation for User Story 2

- [x] T024 [P] [US2] 實作 frontend/src/components/AddSongModal.vue 新增歌曲模態視窗（整合既有 UrlInput.vue 和 FileUpload.vue）
- [x] T025 [US2] 在 frontend/src/App.vue 新增「新增歌曲」按鈕和 AddSongModal 整合
- [x] T026 [US2] 整合 useJobManager 提交新任務後觸發輪詢刷新

**Checkpoint**: User Story 2 完成 - 可以透過模態視窗新增歌曲

---

## Phase 5: User Story 3 - 查看任務佇列進度 (Priority: P2)

**Goal**: 使用者可以在頁面底部看到任務佇列和進度

**Independent Test**: 提交新任務，觀察底部佇列顯示該任務及其進度更新

### Tests for User Story 3

- [x] T027 [P] [US3] 撰寫 frontend/tests/components/TaskQueue.test.ts 測試任務佇列顯示和進度更新
- [x] T028 [P] [US3] 撰寫 frontend/tests/components/TaskItem.test.ts 測試任務項目組件

### Implementation for User Story 3

- [x] T029 [P] [US3] 實作 frontend/src/components/TaskItem.vue 任務項目組件（名稱, 狀態, 進度條, 點擊事件）
- [x] T030 [P] [US3] 實作 frontend/src/components/TaskDetailModal.vue 任務詳情模態視窗
- [x] T031 [US3] 實作 frontend/src/components/TaskQueue.vue 任務佇列組件（整合 TaskItem, 固定底部）
- [x] T032 [US3] 在 frontend/src/App.vue 整合 TaskQueue 組件於頁面底部
- [x] T033 [US3] 確保任務完成後自動移入左側歌曲列表（useJobManager 狀態更新）

**Checkpoint**: User Story 3 完成 - 底部任務佇列可正常顯示進度

---

## Phase 6: User Story 4 - 匯出歌曲 (Priority: P2)

**Goal**: 使用者可以選取歌曲匯出為 ZIP 檔案

**Independent Test**: 勾選歌曲、點擊匯出、下載 ZIP 檔並驗證內容

### Tests for User Story 4

- [x] T034 [P] [US4] 撰寫 backend/tests/test_exporter.py 測試 ZIP 匯出服務（單首、多首、metadata.json）
- [x] T035 [P] [US4] 撰寫 backend/tests/test_jobs_api.py 新增 POST /jobs/export 端點測試

### Implementation for User Story 4

- [x] T036 [P] [US4] 實作 backend/app/services/exporter.py ZIP 匯出服務（create_single_zip, create_multi_zip, metadata.json 生成）
- [x] T037 [US4] 擴展 backend/app/api/v1/jobs.py 新增 POST /jobs/export 和 GET /jobs/export/download/{export_id} 端點
- [x] T038 [US4] 擴展 frontend/src/services/api.ts 新增 exportJobs() API 方法
- [x] T039 [US4] 在 frontend/src/components/AppDrawer.vue 新增「匯出」按鈕和匯出邏輯

**Checkpoint**: User Story 4 完成 - 歌曲匯出功能可正常運作

---

## Phase 7: User Story 5 - 匯入歌曲 (Priority: P3)

**Goal**: 使用者可以匯入 ZIP 檔案還原歌曲

**Independent Test**: 選擇有效 ZIP 檔、匯入後看到歌曲出現在左側抽屜

### Tests for User Story 5

- [x] T040 [P] [US5] 撰寫 backend/tests/test_importer.py 測試 ZIP 匯入服務（驗證、解壓、衝突檢測）
- [x] T041 [P] [US5] 撰寫 backend/tests/test_jobs_api.py 新增 POST /jobs/import 端點測試

### Implementation for User Story 5

- [x] T042 [P] [US5] 實作 backend/app/services/importer.py ZIP 匯入服務（validate_zip, import_single_song, import_multi_zip）
- [x] T043 [US5] 擴展 backend/app/api/v1/jobs.py 新增 POST /jobs/import 和 POST /jobs/import/resolve 端點
- [x] T044 [US5] 擴展 frontend/src/services/api.ts 新增 importJobs(), resolveImportConflict() API 方法
- [x] T045 [P] [US5] 實作 frontend/src/components/ImportConflictModal.vue 匯入衝突確認視窗
- [x] T046 [US5] 在 frontend/src/components/AppDrawer.vue 新增「匯入」按鈕和匯入邏輯（含衝突處理）

**Checkpoint**: User Story 5 完成 - 歌曲匯入功能可正常運作

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: 跨使用者故事的改進和收尾工作

- [x] T047 [P] 更新專案標題為「影片混音器」或「Video Mixer」於 frontend/index.html
- [x] T048 [P] 確保響應式設計：桌面版抽屜預設開啟、手機版預設收合
- [x] T049 確保所有模態視窗有適當的關閉機制和背景遮罩
- [x] T050 執行 quickstart.md 驗證流程，確認所有功能正常
- [x] T051 清理冗餘程式碼，確保一致的命名風格
- [x] T052 [P] 執行所有測試並確保通過：`cd backend && pytest` 和 `cd frontend && npm run test`
- [x] T053 [P] 在 CI 配置中新增測試步驟（如適用）

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 Setup**: 無依賴 - 立即開始
- **Phase 2 Foundational**: 依賴 Phase 1 - 阻塞所有使用者故事
- **Phase 3-7 User Stories**: 依賴 Phase 2 完成後可並行或依優先順序執行
- **Phase 8 Polish**: 依賴所有使用者故事完成

### User Story Dependencies

- **US1 (P1)**: Phase 2 完成後可開始 - 無其他故事依賴
- **US2 (P1)**: Phase 2 完成後可開始 - 獨立於 US1（但可並行）
- **US3 (P2)**: Phase 2 完成後可開始 - 與 US1/US2 整合但可獨立測試
- **US4 (P2)**: Phase 2 完成後可開始 - 依賴 US1 的勾選機制
- **US5 (P3)**: Phase 2 完成後可開始 - 依賴 US4 的 ZIP 格式定義

### Testing Strategy

- **TDD 流程**: 每個使用者故事先撰寫測試，確認測試失敗，再實作功能
- **Backend**: 使用 pytest + pytest-asyncio 測試 API 和服務
- **Frontend**: 使用 Vitest + @vue/test-utils 測試組件

### Parallel Opportunities

**Phase 1 內部**:
- T004, T005 可並行（不同語言環境）

**Phase 2 內部**:
- T006, T007 可並行（不同測試檔案）
- T009, T010, T012 可並行（不同檔案）

**US1 內部**:
- T013, T014, T015 可並行（測試）
- T016, T017 可並行（不同組件）

**US4 和 US5 準備**:
- T034, T040 可並行（不同測試）
- T036, T042 可並行（不同服務）

---

## Parallel Example: Phase 2

```bash
# 可同時執行測試撰寫：
Task T006: "撰寫 backend/tests/test_job_manager.py"
Task T007: "撰寫 backend/tests/test_jobs_api.py"

# 測試通過後，可同時執行實作：
Task T009: "擴展 backend/app/api/v1/jobs.py 新增 GET /jobs 端點"
Task T010: "擴展 frontend/src/services/api.ts 新增 API 方法"
```

## Parallel Example: User Story 4

```bash
# 先撰寫測試：
Task T034: "撰寫 backend/tests/test_exporter.py"
Task T035: "撰寫 backend/tests/test_jobs_api.py 匯出端點測試"

# 測試失敗後，實作服務：
Task T036: "實作 backend/app/services/exporter.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 + 2 Only)

1. 完成 Phase 1: Setup（含測試框架）
2. 完成 Phase 2: Foundational（CRITICAL - 阻塞所有故事）
3. 完成 Phase 3: User Story 1（左側抽屜歌曲列表）
4. 完成 Phase 4: User Story 2（新增歌曲模態）
5. **STOP and VALIDATE**: 執行測試 + 手動驗證 US1 + US2
6. 可部署/展示 MVP

### Incremental Delivery

1. Setup + Foundational → 基礎就緒 + 測試框架就緒
2. 加入 US1 → 測試通過 → 部署（歌曲管理）
3. 加入 US2 → 測試通過 → 部署（新增歌曲）
4. 加入 US3 → 測試通過 → 部署（任務佇列）
5. 加入 US4 → 測試通過 → 部署（匯出功能）
6. 加入 US5 → 測試通過 → 部署（匯入功能）
7. Polish + 全部測試通過 → 最終發布

---

## Test Commands

```bash
# Backend 測試
cd backend && pytest -v

# Frontend 測試
cd frontend && npm run test

# 全部測試（CI 用）
cd backend && pytest && cd ../frontend && npm run test
```

---

## Notes

- [P] tasks = 不同檔案，無依賴
- [Story] label = 任務所屬使用者故事
- 每個使用者故事應可獨立完成和測試
- TDD：先撰寫測試，確認失敗，再實作
- 每個任務或邏輯群組完成後提交
- 任何 Checkpoint 都可停止驗證故事獨立性
- 測試覆蓋：Backend API + Services, Frontend Components + Composables
