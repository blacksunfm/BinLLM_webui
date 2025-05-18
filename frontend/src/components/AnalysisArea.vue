<script setup>
import { defineAsyncComponent } from 'vue';
import { ref } from 'vue';

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

function toggleCollapse() {
  isCollapsed.value = !isCollapsed.value;
}
</script>

<template>
  <div class="analysis-container">
    <!-- 固定在右侧的展开按钮（折叠时显示） -->
    <div 
      v-if="isCollapsed"
      class="fixed-expand-button"
      @click="toggleCollapse"
      title="展开分析面板"
    >
      <div class="button-inner">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M15 12L9 18M15 12L9 6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
        <span>分析</span>
      </div>
    </div>

    <!-- 分析区域主体 -->
    <div 
      class="analysis-area"
      :style="{ 
        width: isCollapsed ? '0' : `${currentWidth}px`,
        minWidth: isCollapsed ? '0' : `${currentWidth}px`
      }"
    >
      <!-- 可拖拽的调整手柄 -->
      <div 
        class="resize-handle"
        @mousedown="startResize"
        title="拖拽调整宽度"
      ></div>
      
      <div class="content-wrapper" v-show="!isCollapsed">
        <!-- 分析内容区域 -->
        <div class="analysis-content">
          <!-- 折叠按钮移动到内容区域右上角 -->
          <button 
            class="floating-collapse-button"
            @click="toggleCollapse"
            title="折叠分析面板"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M9 12L15 18M9 12L15 6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </button>
          
          <!-- 动态加载的组件 -->
          <component 
            :is="getAnalysisComponent(currentModel)" 
            :currentConversationId="currentConversationId"
          />
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

/* 固定在右侧的展开按钮 */
.fixed-expand-button {
  position: fixed;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  background-color: #2563eb;
  color: white;
  padding: 12px 6px;
  border-radius: 4px 0 0 4px;
  cursor: pointer;
  z-index: 100;
  box-shadow: -2px 0 8px rgba(0, 0, 0, 0.1);
  transition: all 0.2s ease;
}

.fixed-expand-button:hover {
  background-color: #1d4ed8;
  padding-right: 8px;
}

.button-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.button-inner svg {
  transform: rotate(180deg);
}

/* 分析区域主体 */
.analysis-area {
  height: 100%;
  background-color: #202123;
  border-left: 1px solid #2d3748;
  transition: width 0.3s ease, min-width 0.3s ease;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.resize-handle {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  background: transparent;
  cursor: col-resize;
  z-index: 10;
}

.resize-handle:hover {
  background: #2563eb;
}

.content-wrapper {
  height: 100%;
  display: flex;
  flex-direction: column;
}

/* 分析内容区域 */
.analysis-content {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
  color: #a0aec0;
  position: relative; /* 为浮动按钮提供定位上下文 */
}

/* 浮动折叠按钮 */
.floating-collapse-button {
  position: absolute;
  top: 12px;
  right: 12px;
  background: rgba(45, 55, 72, 0.7);
  border: none;
  color: #a0aec0;
  cursor: pointer;
  padding: 6px;
  border-radius: 4px;
  z-index: 10;
  transition: all 0.2s ease;
}

.floating-collapse-button:hover {
  color: #e2e8f0;
  background-color: #2d3748;
  transform: scale(1.1);
}

/* 全局拖拽状态样式 */
body.resizing {
  cursor: col-resize !important;
  user-select: none !important;
}
</style>