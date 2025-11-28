<template>
  <div class="empty-state">
    <div class="empty-icon">🎵</div>
    <h2 class="empty-title">{{ title }}</h2>
    <p class="empty-description">{{ description }}</p>
    <slot name="action"></slot>
  </div>
</template>

<script setup lang="ts">
interface Props {
  title?: string
  description?: string
}

withDefaults(defineProps<Props>(), {
  title: '尚無歌曲',
  description: '點擊「新增歌曲」開始處理您的第一首歌曲',
})
</script>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 2rem;
  text-align: center;
  color: #888;
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
  opacity: 0.5;
}

.empty-title {
  font-size: 1.5rem;
  font-weight: 500;
  color: #aaa;
  margin: 0 0 0.5rem 0;
}

.empty-description {
  font-size: 0.9rem;
  max-width: 300px;
  line-height: 1.5;
  margin: 0;
}
</style>
