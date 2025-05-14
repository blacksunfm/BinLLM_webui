<script setup>
defineProps({
  currentConversationId: {
    type: String,
    default: null
  }
});
</script>

<template>
  <div>
    <h5>模型 Dify1 的分析界面</h5>
    <p>这里是针对模型 Dify1 的分析内容。</p>
    <p>当前会话 ID: {{ currentConversationId }}</p>
  </div>
</template>

<style scoped>
/* 添加样式 */
</style>