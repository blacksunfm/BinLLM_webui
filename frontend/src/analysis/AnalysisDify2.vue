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
    <h5>模型 Dify2 的分析界面</h5>
    <p>这里是针对模型 Dify2 的分析内容。</p>
    <p>这里将展示每一步的思考过程、调用了什么、输出什么结果等信息。</p>
          <p>根据具体任务进行设计，每个任务不同（可以展示分析表格、分析思路、思考链、工具链等）。</p>
          <ul>
            <li>每一步的思考过程</li>
            <li>调用的分析工具</li>
            <li>中间分析结果</li>
            <li>最终结论依据</li>
          </ul>
    <p>当前会话 ID: {{ currentConversationId }}</p>
  </div>
</template>

<style scoped>
/* 添加样式 */
</style>