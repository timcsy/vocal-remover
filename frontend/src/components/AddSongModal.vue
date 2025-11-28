<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal">
      <div class="modal-header">
        <h2>新增歌曲</h2>
        <button class="close-btn" @click="$emit('close')">×</button>
      </div>

      <div class="modal-body">
        <div v-if="error" class="error-message">
          {{ error }}
          <button @click="error = null">×</button>
        </div>

        <div class="input-tabs">
          <button
            class="tab"
            :class="{ active: activeTab === 'url' }"
            @click="switchTab('url')"
          >
            YouTube 網址
          </button>
          <button
            class="tab"
            :class="{ active: activeTab === 'upload' }"
            @click="switchTab('upload')"
          >
            上傳檔案
          </button>
        </div>

        <div class="tab-content">
          <!-- YouTube URL 輸入 -->
          <div v-if="activeTab === 'url'" class="url-input">
            <input
              v-model="youtubeUrl"
              type="text"
              placeholder="貼上 YouTube 網址..."
              :disabled="isSubmitting"
              @input="onUrlInput"
              @paste="onUrlPaste"
              @keyup.enter="submitUrl"
            />

            <!-- YouTube 預覽 -->
            <div v-if="youtubePreview" class="preview-card">
              <div class="video-container">
                <iframe
                  :src="`https://www.youtube.com/embed/${youtubePreview.videoId}`"
                  frameborder="0"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowfullscreen
                ></iframe>
              </div>
              <div class="preview-info">
                <p class="preview-title">{{ youtubePreview.title }}</p>
              </div>
            </div>

            <button
              class="submit-btn"
              :disabled="!youtubeUrl || isSubmitting"
              @click="submitUrl"
            >
              {{ isSubmitting ? '處理中...' : '開始處理' }}
            </button>
          </div>

          <!-- 檔案上傳 -->
          <div v-else class="file-upload">
            <div
              v-if="!selectedFile"
              class="drop-zone"
              :class="{ dragover: isDragging }"
              @dragover.prevent="isDragging = true"
              @dragleave="isDragging = false"
              @drop.prevent="handleDrop"
            >
              <input
                ref="fileInput"
                type="file"
                accept=".mp4,.mov,.avi,.mkv,.webm"
                @change="handleFileSelect"
                style="display: none"
              />
              <p>
                拖放影片檔案到這裡<br>
                或 <button class="link-btn" @click="fileInput?.click()">選擇檔案</button>
              </p>
            </div>

            <!-- 檔案預覽 -->
            <div v-else class="file-preview">
              <video
                ref="videoPreview"
                :src="filePreviewUrl"
                class="preview-video"
                controls
                muted
              ></video>
              <div class="file-info">
                <p class="file-name">{{ selectedFile.name }}</p>
                <p class="file-size">{{ formatFileSize(selectedFile.size) }}</p>
                <button class="link-btn remove-btn" @click="clearFile">移除</button>
              </div>
            </div>

            <button
              class="submit-btn"
              :disabled="!selectedFile || isSubmitting"
              @click="submitFile"
            >
              {{ isSubmitting ? '上傳中...' : '開始處理' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from 'vue'
import { api } from '@/services/api'

const emit = defineEmits<{
  close: []
  created: []
}>()

const activeTab = ref<'url' | 'upload'>('url')
const youtubeUrl = ref('')
const selectedFile = ref<File | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)
const videoPreview = ref<HTMLVideoElement | null>(null)
const isSubmitting = ref(false)
const error = ref<string | null>(null)
const isDragging = ref(false)

// YouTube 預覽
interface YouTubePreview {
  title: string
  thumbnail: string
  videoId: string
}
const youtubePreview = ref<YouTubePreview | null>(null)
let urlDebounceTimer: number | null = null

// 檔案預覽 URL
const filePreviewUrl = computed(() => {
  if (selectedFile.value) {
    return URL.createObjectURL(selectedFile.value)
  }
  return ''
})

// 清理 blob URL
watch(selectedFile, (newFile, oldFile) => {
  if (oldFile && !newFile) {
    // 檔案被清除時釋放舊的 blob URL
  }
})

onUnmounted(() => {
  if (filePreviewUrl.value) {
    URL.revokeObjectURL(filePreviewUrl.value)
  }
})

// 從 YouTube URL 解析影片 ID
function extractVideoId(url: string): string | null {
  const patterns = [
    /(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)/,
    /youtube\.com\/shorts\/([^&\n?#]+)/,
  ]
  for (const pattern of patterns) {
    const match = url.match(pattern)
    if (match) return match[1]
  }
  return null
}

// URL 輸入防抖處理
function onUrlInput() {
  if (urlDebounceTimer) {
    clearTimeout(urlDebounceTimer)
  }
  urlDebounceTimer = window.setTimeout(() => {
    updateYoutubePreview()
  }, 500)
}

// 貼上時立即更新預覽
function onUrlPaste(event: ClipboardEvent) {
  const pastedText = event.clipboardData?.getData('text')
  if (pastedText) {
    // 使用 nextTick 確保 v-model 已更新
    setTimeout(() => {
      if (urlDebounceTimer) {
        clearTimeout(urlDebounceTimer)
      }
      updateYoutubePreview()
    }, 0)
  }
}

// 更新 YouTube 預覽
function updateYoutubePreview() {
  const videoId = extractVideoId(youtubeUrl.value)
  if (videoId) {
    youtubePreview.value = {
      videoId,
      thumbnail: `https://img.youtube.com/vi/${videoId}/mqdefault.jpg`,
      title: '載入中...',
    }
    // 使用 noembed 取得標題（免費、無需 API key）
    fetch(`https://noembed.com/embed?url=https://www.youtube.com/watch?v=${videoId}`)
      .then(res => res.json())
      .then(data => {
        if (youtubePreview.value && youtubePreview.value.videoId === videoId) {
          youtubePreview.value.title = data.title || '未知標題'
        }
      })
      .catch(() => {
        if (youtubePreview.value && youtubePreview.value.videoId === videoId) {
          youtubePreview.value.title = 'YouTube 影片'
        }
      })
  } else {
    youtubePreview.value = null
  }
}

// 切換 tab
function switchTab(tab: 'url' | 'upload') {
  activeTab.value = tab
  error.value = null
}

// 清除檔案
function clearFile() {
  if (filePreviewUrl.value) {
    URL.revokeObjectURL(filePreviewUrl.value)
  }
  selectedFile.value = null
}

// 格式化檔案大小
function formatFileSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  return (bytes / (1024 * 1024 * 1024)).toFixed(1) + ' GB'
}

async function submitUrl() {
  if (!youtubeUrl.value || isSubmitting.value) return

  isSubmitting.value = true
  error.value = null

  try {
    await api.createJobFromUrl(youtubeUrl.value)
    emit('created')
  } catch (e: any) {
    error.value = e.message || '建立任務失敗'
  } finally {
    isSubmitting.value = false
  }
}

async function submitFile() {
  if (!selectedFile.value || isSubmitting.value) return

  isSubmitting.value = true
  error.value = null

  try {
    await api.createJobFromUpload(selectedFile.value)
    emit('created')
  } catch (e: any) {
    error.value = e.message || '上傳失敗'
  } finally {
    isSubmitting.value = false
  }
}

function handleFileSelect(event: Event) {
  const input = event.target as HTMLInputElement
  if (input.files && input.files[0]) {
    selectedFile.value = input.files[0]
  }
}

function handleDrop(event: DragEvent) {
  isDragging.value = false
  if (event.dataTransfer?.files && event.dataTransfer.files[0]) {
    selectedFile.value = event.dataTransfer.files[0]
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
}

.modal {
  background: #1e1e1e;
  border-radius: 8px;
  width: 90%;
  max-width: 500px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #333;
}

.modal-header h2 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 500;
}

.close-btn {
  background: transparent;
  border: none;
  color: #888;
  font-size: 1.5rem;
  cursor: pointer;
  padding: 0.25rem 0.5rem;
  line-height: 1;
}

.close-btn:hover {
  color: #fff;
}

.modal-body {
  padding: 1.5rem;
}

.error-message {
  background: #3d1a1a;
  color: #ff6b6b;
  padding: 0.75rem 1rem;
  border-radius: 4px;
  margin-bottom: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.error-message button {
  background: transparent;
  border: none;
  color: #ff6b6b;
  cursor: pointer;
  font-size: 1rem;
}

.input-tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.tab {
  flex: 1;
  padding: 0.75rem;
  background: #2a2a2a;
  border: none;
  border-radius: 4px;
  color: #888;
  cursor: pointer;
  transition: all 0.15s;
}

.tab.active {
  background: #3a3a3a;
  color: #e0e0e0;
}

.tab:hover:not(.active) {
  background: #333;
}

.url-input {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.url-input input {
  padding: 0.75rem 1rem;
  background: #2a2a2a;
  border: 1px solid #333;
  border-radius: 4px;
  color: #e0e0e0;
  font-size: 0.9rem;
}

.url-input input:focus {
  outline: none;
  border-color: #4a9eff;
}

.file-upload {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.drop-zone {
  padding: 2rem;
  border: 2px dashed #333;
  border-radius: 8px;
  text-align: center;
  color: #888;
  transition: all 0.15s;
}

.drop-zone.dragover {
  border-color: #4a9eff;
  background: rgba(74, 158, 255, 0.1);
}

.link-btn {
  background: transparent;
  border: none;
  color: #4a9eff;
  cursor: pointer;
  text-decoration: underline;
}

.submit-btn {
  padding: 0.75rem 1.5rem;
  background: #4a9eff;
  border: none;
  border-radius: 4px;
  color: #fff;
  cursor: pointer;
  font-size: 0.9rem;
  transition: background-color 0.15s;
}

.submit-btn:hover:not(:disabled) {
  background: #3a8eef;
}

.submit-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* YouTube 預覽 */
.preview-card {
  background: #2a2a2a;
  border-radius: 8px;
  overflow: hidden;
}

.video-container {
  position: relative;
  width: 100%;
  padding-bottom: 56.25%; /* 16:9 */
}

.video-container iframe {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.preview-info {
  padding: 0.75rem 1rem;
}

.preview-title {
  font-size: 0.85rem;
  color: #e0e0e0;
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: 1.4;
}

/* 檔案預覽 */
.file-preview {
  background: #2a2a2a;
  border-radius: 8px;
  overflow: hidden;
}

.preview-video {
  width: 100%;
  max-height: 200px;
  background: #000;
  display: block;
}

.file-info {
  padding: 0.75rem 1rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.file-name {
  font-size: 0.85rem;
  color: #e0e0e0;
  margin: 0;
  flex: 1;
  min-width: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-size {
  font-size: 0.75rem;
  color: #888;
  margin: 0;
}

.remove-btn {
  font-size: 0.8rem;
}
</style>
