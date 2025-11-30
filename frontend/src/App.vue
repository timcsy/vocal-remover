<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useJobManager } from './composables/useJobManager';
import { api, type ImportConflict, type ProcessingJob, checkBackendHealth } from './services/api';
import { browserCheck } from './utils/browserCheck';
import type { BrowserCapabilities, BackendCapabilities } from './types/storage';
import AppDrawer from './components/AppDrawer.vue';
import MainView from './components/MainView.vue';
import AddSongModal from './components/AddSongModal.vue';
import TaskQueue from './components/TaskQueue.vue';
import TaskDetailModal from './components/TaskDetailModal.vue';
import ImportConflictModal from './components/ImportConflictModal.vue';
import BrowserWarning from './components/BrowserWarning.vue';

// 瀏覽器與後端功能狀態
const browserCapabilities = ref<BrowserCapabilities | null>(null);
const backendCapabilities = ref<BackendCapabilities | null>(null);
const isInitialized = ref(false);

// 初始化應用程式
onMounted(async () => {
  // 1. 檢查瀏覽器相容性
  browserCapabilities.value = browserCheck.check();

  // 如果不支援核心功能，不繼續初始化
  if (!browserCheck.isSupported()) {
    return;
  }

  // 2. 偵測後端是否可用
  backendCapabilities.value = await checkBackendHealth();

  // 3. 初始化完成
  isInitialized.value = true;

  // 4. 重新整理任務列表
  refreshJobs();
});

// 全域狀態管理
const {
  completedJobs,
  processingJobs,
  selectedJobId,
  drawerOpen,
  selectedJobIds,
  selectedJob,
  hasProcessingJobs,
  selectJob,
  toggleDrawer,
  setDrawerOpen,
  toggleJobSelection,
  selectAllJobs,
  deselectAllJobs,
  deleteJob,
  refreshJobs,
} = useJobManager();

// 模態視窗狀態
const showAddSongModal = ref(false);
const selectedTaskId = ref<string | null>(null);

// 匯入衝突狀態
const importConflicts = ref<ImportConflict[]>([]);
const currentConflict = ref<ImportConflict | null>(null);

// 處理新增歌曲
function handleAddSong() {
  showAddSongModal.value = true;
}

function handleCloseAddSongModal() {
  showAddSongModal.value = false;
}

function handleJobCreated() {
  showAddSongModal.value = false;
  refreshJobs();
}

// 處理刪除歌曲
async function handleDeleteJob(jobId: string) {
  if (confirm('確定要刪除這首歌曲嗎？')) {
    await deleteJob(jobId);
  }
}

// 處理匯出
async function handleExport() {
  const jobIds = Array.from(selectedJobIds.value);
  if (jobIds.length === 0) {
    return;
  }

  try {
    const response = await api.exportJobs(jobIds);
    // 開啟下載連結
    window.open(response.download_url, '_blank');
  } catch (error) {
    console.error('Export failed:', error);
    alert('匯出失敗，請稍後再試');
  }
}

// 處理匯入
async function handleImport() {
  // 開啟檔案選擇器
  const input = document.createElement('input');
  input.type = 'file';
  input.accept = '.zip';

  input.onchange = async (e) => {
    const file = (e.target as HTMLInputElement).files?.[0];
    if (!file) return;

    try {
      const response = await api.importJobs(file);

      // 顯示匯入結果
      if (response.imported.length > 0) {
        refreshJobs();
      }

      if (response.errors.length > 0) {
        alert('部分匯入失敗:\n' + response.errors.join('\n'));
      }

      // 處理衝突
      if (response.conflicts.length > 0) {
        importConflicts.value = response.conflicts;
        currentConflict.value = importConflicts.value[0];
      }
    } catch (error) {
      console.error('Import failed:', error);
      alert('匯入失敗，請確認檔案格式正確');
    }
  };

  input.click();
}

