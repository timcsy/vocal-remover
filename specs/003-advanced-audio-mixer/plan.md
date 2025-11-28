# Implementation Plan: 進階音軌控制功能

**Branch**: `003-advanced-audio-mixer` | **Date**: 2025-11-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-advanced-audio-mixer/spec.md`

## Summary

擴充現有人聲去除服務，支援完整四軌控制（drums, bass, other, vocals）、即時升降 Key（±12 半音）、導唱快速切換、以及多格式下載（MP4/MP3/M4A/WAV）。採用混合架構：前端 Web Audio API 即時預覽，後端 FFmpeg 高品質輸出。

## Technical Context

**Language/Version**: Python 3.11 (後端), TypeScript 5.3 (前端)
**Primary Dependencies**: FastAPI, Vue 3, Demucs, FFmpeg (rubberband), Tone.js
**Storage**: 本地檔案系統 (`/data/`)
**Testing**: pytest (後端), 手動測試 (前端)
**Target Platform**: Linux server (Docker), 現代瀏覽器
**Project Type**: Web application (frontend + backend)
**Performance Goals**: 音頻調整延遲 <100ms, 影片同步誤差 <50ms
**Constraints**: 影片長度 ≤10 分鐘, 記憶體需載入 4 軌音頻
**Scale/Scope**: 單使用者處理，無並發限制

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原則 | 狀態 | 說明 |
|------|------|------|
| I. 繁體中文優先 | ✅ PASS | 規格文件皆使用繁體中文 |
| II. 簡潔設計 | ✅ PASS | 僅實作規格中列出的功能，無預設擴展點 |
| III. 最小文件產出 | ✅ PASS | 僅產出必要的 /specs/ 文件 |
| IV. Git 版本控制紀律 | ✅ PASS | 各階段皆有提交 |
| V. 任務追蹤完整性 | ⏳ N/A | 尚未進入 implement 階段 |
| VI. 規格文件保護 | ✅ PASS | 規格文件完整存在 |

## Project Structure

### Documentation (this feature)

```text
specs/003-advanced-audio-mixer/
├── spec.md              # 功能規格
├── plan.md              # 本文件
├── research.md          # Phase 0 研究結果
├── data-model.md        # Phase 1 資料模型
├── quickstart.md        # Phase 1 快速開始指南
├── contracts/           # Phase 1 API 契約
│   └── api.yaml         # OpenAPI 規格
└── tasks.md             # Phase 2 任務清單 (/speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── api/v1/
│   │   ├── jobs.py          # 修改：新增音軌 API
│   │   └── tracks.py        # 新增：音軌串流端點
│   ├── models/
│   │   └── job.py           # 修改：新增 TrackPaths
│   └── services/
│       ├── separator.py     # 修改：輸出四軌
│       ├── mixer.py         # 新增：混音服務
│       └── processor.py     # 修改：整合混音流程
└── tests/

frontend/
├── src/
│   ├── components/
│   │   ├── AudioMixer/      # 新增目錄
│   │   │   ├── AudioMixer.vue
│   │   │   ├── TrackSlider.vue
│   │   │   └── PitchControl.vue
│   │   └── ResultView.vue   # 修改：整合 AudioMixer
│   ├── composables/
│   │   ├── useWebAudio.ts   # 新增
│   │   └── useAudioSync.ts  # 新增
│   └── services/
│       └── api.ts           # 修改：新增混音 API
└── tests/
```

**Structure Decision**: 維持現有 Web application 結構 (frontend + backend)，在既有目錄中新增模組。

## Complexity Tracking

> 無憲法違規需要說明

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| - | - | - |
