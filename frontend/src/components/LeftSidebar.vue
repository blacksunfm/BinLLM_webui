<script setup>
import { ref, computed } from 'vue';

// Props
const props = defineProps({
  models: {
    type: Array,
    default: () => []
  },
  selectedModel: {
    type: String,
    default: 'dify1'
  }
});

// Events
const emit = defineEmits(['select-model']);

// Handle model selection
function selectModel(modelId) {
  emit('select-model', modelId);
}

// Computed properties to determine active model
const isModelActive = computed(() => {
  return (modelId) => modelId === props.selectedModel;
});

// 机器人图标SVG
const robotIcon = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width="40" height="40">
  <path d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 0 1 7 7h1a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1h-1v1a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-1H2a1 1 0 0 1-1-1v-3a1 1 0 0 1 1-1h1a7 7 0 0 1 7-7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 0 1 2-2M7.5 13A2.5 2.5 0 0 0 5 15.5A2.5 2.5 0 0 0 7.5 18a2.5 2.5 0 0 0 2.5-2.5A2.5 2.5 0 0 0 7.5 13m9 0a2.5 2.5 0 0 0-2.5 2.5a2.5 2.5 0 0 0 2.5 2.5a2.5 2.5 0 0 0 2.5-2.5a2.5 2.5 0 0 0-2.5-2.5z"></path>
</svg>`;

const customNames = ['反编译', '渗透测试', '函数匹配', '类型检测', '安全性分析', '代码质量分析', '控制流分析', '数据流分析', '符号执行', '代码解释']; // 自定义名称数组

</script>

<template>
  <div class="left-sidebar">
    <div class="logo-container">
      <div class="robot-icon" v-html="robotIcon"></div>
      <h2 class="logo-text">NWPU</h2>
    </div>

    <div class="model-buttons">
      <button 
        v-for="(model, index) in models" 
        :key="model.id"
        :class="['model-button', { active: isModelActive(model.id) }]"
        @click="selectModel(model.id)"
      >
        {{ customNames[index] || `未命名功能${index + 1}` }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.left-sidebar {
  width: 100px;
  background-color: #1a1a1a;
  height: 100vh;
  padding: 1rem 0.5rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  border-right: 1px solid #333;
}

.logo-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 2rem;
}

.robot-icon {
  color: #4e8ef7;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo-text {
  font-size: 1.0rem;
  color: #fff;
  margin-top: 0.5rem;
  text-align: center;
}

.model-buttons {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  width: 100%;
}

.model-button {
  background-color: #2a2a2a;
  border: none;
  color: #ccc;
  padding: 0.5rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.8rem;
  transition: all 0.2s ease;
  width: 100%;
  text-align: center;
}

.model-button:hover {
  background-color: #3a3a3a;
}

.model-button.active {
  background-color: #3e6ae1;
  color: white;
}
</style> 