<script setup>
import { ref, computed } from 'vue';

const props = defineProps({
  currentConversationId: { type: String, default: null },
  analysisData: { type: Object, default: () => ({ functions: [] }) }
});
const decompilationData = computed(() => props.analysisData);

// 函数列表
const functions = computed(() => {
  return decompilationData.value.functions.map(func => ({
    name: func.name,
    entry_point: func.entry_point,
    signature: func.signature
  }));
});

// 当前选中的函数
const activeFunction = ref(0);
const currentFunction = computed(() => {
  const funcs = decompilationData.value.functions;
  if (!funcs || funcs.length === 0) return null;
  if (activeFunction.value >= funcs.length) {
    activeFunction.value = 0;
  }
  return funcs[activeFunction.value];
});

// 当前函数的汇编代码
const assemblyLines = computed(() => {
  return currentFunction.value?.disassembly || [];
});

const language = ref('zh');

function selectFunction(index) {
  activeFunction.value = index;
}
</script>

<template>
  <div class="decompiler-content">
    <h5>反编译分析界面</h5>
    <p v-if="props.currentConversationId">当前会话 ID: {{ props.currentConversationId }}</p>
    
    <!-- 如果没有函数数据，显示提示 -->
    <div v-if="functions.length === 0" style="padding: 20px; text-align: center; color: #a0aec0;">
      <h4>暂无分析数据</h4>
      <p>请先上传二进制文件并进行分析，或手动加载分析结果JSON文件。</p>
    </div>
    
    <!-- 有数据时显示分析界面 -->
    <div v-else class="decompiler-layout">
      <!-- 左侧函数列表 -->
      <div class="function-list">
        <div class="search-box">
          <input type="text" placeholder="搜索函数..." />
        </div>
        <div class="function-items">
          <div 
            v-for="(func, index) in functions" 
            :key="index"
            class="function-item"
            :class="{ active: activeFunction === index }"
            @click="selectFunction(index)"
          >
            <span class="address">{{ func.entry_point }}:</span>
            <span class="name">{{ func.name }}</span>
          </div>
        </div>
      </div>

      <!-- 中间汇编代码 -->
      <div class="assembly-code">
        <div class="code-header">
          <h4>汇编代码 - {{ currentFunction?.name || '未知函数' }}</h4>
          <span class="signature">{{ currentFunction?.signature || '' }}</span>
        </div>
        <div class="code-content">
          <div 
            v-for="(line, index) in assemblyLines" 
            :key="index" 
            class="code-line"
          >
            <span class="address">{{ line.address }}:</span>
            <span class="instruction">{{ line.code }}</span>
          </div>
        </div>
      </div>

      <!-- 右侧反编译代码（可选） -->
      <div class="decompiled-code">
        <pre>{{ currentFunction?.c_code || '暂无反编译代码' }}</pre>
      </div>
    </div>
  </div>
</template>

<style scoped>
.decompiler-content {
  height: 100%;
  overflow: hidden;
}

.decompiler-layout {
  display: flex;
  height: 100%;
  font-family: 'Consolas', monospace;
  color: #e2e8f0;
}

.function-list,
.assembly-code {
  height: 100%;
  overflow: auto;
  border-right: 1px solid #2d3748;
}

.function-list {
  width: 250px;
}

.search-box {
  padding: 10px;
  border-bottom: 1px solid #2d3748;
}

.search-box input {
  width: 100%;
  padding: 5px;
  border: 1px solid #2d3748;
  border-radius: 3px;
  background-color: #1a1d23;
  color: #e2e8f0;
}

.function-items {
  height: calc(100% - 42px);
  overflow-y: auto;
}

.function-item {
  padding: 8px 10px;
  cursor: pointer;
  border-bottom: 1px solid #2d3748;
  font-size: 13px;
}

.function-item:hover {
  background-color: #2d3748;
}

.function-item.active {
  background-color: #2563eb;
}

.address {
  color: #a0aec0;
  margin-right: 5px;
}

.assembly-code {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 300px; /* 设置最小宽度 */
}

.code-header {
  padding: 10px;
  border-bottom: 1px solid #2d3748;
}

.code-header h4 {
  margin: 0 0 5px 0;
}

.signature {
  color: #a0aec0;
  font-size: 0.85em;
}

.code-content {
  flex: 1;
  overflow: auto;
  padding: 5px 0;
}

.code-line {
  display: flex;
  padding: 3px 10px;
  font-size: 14px;
  font-family: 'Consolas', monospace;
}

.code-line:hover {
  background-color: #2d3748;
}

.code-line .address {
  width: 120px;
  text-align: right;
  margin-right: 10px;
  color: #718096;
}

.code-line .instruction {
  flex: 1;
}

/* 反编译代码区域样式 */
.decompiled-code {
  width: 400px; /* 固定宽度 */
  min-width: 400px; /* 最小宽度 */
  max-width: 400px; /* 最大宽度 */
  height: 100%;
  overflow: auto;
  border-left: 1px solid #2d3748;
  padding: 10px;
  background-color: #1a1d23;
}

.decompiled-code pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: 'Consolas', monospace;
  font-size: 13px;
  line-height: 1.4;
  color: #e2e8f0;
}
</style>