// 處理衝突解決
async function handleResolveConflict(action: string, newTitle?: string) {
  if (!currentConflict.value) return;

  try {
    const response = await api.resolveImportConflict(
      currentConflict.value.conflict_id,
      action as 'overwrite' | 'rename',
      newTitle
    );

    if (response.error) {
      alert(response.error);
      return;
    }

    // 移除已解決的衝突
    importConflicts.value = importConflicts.value.filter(
      c => c.conflict_id !== currentConflict.value?.conflict_id
    );

    // 處理下一個衝突或關閉
    if (importConflicts.value.length > 0) {
      currentConflict.value = importConflicts.value[0];
    } else {
      currentConflict.value = null;
    }

    // 重新整理列表
    refreshJobs();
  } catch (error) {
    console.error('Resolve conflict failed:', error);
    alert('解決衝突失敗，請稍後再試');
  }
}

// 關閉衝突模態視窗
function handleCloseConflictModal() {
  // 取消所有剩餘衝突
  currentConflict.value = null;
  importConflicts.value = [];
}

// 任務詳情
const selectedTask = computed<ProcessingJob | null>(() => {
  if (!selectedTaskId.value) return null;
  return processingJobs.value.find(job => job.id === selectedTaskId.value) || null;
});

function handleTaskClick(jobId: string) {
  selectedTaskId.value = jobId;
}

function handleCloseTaskDetail() {
  selectedTaskId.value = null;
}
</script>

<template>
  <div class="app">
    <!-- 瀏覽器相容性警告元件 -->
    <BrowserWarning
      v-if="browserCapabilities"
      :capabilities="browserCapabilities"
    />

    <!-- 主應用內容（僅在初始化完成後顯示） -->
    <template v-if="isInitialized">
      <!-- 左側抽屜 -->
      <AppDrawer
      :isOpen="drawerOpen"
      :jobs="completedJobs"
      :selectedJobId="selectedJobId"
      :selectedJobIds="selectedJobIds"
      @close="setDrawerOpen(false)"
      @select="selectJob"
      @toggle="toggleJobSelection"
      @delete="handleDeleteJob"
      @selectAll="selectAllJobs"
      @deselectAll="deselectAllJobs"
      @addSong="handleAddSong"
      @export="handleExport"
      @import="handleImport"
    />

    <!-- 主內容區 -->
    <MainView
      :selectedJob="selectedJob"
      :drawerOpen="drawerOpen"
      @toggleDrawer="toggleDrawer"
      @addSong="handleAddSong"
    />

    <!-- 底部任務佇列 -->
    <TaskQueue
      v-if="hasProcessingJobs"
      :jobs="processingJobs"
      :drawerOpen="drawerOpen"
      @taskClick="handleTaskClick"
    />

    <!-- 新增歌曲模態視窗 -->
    <AddSongModal
      v-if="showAddSongModal"
      @close="handleCloseAddSongModal"
      @created="handleJobCreated"
    />

    <!-- 匯入衝突模態視窗 -->
    <ImportConflictModal
      v-if="currentConflict"
      :conflict="currentConflict"
      @close="handleCloseConflictModal"
      @resolve="handleResolveConflict"
    />

    <!-- 任務詳情模態視窗 -->
    <TaskDetailModal
      v-if="selectedTask"
      :job="selectedTask"
      @close="handleCloseTaskDetail"
    />
    </template>

    <!-- 載入中畫面（僅當瀏覽器支援且尚未初始化時顯示） -->
    <div v-if="!isInitialized && browserCapabilities?.sharedArrayBuffer && browserCapabilities?.indexedDB" class="loading">
      <div class="loading-spinner"></div>
      <p>正在初始化...</p>
    </div>
  </div>
</template>

<style>
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #121212;
  color: #e0e0e0;
  min-height: 100vh;
}

.app {
  min-height: 100vh;
}

/* 載入中 */
.loading {
  position: fixed;
  inset: 0;
  background: #121212;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #333;
  border-top-color: #1db954;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
