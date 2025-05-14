<script setup>
import { defineAsyncComponent } from 'vue';

defineProps({
  currentConversationId: {
    type: String,
    default: null
  },
  currentModel: {
    type: String,
    required: true
  }
});

// 动态加载组件
const getAnalysisComponent = (model) => {
  const componentMap = {
    dify1: defineAsyncComponent({
      loader: () => import('../analysis/AnalysisDify1.vue'),
      loadingComponent: {
        template: '<p>加载中...</p>'
      },
      errorComponent: {
        template: '<p>加载失败，请稍后重试。</p>'
      },
      delay: 200, // 延迟显示加载状态（毫秒）
      timeout: 3000 // 超时时间（毫秒）
    }),
    dify2: defineAsyncComponent({
      loader: () => import('../analysis/AnalysisDify2.vue'),
      loadingComponent: {
        template: '<p>加载中...</p>'
      },
      errorComponent: {
        template: '<p>加载失败，请稍后重试。</p>'
      },
      delay: 200,
      timeout: 3000
    }),
    default: defineAsyncComponent({
      loader: () => import('../analysis/DefaultAnalysis.vue'),
      loadingComponent: {
        template: '<p>加载中...</p>'
      },
      errorComponent: {
        template: '<p>加载失败，请稍后重试。</p>'
      },
      delay: 200,
      timeout: 3000
    }),
    // 添加更多模型映射
  };
  return componentMap[model] || componentMap.default;
};
</script>

<template>
  <div class="analysis-area">
    <h4>分析展示界面</h4>
    <p>这里将展示每一步的思考过程、调用了什么、输出什么结果等信息。</p>
    <p>根据具体任务进行设计，每个任务不同（可以展示分析表格、分析思路、思考链、工具链等）。</p>
     <!-- Display current conversation ID -->
     <!-- <div v-if="currentConversationId" class="conversation-id-display">
         当前会话 ID: {{ currentConversationId }}
     </div> -->

    <!-- 动态加载分析组件 -->
    <component 
      :is="getAnalysisComponent(currentModel)" 
      :currentConversationId="currentConversationId"
    />
  </div>
</template>

<style scoped>
.analysis-area {
  flex: 4; /* Proportion 4 */
  padding: 15px;
  background-color: #f8f9fa;
   overflow-y: auto; /* Allow scrolling if content exceeds height */
   border-left: 1px solid #ddd; /* Separator */
}

.conversation-id-display {
  margin-top: 20px; 
  font-size: 12px; 
  color: grey;
  word-break: break-all; /* Break long IDs */
}
</style> 