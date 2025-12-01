/**
 * 應用程式設定服務
 * 管理 WebGPU 等使用者偏好設定
 */

const STORAGE_KEY = 'song-mixer-settings'

export interface AppSettings {
  /** 是否啟用 WebGPU（預設：桌面開啟、行動裝置關閉） */
  useWebGPU: boolean
}

/**
 * 檢查是否為行動裝置
 */
export function isMobileDevice(): boolean {
  // 使用 User Agent 偵測
  const userAgent = navigator.userAgent || navigator.vendor || (window as any).opera

  // 檢查常見的行動裝置標識
  const mobileRegex = /android|webos|iphone|ipad|ipod|blackberry|iemobile|opera mini|mobile|tablet/i

  // 也檢查螢幕寬度（小於 768px 視為行動裝置）
  const isSmallScreen = window.innerWidth < 768

  // 檢查觸控支援
  const hasTouch = 'ontouchstart' in window || navigator.maxTouchPoints > 0

  return mobileRegex.test(userAgent.toLowerCase()) || (isSmallScreen && hasTouch)
}

/**
 * 檢查瀏覽器是否支援 WebGPU
 */
export function isWebGPUSupported(): boolean {
  return typeof navigator !== 'undefined' && 'gpu' in navigator
}

/**
 * 取得預設設定
 */
function getDefaultSettings(): AppSettings {
  return {
    // 桌面預設開啟 WebGPU，行動裝置預設關閉
    useWebGPU: isWebGPUSupported() && !isMobileDevice(),
  }
}

/**
 * 設定服務
 */
class SettingsService {
  private settings: AppSettings

  constructor() {
    this.settings = this.loadSettings()
  }

  /**
   * 從 localStorage 載入設定
   */
  private loadSettings(): AppSettings {
    try {
      const saved = localStorage.getItem(STORAGE_KEY)
      if (saved) {
        const parsed = JSON.parse(saved)
        // 合併預設設定以處理新增的設定項目
        return { ...getDefaultSettings(), ...parsed }
      }
    } catch (err) {
      console.warn('Failed to load settings:', err)
    }
    return getDefaultSettings()
  }

  /**
   * 儲存設定到 localStorage
   */
  private saveSettings(): void {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(this.settings))
    } catch (err) {
      console.warn('Failed to save settings:', err)
    }
  }

  /**
   * 取得所有設定
   */
  getSettings(): Readonly<AppSettings> {
    return { ...this.settings }
  }

  /**
   * 取得 WebGPU 設定
   */
  getUseWebGPU(): boolean {
    // 如果瀏覽器不支援 WebGPU，永遠回傳 false
    if (!isWebGPUSupported()) {
      return false
    }
    return this.settings.useWebGPU
  }

  /**
   * 設定 WebGPU 開關
   */
  setUseWebGPU(value: boolean): void {
    this.settings.useWebGPU = value
    this.saveSettings()
  }

  /**
   * 重設為預設設定
   */
  resetToDefaults(): void {
    this.settings = getDefaultSettings()
    this.saveSettings()
  }
}

export const settingsService = new SettingsService()
export default settingsService
