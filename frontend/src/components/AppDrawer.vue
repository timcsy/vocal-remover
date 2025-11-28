<template>
  <aside class="drawer" :class="{ open: isOpen }">
    <div class="drawer-header">
      <h2 class="drawer-title">歌曲列表</h2>
      <button class="drawer-close" @click="$emit('close')" title="關閉">×</button>
    </div>

    <div class="drawer-content">
      <SongList
        :jobs="jobs"
        :selectedJobId="selectedJobId"
        :selectedJobIds="selectedJobIds"
        @select="$emit('select', $event)"
        @toggle="$emit('toggle', $event)"
        @delete="$emit('delete', $event)"
        @selectAll="$emit('selectAll')"
        @deselectAll="$emit('deselectAll')"
      />
    </div>

    <div class="drawer-footer">
      <button class="btn btn-primary" @click="$emit('addSong')">
        + 新增歌曲
      </button>
      <div class="export-actions" v-if="hasSelectedJobs">
        <button class="btn btn-secondary" @click="$emit('export')">
          匯出 ({{ selectedCount }})
        </button>
      </div>
      <button class="btn btn-secondary" @click="$emit('import')">
        匯入
      </button>
    </div>
  </aside>

  <!-- 手機版背景遮罩 -->
  <div
    v-if="isOpen"
    class="drawer-overlay"
    @click="$emit('close')"
  ></div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { CompletedJob } from '@/services/api'
import SongList from './SongList.vue'

interface Props {
  isOpen: boolean
  jobs: readonly CompletedJob[]
  selectedJobId?: string | null
  selectedJobIds?: ReadonlySet<string>
}

const props = withDefaults(defineProps<Props>(), {
  selectedJobId: null,
  selectedJobIds: () => new Set(),
})

defineEmits<{
  close: []
  select: [jobId: string]
  toggle: [jobId: string]
  delete: [jobId: string]
  selectAll: []
  deselectAll: []
  addSong: []
  export: []
  import: []
}>()

const hasSelectedJobs = computed(() => props.selectedJobIds.size > 0)
const selectedCount = computed(() => props.selectedJobIds.size)
</script>

<style scoped>
.drawer {
  position: fixed;
  left: 0;
  top: 0;
  width: 300px;
  height: 100vh;
  background: #1e1e1e;
  border-right: 1px solid #333;
  display: flex;
  flex-direction: column;
  transform: translateX(-100%);
  transition: transform 0.3s ease;
  z-index: 100;
}

.drawer.open {
  transform: translateX(0);
}

.drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem;
  border-bottom: 1px solid #333;
  background: #252525;
}

.drawer-title {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 500;
  color: #e0e0e0;
}

.drawer-close {
  background: transparent;
  border: none;
  color: #888;
  font-size: 1.5rem;
  cursor: pointer;
  padding: 0.25rem 0.5rem;
  line-height: 1;
}

.drawer-close:hover {
  color: #fff;
}

.drawer-content {
  flex: 1;
  overflow: hidden;
}

.drawer-footer {
  padding: 1rem;
  border-top: 1px solid #333;
  background: #252525;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.btn {
  padding: 0.75rem 1rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: background-color 0.15s;
}

.btn-primary {
  background: #4a9eff;
  color: #fff;
}

.btn-primary:hover {
  background: #3a8eef;
}

.btn-secondary {
  background: #3a3a3a;
  color: #e0e0e0;
}

.btn-secondary:hover {
  background: #4a4a4a;
}

.export-actions {
  display: flex;
  gap: 0.5rem;
}

.export-actions .btn {
  flex: 1;
}

.drawer-overlay {
  display: none;
}

/* 手機版 */
@media (max-width: 768px) {
  .drawer {
    width: 85%;
    max-width: 320px;
  }

  .drawer-overlay {
    display: block;
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    z-index: 99;
  }
}
</style>
