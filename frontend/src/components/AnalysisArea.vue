<script setup>
import { defineAsyncComponent, computed } from 'vue';
import { ref, defineEmits } from 'vue';
import { analyzeBinary } from '../services/api.js';
import AnalysisDify1 from '../analysis/AnalysisDify1.vue';
import { watch } from 'vue';

const props = defineProps({
  currentConversationId: {
    type: String,
    default: null
  },
  currentModel: {
    type: String,
    required: true
  }
});

// 布局控制
const isCollapsed = ref(false);
const currentWidth = ref(300);
const isResizing = ref(false);
const startX = ref(0);
const startWidth = ref(0);

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
      delay: 200,
      timeout: 3000
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
    dify3: defineAsyncComponent({
      loader: () => import('../analysis/AnalysisDify3.vue'),
      loadingComponent: {
        template: '<p>加载中...</p>'
      },
      errorComponent: {
        template: '<p>加载失败，请稍后重试。</p>'
      },
      delay: 200,
      timeout: 3000
    }),
    dify4: defineAsyncComponent({
      loader: () => import('../analysis/AnalysisDify4.vue'),
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
  };
  return componentMap[model] || componentMap.default;
};

// 根据当前模型计算要使用的组件
const currentAnalysisComponent = computed(() => {
  return getAnalysisComponent(props.currentModel);
});

// 拖拽逻辑
function startResize(e) {
  isResizing.value = true;
  startX.value = e.clientX;
  startWidth.value = currentWidth.value;
  document.addEventListener('mousemove', handleResize);
  document.addEventListener('mouseup', stopResize);
  document.body.classList.add('resizing');
  e.preventDefault();
}

function handleResize(e) {
  if (!isResizing.value) return;
  const deltaX = startX.value - e.clientX;
  currentWidth.value = Math.min(Math.max(startWidth.value + deltaX, 200), 1000);
}

function stopResize() {
  isResizing.value = false;
  document.removeEventListener('mousemove', handleResize);
  document.removeEventListener('mouseup', stopResize);
  document.body.classList.remove('resizing');
}

const emit = defineEmits(['toggle-analysis-area']);

// 移除 fixed-expand-button、floating-collapse-button、toggleCollapse、isCollapsed 相关内容和样式。

const analysisData = ref({ functions: [] });

// 调试：监听currentModel变化
watch(() => props.currentModel, (val) => { 
  console.log('AnalysisArea - currentModel changed:', val); 
});

// 暴露给父组件的方法
function setAnalysisData(data) {
  console.log('setAnalysisData called with:', data);
  analysisData.value = data;
}

defineExpose({ setAnalysisData });
</script>

<template>
  <div class="analysis-container">
    <!-- 分析区域主体 -->
    <div 
      class="analysis-area"
      v-show="!isCollapsed"
      style="width: 100%; min-width: 0;"
    >
      <div class="content-wrapper">
        <!-- 分析内容区域 -->
        <div class="analysis-content">
          <component :is="currentAnalysisComponent" :currentConversationId="props.currentConversationId" :analysisData="analysisData" />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.analysis-container {
  position: relative;
  height: 100%;
}
.analysis-area {
  height: 100%;
  background-color: #202123;
  border-left: 1px solid #2d3748;
  transition: width 0.3s ease, min-width 0.3s ease;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  width: 100%;
  min-width: 0;
}
.content-wrapper {
  height: 100%;
  display: flex;
  flex-direction: column;
}
.analysis-content {
  flex: 1;
  padding: 16px;
  overflow: hidden;
  color: #a0aec0;
  position: relative;
}
</style>