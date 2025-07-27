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
    <h5>默认分析界面</h5>
    <p>当前模型未定义特定的分析界面。</p>
    <p>当前会话 ID: {{ currentConversationId }}</p>
  </div>
</template>

<style scoped>
/* 添加样式 */
</style>