/**
 * useLocalProcessor Composable Unit Tests
 * TDD: 先寫測試，確保測試 FAIL 後再實作
 */
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'

// Mock services
vi.mock('@/services/ffmpegService', () => ({
  ffmpegService: {
    initialize: vi.fn().mockResolvedValue(undefined),
    isLoaded: vi.fn().mockReturnValue(true),
    extractAudio: vi.fn().mockResolvedValue(new ArrayBuffer(1024)),
  },
}))

vi.mock('@/services/demucsService', () => ({
  demucsService: {
    initialize: vi.fn().mockResolvedValue(undefined),
    isLoaded: vi.fn().mockReturnValue(true),
    separate: vi.fn().mockResolvedValue({
      drums: { left: new Float32Array(1024), right: new Float32Array(1024) },
      bass: { left: new Float32Array(1024), right: new Float32Array(1024) },
      other: { left: new Float32Array(1024), right: new Float32Array(1024) },
      vocals: { left: new Float32Array(1024), right: new Float32Array(1024) },
    }),
    stereoToArrayBuffer: vi.fn().mockReturnValue(new ArrayBuffer(2048)),
  },
}))

vi.mock('@/services/storageService', () => ({
  storageService: {
    init: vi.fn().mockResolvedValue(undefined),
    saveSong: vi.fn().mockResolvedValue(undefined),
    getSong: vi.fn().mockResolvedValue(null),
    getAllSongs: vi.fn().mockResolvedValue([]),
    deleteSong: vi.fn().mockResolvedValue(undefined),
  },
}))

describe('useLocalProcessor', () => {
  beforeEach(() => {
    vi.resetModules()
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  describe('processUpload()', () => {
    it('應該成功處理上傳的影片檔案', async () => {
      const { useLocalProcessor } = await import('@/composables/useLocalProcessor')
      const { processUpload, state } = useLocalProcessor()

      // 建立假的影片檔案
      const mockFile = new File(['video content'], 'test.mp4', { type: 'video/mp4' })

      // Act
      const songId = await processUpload(mockFile, '測試歌曲')

      // Assert
      expect(songId).toBeDefined()
      expect(typeof songId).toBe('string')
      expect(state.value.stage).toBe('idle')
      expect(state.value.songId).toBe(songId)
    })

    it('應該依序更新處理階段', async () => {
      const { useLocalProcessor } = await import('@/composables/useLocalProcessor')
      const { processUpload, state } = useLocalProcessor()

      const stages: string[] = []

      // 監聽狀態變化
      const mockFile = new File(['video content'], 'test.mp4', { type: 'video/mp4' })

      // 使用 onProgress callback 追蹤階段
      const processPromise = processUpload(mockFile, '測試歌曲', {
        onProgress: (s) => {
          if (!stages.includes(s.stage)) {
            stages.push(s.stage)
          }
        },
      })

      await processPromise

      // 應該經過這些階段：extracting → separating → saving → idle
      expect(stages).toContain('extracting')
      expect(stages).toContain('separating')
      expect(stages).toContain('saving')
    })

    it('應該在處理失敗時設定錯誤訊息', async () => {
      // 模擬 ffmpeg 失敗
      const ffmpegMock = await import('@/services/ffmpegService')
      vi.mocked(ffmpegMock.ffmpegService.extractAudio).mockRejectedValueOnce(
        new Error('音頻提取失敗')
      )

      const { useLocalProcessor } = await import('@/composables/useLocalProcessor')
      const { processUpload, state } = useLocalProcessor()

      const mockFile = new File(['video content'], 'test.mp4', { type: 'video/mp4' })

      await expect(processUpload(mockFile, '測試歌曲')).rejects.toThrow()

      expect(state.value.error).toBeTruthy()
    })
  })

  describe('cancel()', () => {
    it('應該取消處理並重設狀態', async () => {
      const { useLocalProcessor } = await import('@/composables/useLocalProcessor')
      const { cancel, state } = useLocalProcessor()

      // 模擬處理中狀態
      state.value.stage = 'separating'
      state.value.progress = 50

      // Act
      cancel()

      // Assert
      expect(state.value.stage).toBe('idle')
      expect(state.value.progress).toBe(0)
      expect(state.value.error).toBeNull()
    })
  })

  describe('state', () => {
    it('應該有正確的初始狀態', async () => {
      const { useLocalProcessor } = await import('@/composables/useLocalProcessor')
      const { state } = useLocalProcessor()

      expect(state.value.stage).toBe('idle')
      expect(state.value.progress).toBe(0)
      expect(state.value.error).toBeNull()
      expect(state.value.songId).toBeUndefined()
    })
  })
})
