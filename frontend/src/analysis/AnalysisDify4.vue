<template>
  <div class="analysis-dify4">
    <h3>Dify4 分析组件</h3>
    <p>当前对话ID: {{ currentConversationId }}</p>
    <div v-if="analysisData && analysisData.functions">
      <h4>函数分析结果 (Dify4):</h4>
      <div v-for="(func, index) in analysisData.functions" :key="index" class="function-item">
        <h5>{{ func.name || `函数 ${index + 1}` }}</h5>
        <p><strong>地址:</strong> {{ func.address }}</p>
        <p><strong>大小:</strong> {{ func.size }}</p>
        <p v-if="func.description"><strong>描述:</strong> {{ func.description }}</p>
      </div>
    </div>
    <div v-else>
      <p>暂无分析数据</p>
    </div>
  </div>
</template>

<script setup>
defineProps({
  currentConversationId: {
    type: String,
    default: null
  },
  analysisData: {
    type: Object,
    default: () => ({ functions: [] })
  }
});
</script>

<style scoped>
.analysis-dify4 {
  padding: 16px;
  color: #a0aec0;
}

.function-item {
  margin-bottom: 16px;
  padding: 12px;
  border: 1px solid #2d3748;
  border-radius: 4px;
  background-color: #1a202c;
}

.function-item h5 {
  margin: 0 0 8px 0;
  color: #e2e8f0;
}

.function-item p {
  margin: 4px 0;
}
</style> 