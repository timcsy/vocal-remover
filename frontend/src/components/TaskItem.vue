<template>
  <div class="task-item" @click="$emit('click', job.id)">
    <div class="task-info">
      <span class="task-title">{{ job.source_title || '處理中...' }}</span>
      <span class="task-status">{{ statusText }}</span>
    </div>
    <div class="task-progress">
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: `${job.progress}%` }"></div>
      </div>
      <span class="progress-text">{{ job.progress }}%</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ProcessingJob } from '@/services/api'

interface Props {
  job: ProcessingJob
}

const props = defineProps<Props>()

defineEmits<{
  click: [jobId: string]
}>()

const statusText = computed(() => {
  if (props.job.current_stage) {
    return props.job.current_stage
  }
  switch (props.job.status) {
    case 'pending':
      return '等待中'
    case 'downloading':
      return '下載中'
    case 'separating':
      return '分離人聲中'
    case 'merging':
      return '影片擷取中'
    case 'mixing':
      return '混音中'
    default:
      return '處理中'
  }
})
</script>

<style scoped>
.task-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem 1rem;
  background: #252525;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.15s;
  min-width: 200px;
}

.task-item:hover {
  background: #2a2a2a;
}

.task-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  min-width: 0;
}

.task-title {
  font-size: 0.85rem;
  color: #e0e0e0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 150px;
}

.task-status {
  font-size: 0.7rem;
  color: #888;
}

.task-progress {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.progress-bar {
  width: 60px;
  height: 4px;
  background: #333;
  border-radius: 2px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #4a9eff;
  transition: width 0.3s;
}

.progress-text {
  font-size: 0.7rem;
  color: #888;
  font-family: monospace;
  min-width: 32px;
}
</style>
