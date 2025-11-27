<script setup lang="ts">
import { ref } from 'vue';
import { api, type Job, type ApiError } from '../services/api';

const emit = defineEmits<{
  (e: 'jobCreated', job: Job): void;
  (e: 'error', message: string): void;
}>();

const isDragging = ref(false);
const isLoading = ref(false);
const selectedFile = ref<File | null>(null);

const allowedTypes = ['video/mp4', 'video/quicktime', 'video/x-msvideo', 'video/x-matroska', 'video/webm'];
const allowedExtensions = ['.mp4', '.mov', '.avi', '.mkv', '.webm'];
const maxSize = 500 * 1024 * 1024; // 500MB

function isValidFile(file: File): boolean {
  // 檢查類型
  const ext = '.' + file.name.split('.').pop()?.toLowerCase();
  if (!allowedExtensions.includes(ext)) {
    return false;
  }
  // 檢查大小
  if (file.size > maxSize) {
    return false;
  }
  return true;
}

function handleDragOver(e: DragEvent) {
  e.preventDefault();
  isDragging.value = true;
}

function handleDragLeave(e: DragEvent) {
  e.preventDefault();
  isDragging.value = false;
}

function handleDrop(e: DragEvent) {
  e.preventDefault();
  isDragging.value = false;

  const files = e.dataTransfer?.files;
  if (files && files.length > 0) {
    handleFile(files[0]);
  }
}

function handleFileSelect(e: Event) {
  const input = e.target as HTMLInputElement;
  if (input.files && input.files.length > 0) {
    handleFile(input.files[0]);
  }
}

function handleFile(file: File) {
  if (!isValidFile(file)) {
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!allowedExtensions.includes(ext)) {
      emit('error', `不支援的檔案格式，支援: ${allowedExtensions.join(', ')}`);
    } else {
      emit('error', `檔案大小超過限制 (${maxSize / (1024 * 1024)}MB)`);
    }
    return;
  }
  selectedFile.value = file;
}

function clearFile() {
  selectedFile.value = null;
}

async function submit() {
  if (!selectedFile.value) return;

  isLoading.value = true;

  try {
    const job = await api.createJobFromUpload(selectedFile.value);
    selectedFile.value = null;
    emit('jobCreated', job);
  } catch (error) {
    const apiError = error as ApiError;
    emit('error', apiError.message || '上傳失敗');
  } finally {
    isLoading.value = false;
  }
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
</script>

<template>
  <div class="file-upload">
    <h2>上傳影片</h2>
    <p class="description">上傳本地影片檔案，自動去除人聲</p>

    <!-- 拖放區域 -->
    <div
      v-if="!selectedFile"
      class="drop-zone"
      :class="{ dragging: isDragging }"
      @dragover="handleDragOver"
      @dragleave="handleDragLeave"
      @drop="handleDrop"
      @click="($refs.fileInput as HTMLInputElement).click()"
    >
      <div class="drop-content">
        <span class="drop-icon">📁</span>
        <p>拖放影片檔案到這裡</p>
        <p class="drop-hint">或點擊選擇檔案</p>
        <p class="drop-formats">支援 MP4、MOV、AVI、MKV、WebM（最大 500MB）</p>
      </div>
    </div>

    <!-- 已選擇檔案 -->
    <div v-else class="selected-file">
      <div class="file-info">
        <span class="file-icon">🎬</span>
        <div class="file-details">
          <p class="file-name">{{ selectedFile.name }}</p>
          <p class="file-size">{{ formatSize(selectedFile.size) }}</p>
        </div>
        <button @click="clearFile" class="clear-btn" :disabled="isLoading">✕</button>
      </div>
      <button
        @click="submit"
        :disabled="isLoading"
        class="submit-btn"
      >
        {{ isLoading ? '上傳中...' : '開始處理' }}
      </button>
    </div>

    <input
      ref="fileInput"
      type="file"
      :accept="allowedExtensions.join(',')"
      @change="handleFileSelect"
      style="display: none"
    />
  </div>
</template>

<style scoped>
.file-upload {
  margin-top: 2rem;
  padding-top: 2rem;
  border-top: 1px solid #eee;
}

.file-upload h2 {
  font-size: 1.25rem;
  margin-bottom: 0.5rem;
  color: #333;
}

.description {
  color: #666;
  margin-bottom: 1rem;
}

.drop-zone {
  border: 2px dashed #ddd;
  border-radius: 8px;
  padding: 2rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
}

.drop-zone:hover {
  border-color: #4a90d9;
  background: #f8fbff;
}

.drop-zone.dragging {
  border-color: #4a90d9;
  background: #e8f4fd;
}

.drop-content {
  color: #666;
}

.drop-icon {
  font-size: 3rem;
  display: block;
  margin-bottom: 1rem;
}

.drop-hint {
  font-size: 0.875rem;
  color: #999;
  margin-top: 0.5rem;
}

.drop-formats {
  font-size: 0.75rem;
  color: #999;
  margin-top: 0.5rem;
}

.selected-file {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 1rem;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.file-icon {
  font-size: 2rem;
}

.file-details {
  flex: 1;
}

.file-name {
  font-weight: 500;
  color: #333;
  word-break: break-all;
}

.file-size {
  font-size: 0.875rem;
  color: #666;
  margin-top: 0.25rem;
}

.clear-btn {
  background: none;
  border: none;
  color: #999;
  font-size: 1.25rem;
  cursor: pointer;
  padding: 0.5rem;
}

.clear-btn:hover:not(:disabled) {
  color: #666;
}

.clear-btn:disabled {
  cursor: not-allowed;
}

.submit-btn {
  width: 100%;
  padding: 0.75rem;
  background: #4a90d9;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  cursor: pointer;
  margin-top: 1rem;
}

.submit-btn:hover:not(:disabled) {
  background: #3a7bc8;
}

.submit-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}
</style>
