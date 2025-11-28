# 資料模型：進階音軌控制功能

**Date**: 2025-11-28
**Feature**: 003-advanced-audio-mixer

## 實體定義

### 1. TrackPaths（音軌路徑）

擴充 Job 模型，儲存分離後的四軌檔案路徑。

```python
class TrackPaths(BaseModel):
    """分離後的音軌檔案路徑"""
    drums: Optional[str] = None    # 鼓聲軌道路徑
    bass: Optional[str] = None     # 貝斯軌道路徑
    other: Optional[str] = None    # 其他樂器軌道路徑
    vocals: Optional[str] = None   # 人聲軌道路徑
```

### 2. Job（擴充）

在現有 Job 模型中新增欄位：

```python
class Job(BaseModel):
    # ... 現有欄位 ...

    # 新增欄位
    track_paths: Optional[TrackPaths] = None  # 四軌路徑
    sample_rate: Optional[int] = None          # 音頻取樣率
```

### 3. MixSettings（混音設定）

前端發送的混音參數。

```python
class MixSettings(BaseModel):
    """混音設定"""
    drums_volume: float = Field(1.0, ge=0.0, le=2.0)   # 鼓聲音量 (0-200%)
    bass_volume: float = Field(1.0, ge=0.0, le=2.0)    # 貝斯音量
    other_volume: float = Field(1.0, ge=0.0, le=2.0)   # 其他樂器音量
    vocals_volume: float = Field(0.0, ge=0.0, le=2.0)  # 人聲音量（預設關閉）
    pitch_shift: int = Field(0, ge=-12, le=12)         # 升降 Key（半音）
    output_format: OutputFormat = OutputFormat.MP4     # 輸出格式
```

### 4. OutputFormat（輸出格式）

支援的輸出格式列舉。

```python
class OutputFormat(str, Enum):
    """輸出格式"""
    MP4 = "mp4"   # 影片 + 音頻
    MP3 = "mp3"   # 純音頻 (lossy)
    M4A = "m4a"   # 純音頻 (AAC)
    WAV = "wav"   # 純音頻 (lossless)
```

### 5. MixJob（混音任務）

複用 Job 佇列機制的混音任務（不建立新模型，使用現有 Job）。

**新增 JobStatus 狀態：**
```python
class JobStatus(str, Enum):
    # ... 現有狀態 ...
    MIXING = "mixing"  # 新增：混音處理中
```

### 6. MixResponse（混音回應）

混音 API 回應。

```python
class MixResponse(BaseModel):
    """混音產生回應"""
    mix_id: str                    # 混音任務 ID
    status: str                    # 任務狀態
    download_url: Optional[str]    # 下載 URL（完成後填入）
    cached: bool = False           # 是否來自快取
```

---

## 前端型別定義

```typescript
// types/audio.ts

export interface TrackPaths {
  drums: string | null;
  bass: string | null;
  other: string | null;
  vocals: string | null;
}

export interface MixSettings {
  drums_volume: number;    // 0.0 - 2.0
  bass_volume: number;
  other_volume: number;
  vocals_volume: number;
  pitch_shift: number;     // -12 to +12
  output_format: OutputFormat;
}

export type OutputFormat = 'mp4' | 'mp3' | 'm4a' | 'wav';

export interface TracksInfo {
  tracks: string[];        // ['drums', 'bass', 'other', 'vocals']
  sample_rate: number;     // e.g., 44100
  duration: number;        // 秒數
}

export interface MixResponse {
  mix_id: string;
  status: 'processing' | 'completed' | 'failed';
  download_url: string | null;
  cached: boolean;
}
```

---

## 狀態轉換圖

```
Job 狀態流程（擴充）:

PENDING → DOWNLOADING → SEPARATING → COMPLETED
                                ↓
                           (可選) MIXING → COMPLETED
                                   ↓
                               FAILED

注意：
- SEPARATING 完成後直接 COMPLETED（四軌分離完成）
- MIXING 是獨立的混音產生請求（POST /mix 觸發）
```

---

## 檔案儲存結構

```
/data/
├── uploads/
│   └── {job_id}/
│       └── input.mp4              # 原始上傳檔案
├── results/
│   └── {job_id}/
│       ├── drums.wav              # 鼓聲軌道
│       ├── bass.wav               # 貝斯軌道
│       ├── other.wav              # 其他樂器軌道
│       ├── vocals.wav             # 人聲軌道
│       ├── background.wav         # 伴奏（向後相容）
│       └── mixes/                 # 混音快取目錄
│           ├── {hash1}.mp4
│           └── {hash2}.mp3
└── temp/
    └── {job_id}/                  # 處理中的暫存檔案
```

---

## 驗證規則

| 欄位 | 規則 |
|------|------|
| `*_volume` | 0.0 ≤ value ≤ 2.0 |
| `pitch_shift` | -12 ≤ value ≤ 12（整數） |
| `output_format` | mp4, mp3, m4a, wav 其一 |
| `job_id` | 必須存在且狀態為 COMPLETED |
