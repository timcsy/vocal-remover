<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { api, type Job, type ApiError } from '../services/api';

const emit = defineEmits<{
  (e: 'jobCreated', job: Job): void;
  (e: 'error', message: string): void;
}>();

const url = ref('');
const isLoading = ref(false);

const youtubeUrlPattern = /^(https?:\/\/)?(www\.)?(youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/shorts\/)[a-zA-Z0-9_-]{11}/;

// 從 URL 提取 YouTube 影片 ID
function extractVideoId(inputUrl: string): string | null {
  const patterns = [
    /youtube\.com\/watch\?v=([a-zA-Z0-9_-]{11})/,
    /youtu\.be\/([a-zA-Z0-9_-]{11})/,
    /youtube\.com\/shorts\/([a-zA-Z0-9_-]{11})/,
  ];

  for (const pattern of patterns) {
    const match = inputUrl.match(pattern);
    if (match) return match[1];
  }
  return null;
}

// 計算當前影片 ID
const videoId = computed(() => extractVideoId(url.value));

// YouTube 嵌入網址
const embedUrl = computed(() => {
  if (!videoId.value) return null;
  return `https://www.youtube.com/embed/${videoId.value}`;
});

function isValidUrl(): boolean {
  return youtubeUrlPattern.test(url.value);
}

async function submit() {
  if (!isValidUrl()) {
    emit('error', '請輸入有效的 YouTube 網址');
    return;
  }

  isLoading.value = true;

  try {
    const job = await api.createJobFromUrl(url.value);
    url.value = '';
    emit('jobCreated', job);
  } catch (error) {
    const apiError = error as ApiError;
    emit('error', apiError.message || '建立任務失敗');
  } finally {
    isLoading.value = false;
  }
}
</script>

<template>
  <div class="url-input">
    <h2>YouTube 網址</h2>
    <p class="description">貼上 YouTube 影片網址，自動下載並去除人聲</p>

    <form @submit.prevent="submit" class="input-form">
      <input
        v-model="url"
        type="text"
        placeholder="https://www.youtube.com/watch?v=..."
        :disabled="isLoading"
        class="url-field"
      />
      <button
        type="submit"
        :disabled="isLoading || !url.trim()"
        class="submit-btn"
      >
        {{ isLoading ? '處理中...' : '開始處理' }}
      </button>
    </form>

    <p class="hint">支援 youtube.com 和 youtu.be 網址</p>

    <!-- YouTube 預覽播放器 -->
    <div v-if="embedUrl" class="video-preview">
      <h3>影片預覽</h3>
      <div class="video-container">
        <iframe
          :src="embedUrl"
          frameborder="0"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          allowfullscreen
        ></iframe>
      </div>
    </div>
  </div>
</template>

<style scoped>
.url-input {
  margin-bottom: 2rem;
}

.url-input h2 {
  font-size: 1.25rem;
  margin-bottom: 0.5rem;
  color: #333;
}

.description {
  color: #666;
  margin-bottom: 1rem;
}

.input-form {
  display: flex;
  gap: 0.5rem;
}

.url-field {
  flex: 1;
  padding: 0.75rem 1rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
}

.url-field:focus {
  outline: none;
  border-color: #4a90d9;
  box-shadow: 0 0 0 2px rgba(74, 144, 217, 0.2);
}

.url-field:disabled {
  background: #f5f5f5;
  cursor: not-allowed;
}

.submit-btn {
  padding: 0.75rem 1.5rem;
  background: #4a90d9;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  cursor: pointer;
  white-space: nowrap;
}

.submit-btn:hover:not(:disabled) {
  background: #3a7bc8;
}

.submit-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.hint {
  font-size: 0.875rem;
  color: #999;
  margin-top: 0.5rem;
}

.video-preview {
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid #eee;
}

.video-preview h3 {
  font-size: 1rem;
  color: #666;
  margin-bottom: 0.75rem;
}

.video-container {
  position: relative;
  width: 100%;
  padding-bottom: 56.25%; /* 16:9 比例 */
  background: #000;
  border-radius: 8px;
  overflow: hidden;
}

.video-container iframe {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}
</style>
