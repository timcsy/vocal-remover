<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal">
      <div class="modal-header">
        <h2>匯入衝突</h2>
        <button class="close-btn" @click="$emit('close')">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 6L6 18M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div class="modal-body">
        <p class="conflict-message">
          歌曲「<strong>{{ conflict.source_title }}</strong>」已存在。
          <br>請選擇處理方式：
        </p>

        <div class="options">
          <button
            class="option-btn"
            :class="{ active: selectedAction === 'overwrite' }"
            @click="selectedAction = 'overwrite'"
          >
            <div class="option-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="7 10 12 15 17 10" />
                <line x1="12" y1="15" x2="12" y2="3" />
              </svg>
            </div>
            <div class="option-content">
              <span class="option-title">覆蓋</span>
              <span class="option-desc">用新匯入的內容取代現有歌曲</span>
            </div>
          </button>

          <button
            class="option-btn"
            :class="{ active: selectedAction === 'rename' }"
            @click="selectedAction = 'rename'"
          >
            <div class="option-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
              </svg>
            </div>
            <div class="option-content">
              <span class="option-title">重新命名</span>
              <span class="option-desc">保留兩者，為新匯入的歌曲命名</span>
            </div>
          </button>
        </div>

        <div v-if="selectedAction === 'rename'" class="rename-input">
          <label for="newTitle">新名稱</label>
          <input
            id="newTitle"
            v-model="newTitle"
            type="text"
            placeholder="輸入新的歌曲名稱"
            @keyup.enter="handleConfirm"
          />
        </div>

        <p v-if="errorMessage" class="error-message">{{ errorMessage }}</p>
      </div>

      <div class="modal-footer">
        <button class="btn-secondary" @click="$emit('close')">取消</button>
        <button
          class="btn-primary"
          :disabled="!canConfirm || isLoading"
          @click="handleConfirm"
        >
          {{ isLoading ? '處理中...' : '確認' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { ImportConflict } from '@/services/api'

interface Props {
  conflict: ImportConflict
}

const props = defineProps<Props>()

const emit = defineEmits<{
  close: []
  resolve: [action: string, newTitle?: string]
}>()

const selectedAction = ref<'overwrite' | 'rename' | null>(null)
const newTitle = ref(props.conflict.source_title + ' (2)')
const isLoading = ref(false)
const errorMessage = ref('')

const canConfirm = computed(() => {
  if (!selectedAction.value) return false
  if (selectedAction.value === 'rename' && !newTitle.value.trim()) return false
  return true
})

function handleConfirm() {
  if (!canConfirm.value || isLoading.value) return

  errorMessage.value = ''

  if (selectedAction.value === 'rename' && newTitle.value.trim() === props.conflict.source_title) {
    errorMessage.value = '新名稱不能與原名稱相同'
    return
  }

  emit('resolve', selectedAction.value!, selectedAction.value === 'rename' ? newTitle.value.trim() : undefined)
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
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
  max-width: 450px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.5);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid #333;
}

.modal-header h2 {
  font-size: 1.1rem;
  font-weight: 600;
  color: #fff;
}

.close-btn {
  background: none;
  border: none;
  color: #888;
  cursor: pointer;
  padding: 0.25rem;
  transition: color 0.15s;
}

.close-btn:hover {
  color: #fff;
}

.modal-body {
  padding: 1.25rem;
}

.conflict-message {
  color: #ccc;
  margin-bottom: 1rem;
  line-height: 1.5;
}

.conflict-message strong {
  color: #fff;
}

.options {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.option-btn {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: #252525;
  border: 2px solid #333;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s;
  text-align: left;
}

.option-btn:hover {
  border-color: #444;
  background: #2a2a2a;
}

.option-btn.active {
  border-color: #4a9eff;
  background: rgba(74, 158, 255, 0.1);
}

.option-icon {
  flex-shrink: 0;
  color: #888;
}

.option-btn.active .option-icon {
  color: #4a9eff;
}

.option-content {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.option-title {
  font-weight: 600;
  color: #e0e0e0;
}

.option-desc {
  font-size: 0.8rem;
  color: #888;
}

.rename-input {
  margin-top: 1rem;
}

.rename-input label {
  display: block;
  font-size: 0.85rem;
  color: #888;
  margin-bottom: 0.5rem;
}

.rename-input input {
  width: 100%;
  padding: 0.75rem 1rem;
  background: #252525;
  border: 1px solid #333;
  border-radius: 4px;
  color: #e0e0e0;
  font-size: 0.95rem;
}

.rename-input input:focus {
  outline: none;
  border-color: #4a9eff;
}

.error-message {
  color: #ff6b6b;
  font-size: 0.85rem;
  margin-top: 0.75rem;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  padding: 1rem 1.25rem;
  border-top: 1px solid #333;
}

.btn-secondary {
  padding: 0.6rem 1.25rem;
  background: #333;
  border: none;
  border-radius: 4px;
  color: #e0e0e0;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.15s;
}

.btn-secondary:hover {
  background: #444;
}

.btn-primary {
  padding: 0.6rem 1.25rem;
  background: #4a9eff;
  border: none;
  border-radius: 4px;
  color: #fff;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.15s;
}

.btn-primary:hover:not(:disabled) {
  background: #3a8eef;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
