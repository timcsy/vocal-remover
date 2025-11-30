# Tasks: 純前端人聲去除服務架構改造

**Input**: Design documents from `/specs/005-frontend-processing/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: 未明確要求測試，此任務清單不包含測試任務。

**Organization**: 任務依使用者故事分組，支援獨立實作與測試。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 可並行執行（不同檔案，無依賴）
- **[Story]**: 所屬使用者故事（US1, US2, US3, US4）
- 描述包含確切檔案路徑

---

## Phase 1: Setup（專案設定）

**Purpose**: 專案初始化與基礎結構設定

- [ ] T001 安裝前端新依賴：npm install demucs-web onnxruntime-web lamejs 於 frontend/
- [ ] T002 [P] 下載 coi-serviceworker.js 到 frontend/public/coi-serviceworker.js
- [ ] T003 [P] 更新 frontend/index.html 引入 coi-serviceworker.js 和 ffmpeg.wasm CDN
- [ ] T004 [P] 更新 frontend/vite.config.ts 加入 COOP/COEP headers（開發模式）
- [ ] T005 [P] 更新 docker/nginx.conf 加入 COOP/COEP headers（Docker 模式）

---

## Phase 2: Foundational（基礎建設）

**Purpose**: 所有使用者故事共用的核心基礎設施

**⚠️ CRITICAL**: 此階段必須完成後才能開始任何使用者故事

- [ ] T006 建立型別定義檔 frontend/src/types/storage.ts（SongRecord, ProcessingState, MixerSettings 等）
- [ ] T007 [P] 建立瀏覽器相容性檢查工具 frontend/src/utils/browserCheck.ts
- [ ] T008 [P] 建立 IndexedDB 儲存服務 frontend/src/services/storageService.ts
- [ ] T009 [P] 建立 demucs-web 封裝服務 frontend/src/services/demucsService.ts
- [ ] T010 [P] 建立 ffmpeg.wasm 封裝服務 frontend/src/services/ffmpegService.ts
- [ ] T011 [P] 建立音訊匯出服務 frontend/src/services/audioExportService.ts（WAV/MP3）
- [ ] T012 更新 frontend/src/services/api.ts 加入後端偵測和 YouTube 代理 API
- [ ] T013 建立 App 啟動時的瀏覽器檢查與後端偵測邏輯於 frontend/src/App.vue

**Checkpoint**: 基礎設施就緒 - 可開始使用者故事實作

---

## Phase 3: User Story 1 - 本地影片上傳處理 (Priority: P1) 🎯 MVP

**Goal**: 使用者可上傳本地影片，瀏覽器完成人聲分離，無需後端

**Independent Test**: 在 GitHub Pages 靜態部署環境上傳影片，應能完成分離並播放

### Implementation for User Story 1

- [ ] T014 [US1] 建立本地處理流程 composable frontend/src/composables/useLocalProcessor.ts
- [ ] T015 [US1] 修改 frontend/src/composables/useJobManager.ts 改用 IndexedDB 儲存
- [ ] T016 [US1] 修改 frontend/src/composables/useWebAudio.ts 支援從 ArrayBuffer 載入音軌
- [ ] T017 [US1] 修改 frontend/src/components/AddSongModal.vue 整合本地處理流程
- [ ] T018 [US1] 加入處理進度顯示（多階段：提取音頻 → 分離人聲 → 儲存）
- [ ] T019 [US1] 加入瀏覽器不支援時的全螢幕警告元件
- [ ] T020 [US1] 加入 WebGPU 不支援時的效能警告提示
- [ ] T021 [US1] 加入檔案大小超過 100MB 的軟限制警告

**Checkpoint**: User Story 1 完成 - 可獨立測試本地上傳處理功能

---

## Phase 4: User Story 2 - 歌曲管理與刪除 (Priority: P1)

**Goal**: 使用者可查看已處理歌曲列表，並刪除歌曲釋放空間

**Independent Test**: 處理一首歌後，在列表中看到並刪除它，確認空間已釋放

### Implementation for User Story 2

- [ ] T022 [US2] 修改 frontend/src/components/SongList.vue 從 IndexedDB 載入歌曲列表
- [ ] T023 [US2] 加入歌曲刪除功能（含確認對話框）
- [ ] T024 [US2] 加入 IndexedDB 儲存使用量顯示
- [ ] T025 [US2] 加入儲存空間已滿時的錯誤提示

**Checkpoint**: User Stories 1 & 2 完成 - 可獨立測試歌曲管理功能

---

## Phase 5: User Story 3 - 混音下載輸出 (Priority: P2)

**Goal**: 使用者可調整混音後下載 MP4/MP3/M4A/WAV 檔案

**Independent Test**: 處理完成後，選擇不同格式下載，確認輸出正確

### Implementation for User Story 3

- [ ] T026 [US3] 修改 frontend/src/components/ResultView.vue 整合新的下載邏輯
- [ ] T027 [US3] 實作 WAV 下載（使用 audioExportService.mixToWav）
- [ ] T028 [US3] 實作 MP3 下載（使用 audioExportService.mixToMp3 + lamejs）
- [ ] T029 [US3] 實作 MP4/M4A 下載（純靜態模式：ffmpegService.mergeVideoAudio）
- [ ] T030 [US3] 實作 MP4/M4A 下載（Docker 模式：後端 FFmpeg API）
- [ ] T031 [US3] 根據後端可用性自動選擇下載方式

**Checkpoint**: User Stories 1, 2 & 3 完成 - 純靜態部署功能完整

---

## Phase 6: User Story 4 - YouTube 影片處理（Docker 模式）(Priority: P3)

**Goal**: Docker 部署時，使用者可輸入 YouTube 網址下載處理

**Independent Test**: 在 Docker 環境輸入 YouTube 網址，應能下載並完成分離

### Backend Implementation

- [ ] T032 [P] [US4] 建立 YouTube 代理 API 端點 backend/app/api/v1/youtube.py
- [ ] T033 [P] [US4] 建立 FFmpeg 代理 API 端點（extract-audio, merge）於 backend/app/api/v1/ffmpeg.py
- [ ] T034 [US4] 更新 backend/app/main.py 註冊新路由
- [ ] T035 [US4] 簡化 backend/app/main.py 移除舊的 jobs API

### Frontend Implementation

- [ ] T036 [US4] 修改 frontend/src/components/AddSongModal.vue 根據後端可用性顯示/隱藏 YouTube 輸入
- [ ] T037 [US4] 實作 YouTube 下載處理流程於 useLocalProcessor.ts
- [ ] T038 [US4] 加入純靜態模式時的「請自行下載影片」提示
- [ ] T039 [US4] 加入 YouTube 網址驗證和錯誤處理

**Checkpoint**: 所有使用者故事完成 - Docker 部署功能完整

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: 跨功能優化與清理

- [ ] T040 移除舊的後端處理程式碼（job_manager.py, processor.py, separator.py 等）
- [ ] T041 [P] 更新 Dockerfile 移除 Demucs 模型依賴（減小映像大小）
- [ ] T042 [P] 更新 frontend/package.json 移除不再需要的依賴
- [ ] T043 驗證 quickstart.md 所有步驟正確
- [ ] T044 效能測試：確認 3 分鐘歌曲處理時間 ≤5 分鐘

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 無依賴 - 可立即開始
- **Foundational (Phase 2)**: 依賴 Setup 完成 - 阻塞所有使用者故事
- **User Stories (Phase 3-6)**: 依賴 Foundational 完成
  - US1 & US2 (P1) 可並行進行
  - US3 (P2) 依賴 US1 完成
  - US4 (P3) 可獨立進行（後端部分）
- **Polish (Phase 7)**: 依賴所有使用者故事完成

### User Story Dependencies

- **User Story 1 (P1)**: Foundational 完成後可開始 - 無其他故事依賴
- **User Story 2 (P1)**: Foundational 完成後可開始 - 可與 US1 並行
- **User Story 3 (P2)**: 依賴 US1 的處理功能完成
- **User Story 4 (P3)**: 後端部分可獨立進行，前端整合依賴 US1

### Within Each User Story

- Services before composables
- Composables before components
- Core implementation before edge cases

### Parallel Opportunities

- T002, T003, T004, T005 可並行（Setup 階段）
- T007, T008, T009, T010, T011 可並行（Foundational 階段）
- US1 與 US2 可並行（兩者皆為 P1）
- T032, T033 可並行（後端 API 建立）

---

## Parallel Example: Foundational Phase

```bash
# 可同時啟動：
Task: "建立瀏覽器相容性檢查工具 frontend/src/utils/browserCheck.ts"
Task: "建立 IndexedDB 儲存服務 frontend/src/services/storageService.ts"
Task: "建立 demucs-web 封裝服務 frontend/src/services/demucsService.ts"
Task: "建立 ffmpeg.wasm 封裝服務 frontend/src/services/ffmpegService.ts"
Task: "建立音訊匯出服務 frontend/src/services/audioExportService.ts"
```

---

## Implementation Strategy

### MVP First (User Story 1 + 2)

1. 完成 Phase 1: Setup
2. 完成 Phase 2: Foundational（**CRITICAL**）
3. 完成 Phase 3: User Story 1（本地上傳處理）
4. 完成 Phase 4: User Story 2（歌曲管理）
5. **STOP and VALIDATE**: 部署到 GitHub Pages 測試純靜態功能
6. 此時已可提供基本可用的服務

### Incremental Delivery

1. Setup + Foundational → 基礎就緒
2. Add US1 + US2 → 部署 GitHub Pages（MVP!）
3. Add US3 → 加入下載功能 → 更新部署
4. Add US4 + Backend → Docker 完整功能 → 完整部署

### Suggested MVP Scope

**最小可行產品 = Phase 1 + Phase 2 + Phase 3 + Phase 4**

功能：本地影片上傳、人聲分離、歌曲管理、即時播放混音
限制：僅支援即時播放，無下載功能
部署：GitHub Pages 純靜態

---

## Notes

- [P] 任務 = 不同檔案，無依賴，可並行
- [Story] 標籤對應 spec.md 中的使用者故事
- 每個使用者故事應可獨立完成和測試
- 每個任務或邏輯群組完成後提交
- 任何 Checkpoint 都可停下來驗證功能
