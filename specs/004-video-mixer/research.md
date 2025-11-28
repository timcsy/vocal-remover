# Research: Video Mixer 影片混音器

## 研究項目

### 1. Python ZIP 檔案處理

**Decision**: 使用 Python 標準庫 `zipfile` 模組

**Rationale**:
- 無需額外依賴，已內建於 Python
- 支援讀取和寫入 ZIP 檔案
- 支援串流處理大檔案
- 既有專案已使用標準庫處理檔案操作

**Alternatives considered**:
- `shutil.make_archive`: 較簡單但彈性不足，無法自訂 ZIP 內部結構
- `py7zr`: 支援 7z 格式但非標準 ZIP，增加不必要複雜度

### 2. 前端全域狀態管理

**Decision**: 使用 Vue 3 Composition API 搭配 `reactive` 和 `provide/inject`

**Rationale**:
- 既有專案使用 Vue 3 Composition API
- 無需引入額外狀態管理庫（如 Pinia、Vuex）
- 符合憲法原則 II（簡潔設計）
- `useJobManager.ts` composable 可以提供全域單例狀態

**Alternatives considered**:
- Pinia: 功能強大但對此規模專案過度設計
- Vuex: Vue 3 已推薦改用 Pinia，且同樣過度設計
- Event Bus: 難以追蹤狀態變化，不推薦

### 3. 左側抽屜動畫實作

**Decision**: 使用 CSS `transform: translateX()` + `transition`

**Rationale**:
- 規格中 Assumptions 已指定使用 CSS transform
- GPU 加速，效能優於修改 `left` 或 `margin`
- 簡單且瀏覽器支援度高

**Implementation pattern**:
```css
.drawer {
  position: fixed;
  left: 0;
  top: 0;
  width: 300px;
  height: 100vh;
  transform: translateX(-100%);
  transition: transform 0.3s ease;
}
.drawer.open {
  transform: translateX(0);
}
```

### 4. 任務佇列輪詢機制

**Decision**: 使用 `setInterval` 搭配 2 秒間隔輪詢

**Rationale**:
- 規格 FR-006 要求每 2 秒更新一次
- 規格 Assumptions 已排除 WebSocket
- 簡單可靠，易於實作和除錯

**Implementation pattern**:
```typescript
const pollInterval = setInterval(async () => {
  const response = await api.getJobs();
  completedJobs.value = response.jobs;
  processingJobs.value = response.processing;
}, 2000);
```

### 5. 匯出 ZIP 檔案結構

**Decision**: 採用規格定義的巢狀 ZIP 結構

**Rationale**:
- 規格已明確定義單首和多首歌曲的 ZIP 格式
- 單首歌曲包含：4 軌 WAV、原始影片、metadata.json
- 多首歌曲為多個單首 ZIP 的集合

**Single song ZIP structure**:
```
{source_title}.zip
├── drums.wav
├── bass.wav
├── other.wav
├── vocals.wav
├── video.mp4
└── metadata.json
```

**Multiple songs ZIP structure**:
```
export_YYYYMMDD.zip
├── 歌曲A.zip
├── 歌曲B.zip
└── 歌曲C.zip
```

### 6. 匯入名稱衝突處理

**Decision**: 彈出確認視窗讓使用者選擇覆蓋或重新命名

**Rationale**:
- Clarifications Session 2025-01-28 已明確決定
- 給予使用者控制權，避免意外資料遺失
- 前端實作 `ImportConflictModal.vue` 組件

### 7. 響應式設計斷點

**Decision**: 768px 作為桌面/手機斷點

**Rationale**:
- 行業標準斷點
- 規格要求桌面版預設開啟抽屜，手機版預設收合
- 使用 CSS media query 判斷

**Implementation**:
```css
@media (max-width: 768px) {
  .drawer { transform: translateX(-100%); }
}
@media (min-width: 769px) {
  .drawer { transform: translateX(0); }
}
```

## 技術決策摘要

| 項目 | 決策 | 理由 |
|------|------|------|
| ZIP 處理 | Python zipfile | 標準庫，無額外依賴 |
| 狀態管理 | Vue Composition API | 簡潔，符合既有架構 |
| 抽屜動畫 | CSS transform | GPU 加速，規格指定 |
| 輪詢機制 | setInterval 2秒 | 規格要求，簡單可靠 |
| ZIP 結構 | 巢狀 ZIP | 規格定義 |
| 名稱衝突 | 使用者確認 | Clarifications 決定 |
| 響應式斷點 | 768px | 行業標準 |

## 無需進一步研究的項目

- FastAPI 路由：既有專案已有完整範例
- Vue 組件：既有專案已有組件模式
- 檔案上傳：既有 `/jobs/upload` 端點可參考
- 音頻串流：既有 `/jobs/{id}/tracks/{track}` 端點可參考
