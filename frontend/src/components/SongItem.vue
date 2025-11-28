<template>
  <div
    class="song-item"
    :class="{ selected: isSelected, checked: isChecked }"
    @click="handleClick"
  >
    <input
      type="checkbox"
      :checked="isChecked"
      @click.stop="handleCheckboxClick"
      class="song-checkbox"
    />
    <div class="song-info">
      <span class="song-title">{{ job.source_title || '未命名' }}</span>
      <span class="song-meta">
        <span v-if="job.original_duration" class="duration">
          {{ formatDuration(job.original_duration) }}
        </span>
        <span class="source-type">{{ job.source_type === 'youtube' ? 'YouTube' : '上傳' }}</span>
      </span>
    </div>
    <button
      v-if="showDelete"
      class="delete-btn"
      @click.stop="handleDelete"
      title="刪除"
    >
      ×
    </button>
  </div>
</template>

<script setup lang="ts">
import type { CompletedJob } from '@/services/api'

interface Props {
  job: CompletedJob
  isSelected?: boolean
  isChecked?: boolean
  showDelete?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isSelected: false,
  isChecked: false,
  showDelete: true,
})

const emit = defineEmits<{
  select: [jobId: string]
  toggle: [jobId: string]
  delete: [jobId: string]
}>()

function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

function handleClick() {
  emit('select', props.job.id)
}

function handleCheckboxClick() {
  emit('toggle', props.job.id)
}

function handleDelete() {
  emit('delete', props.job.id)
}
</script>

<style scoped>
.song-item {
  display: flex;
  align-items: center;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #333;
  cursor: pointer;
  transition: background-color 0.15s;
}

.song-item:hover {
  background-color: #2a2a2a;
}

.song-item.selected {
  background-color: #3a3a3a;
  border-left: 3px solid #4a9eff;
}

.song-item.checked {
  background-color: #2d3748;
}

.song-checkbox {
  margin-right: 0.75rem;
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.song-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.song-title {
  font-size: 0.9rem;
  color: #e0e0e0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.song-meta {
  display: flex;
  gap: 0.5rem;
  font-size: 0.75rem;
  color: #888;
}

.duration {
  font-family: monospace;
}

.source-type {
  text-transform: uppercase;
  font-size: 0.65rem;
  background: #444;
  padding: 0.1rem 0.3rem;
  border-radius: 2px;
}

.delete-btn {
  background: transparent;
  border: none;
  color: #888;
  font-size: 1.2rem;
  cursor: pointer;
  padding: 0.25rem 0.5rem;
  opacity: 0;
  transition: opacity 0.15s, color 0.15s;
}

.song-item:hover .delete-btn {
  opacity: 1;
}

.delete-btn:hover {
  color: #ff4444;
}
</style>
