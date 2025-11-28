/**
 * useJobManager - 全域狀態管理
 *
 * 管理已完成歌曲列表、處理中任務列表、選中狀態、抽屜狀態等
 */
import { ref, computed, readonly, onMounted, onUnmounted } from 'vue'
import { api, type CompletedJob, type ProcessingJob } from '@/services/api'

// 全域狀態（單例模式）
const completedJobs = ref<CompletedJob[]>([])
const processingJobs = ref<ProcessingJob[]>([])
const selectedJobId = ref<string | null>(null)
const drawerOpen = ref(window.innerWidth >= 768) // 桌面版預設開啟
const selectedJobIds = ref<Set<string>>(new Set()) // 勾選的歌曲（用於匯出）
const isPolling = ref(false)
const error = ref<string | null>(null)

let pollIntervalId: number | null = null
const POLL_INTERVAL = 2000 // 2 秒

// 輪詢邏輯
async function fetchJobs() {
  try {
    const response = await api.getJobs()
    completedJobs.value = response.jobs
    processingJobs.value = response.processing
    error.value = null
  } catch (err) {
    error.value = err instanceof Error ? err.message : '載入失敗'
    console.error('Failed to fetch jobs:', err)
  }
}

function startPolling() {
  if (isPolling.value) return
  isPolling.value = true
  fetchJobs() // 立即執行一次
  pollIntervalId = window.setInterval(fetchJobs, POLL_INTERVAL)
}

function stopPolling() {
  if (pollIntervalId !== null) {
    clearInterval(pollIntervalId)
    pollIntervalId = null
  }
  isPolling.value = false
}

// 選取歌曲
function selectJob(jobId: string | null) {
  selectedJobId.value = jobId
}

// 切換抽屜
function toggleDrawer() {
  drawerOpen.value = !drawerOpen.value
}

function setDrawerOpen(open: boolean) {
  drawerOpen.value = open
}

// 勾選/取消勾選歌曲（用於匯出）
function toggleJobSelection(jobId: string) {
  const newSet = new Set(selectedJobIds.value)
  if (newSet.has(jobId)) {
    newSet.delete(jobId)
  } else {
    newSet.add(jobId)
  }
  selectedJobIds.value = newSet
}

function selectAllJobs() {
  selectedJobIds.value = new Set(completedJobs.value.map(j => j.id))
}

function deselectAllJobs() {
  selectedJobIds.value = new Set()
}

// 刪除歌曲
async function deleteJob(jobId: string): Promise<boolean> {
  try {
    await api.deleteJob(jobId)
    // 從列表中移除
    completedJobs.value = completedJobs.value.filter(j => j.id !== jobId)
    processingJobs.value = processingJobs.value.filter(j => j.id !== jobId)
    // 取消選取
    if (selectedJobId.value === jobId) {
      selectedJobId.value = null
    }
    selectedJobIds.value.delete(jobId)
    return true
  } catch (err) {
    console.error('Failed to delete job:', err)
    return false
  }
}

// 手動刷新
async function refreshJobs() {
  await fetchJobs()
}

// 取得選中的歌曲
const selectedJob = computed(() => {
  if (!selectedJobId.value) return null
  return completedJobs.value.find(j => j.id === selectedJobId.value) || null
})

// 是否有處理中任務
const hasProcessingJobs = computed(() => processingJobs.value.length > 0)

// 是否有選中的歌曲（用於匯出）
const hasSelectedJobs = computed(() => selectedJobIds.value.size > 0)

// 選中歌曲數量
const selectedJobCount = computed(() => selectedJobIds.value.size)

export function useJobManager() {
  // 生命週期管理
  onMounted(() => {
    startPolling()
    // 響應式斷點監聽
    const handleResize = () => {
      // 只在視窗寬度變化跨越斷點時調整
      // 不強制覆蓋使用者手動設定的狀態
    }
    window.addEventListener('resize', handleResize)
  })

  onUnmounted(() => {
    stopPolling()
  })

  return {
    // 狀態（唯讀）
    completedJobs: readonly(completedJobs),
    processingJobs: readonly(processingJobs),
    selectedJobId: readonly(selectedJobId),
    drawerOpen: readonly(drawerOpen),
    selectedJobIds: readonly(selectedJobIds),
    isPolling: readonly(isPolling),
    error: readonly(error),

    // 計算屬性
    selectedJob,
    hasProcessingJobs,
    hasSelectedJobs,
    selectedJobCount,

    // 方法
    selectJob,
    toggleDrawer,
    setDrawerOpen,
    toggleJobSelection,
    selectAllJobs,
    deselectAllJobs,
    deleteJob,
    refreshJobs,
    startPolling,
    stopPolling,
  }
}
