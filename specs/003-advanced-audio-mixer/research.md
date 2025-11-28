# 研究筆記：進階音軌控制功能

**Date**: 2025-11-28
**Feature**: 003-advanced-audio-mixer

## 1. 前端即時 Pitch Shift (Tone.js)

### 決策
使用 Tone.js PitchShift 效果器進行前端即時音高調整。

### 理由
- 成熟穩定的 Web Audio API 封裝
- 支援多音源同時處理
- 內建視窗大小調整以平衡延遲與品質

### 實作要點

```typescript
// 建立 PitchShift 效果器
const pitchShift = new Tone.PitchShift({
  pitch: 0,           // 半音數 (-12 to +12)
  windowSize: 0.1,    // 0.03-0.1 秒（較小=較低延遲）
}).toDestination();

// 多音軌連接
const drums = new Tone.Player(drumsUrl);
const bass = new Tone.Player(bassUrl);
drums.connect(pitchShift);
bass.connect(pitchShift);

// 音量控制使用 GainNode
const drumsGain = new Tone.Gain(1.0);
drums.connect(drumsGain).connect(pitchShift);
```

### 影片同步策略
- PitchShift 會產生 40-100ms 延遲
- 使用 `Tone.Draw` 進行 UI 同步，避免直接在 Transport 回調中操作 DOM
- 每秒校正一次音頻與影片時間

### 效能注意事項
- 設定 `latencyHint: "playback"` 優化吞吐量
- 避免在音頻回調中操作 DOM
- 行動裝置需測試大檔案記憶體用量

### 替代方案（已排除）
- 原生 Web Audio API：需自行實作，複雜度高
- SoundTouch.js：較舊，維護較少

---

## 2. 後端混音 Pitch Shift (FFmpeg rubberband)

### 決策
使用 FFmpeg rubberband filter 進行高品質離線音高調整。

### 理由
- 保持原始播放速度（僅改變音高）
- 支援 formant 保留，人聲更自然
- FFmpeg 已內建，無需額外安裝

### Pitch 值計算公式
```
pitch_value = 2^(semitones/12)
```

| 半音數 | pitch 值 |
|--------|----------|
| +1 | 1.059463 |
| +2 | 1.122462 |
| +5 | 1.334840 |
| +12 | 2.0 |
| -1 | 0.943874 |
| -3 | 0.890899 |
| -12 | 0.5 |

### FFmpeg 指令範例

**四軌混音 + Pitch Shift + 輸出 MP4：**
```bash
ffmpeg -i original_video.mp4 \
  -i drums.wav -i bass.wav -i other.wav -i vocals.wav \
  -filter_complex "
    [1:a]volume=1.0[d];
    [2:a]volume=1.0[b];
    [3:a]volume=1.0[o];
    [4:a]volume=0.0[v];
    [d][b][o][v]amix=inputs=4:normalize=0[mixed];
    [mixed]rubberband=pitch=1.122462[final]
  " \
  -map 0:v -map "[final]" \
  -c:v copy -c:a aac -b:a 256k output.mp4
```

**純音頻輸出 (MP3)：**
```bash
ffmpeg -i drums.wav -i bass.wav -i other.wav -i vocals.wav \
  -filter_complex "
    [0:a]volume=1.0[d];
    [1:a]volume=1.0[b];
    [2:a]volume=1.0[o];
    [3:a]volume=0.0[v];
    [d][b][o][v]amix=inputs=4:normalize=0[mixed];
    [mixed]rubberband=pitch=1.122462[final]
  " \
  -map "[final]" -c:a libmp3lame -b:a 320k output.mp3
```

### 輸出格式設定

| 格式 | FFmpeg 參數 |
|------|-------------|
| MP4 | `-c:v copy -c:a aac -b:a 256k` |
| MP3 | `-c:a libmp3lame -b:a 320k` |
| M4A | `-c:a aac -b:a 256k` |
| WAV | `-c:a pcm_s16le -ar 44100` |

### 替代方案（已排除）
- SoX：功能強大但需額外安裝
- Python librosa：較慢，不適合大檔案

---

## 3. 音軌串流載入

### 決策
使用 Web Audio API + HTTP Range Request 實現漸進式載入。

### 理由
- 不需等待完整檔案下載
- 減少初始載入時間
- 與 Tone.js 相容

### 實作要點
- 後端 API 需支援 HTTP Range headers
- 前端使用 `fetch` + `AudioContext.decodeAudioData`
- 大檔案分段載入，每段約 5-10 秒

---

## 4. 混音快取策略

### 決策
以混音設定雜湊值作為快取索引。

### 雜湊計算
```python
import hashlib
import json

def get_mix_cache_key(job_id: str, settings: dict) -> str:
    """產生混音快取鍵"""
    settings_str = json.dumps(settings, sort_keys=True)
    hash_input = f"{job_id}:{settings_str}"
    return hashlib.md5(hash_input.encode()).hexdigest()[:16]
```

### 快取檔案結構
```
/data/results/{job_id}/
├── drums.wav
├── bass.wav
├── other.wav
├── vocals.wav
└── mixes/
    ├── {hash1}.mp4
    └── {hash2}.mp3
```

---

## 5. Docker 相容性

### 確認事項
- FFmpeg 已包含 librubberband（現有 Dockerfile 需確認）
- 若無，需新增：`apt-get install librubberband-dev`

### Dockerfile 更新
```dockerfile
RUN apt-get update && apt-get install -y \
    ffmpeg \
    librubberband-dev \
    && rm -rf /var/lib/apt/lists/*
```
