<script setup>
import { ref } from 'vue';

defineProps({
  currentConversationId: {
    type: String,
    default: null
  }
});

// 反编译数据
const functions = ref([
  { address: '5368713216', name: 'sub_140001000' },
  { address: '5368713276', name: 'sub_14000103C' },
  { address: '5368713344', name: 'sub_140001080' },
  { address: '5368713360', name: 'sub_140001090' },
  { address: '5368713440', name: 'sub_1400010E0' },
  { address: '5368713904', name: 'sub_140001280' },
  { address: '5368714000', name: 'sub_140001310' }
]);

const assemblyLines = ref([
  'sub rsp, 0x28',
  'lea rcx,[rip+0x9c43]',
  'call qword ptr [rip+0x472d]',
  'lea rax,[rip+0x4c0e]',
  'mov dword ptr [rip+0x3d78],1',
  'lea rk, [rip+0x3455]',
  'mov qword ptr [rip+0x9cle],rax',
  'add rsp,0x28',
  'jmp 0x140003762'
]);

const decompiledCode = ref(`if (accountBalance < 0) {
  printf("账户余额不足，请及时充值");
}`);

const explanation = ref({
  zh: "根据英文函数语义搜索，如：python",
  en: "Search based on function semantics, e.g.: python"
});

const activeFunction = ref(0);
const language = ref('zh');

function selectFunction(index) {
  activeFunction.value = index;
}
</script>

<template>
  <div class="decompiler-content">
    <h5>Dify1 反编译分析界面</h5>
    <p v-if="currentConversationId">当前会话 ID: {{ currentConversationId }}</p>
    
    <div class="decompiler-layout">
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
            <span class="address">{{ func.address }}:</span>
            <span class="name">{{ func.name }}</span>
          </div>
        </div>
      </div>

      <!-- 中间汇编代码 -->
      <div class="assembly-code">
        <div class="code-content">
          <div v-for="(line, index) in assemblyLines" :key="index" class="code-line">
            <span class="line-number">{{ index + 1 }}</span>
            <span class="instruction">{{ line }}</span>
          </div>
        </div>
      </div>

      <!-- 右侧反编译代码 -->
      <div class="decompiled-code">
        <div class="code-content">
          <pre>{{ decompiledCode }}</pre>
        </div>
        <div class="code-explanation">
          <div class="explanation-header">
            <span>代码解释</span>
            <select v-model="language">
              <option value="zh">简体中文</option>
              <option value="en">English</option>
            </select>
          </div>
          <div class="explanation-content">
            {{ explanation[language] }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 复制原有反编译样式 */
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
.assembly-code,
.decompiled-code {
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
  width: 350px;
}

.code-line {
  display: flex;
  padding: 3px 10px;
  font-size: 14px;
}

.code-line:hover {
  background-color: #2d3748;
}

.line-number {
  color: #718096;
  width: 30px;
  text-align: right;
  margin-right: 10px;
}

.decompiled-code {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.code-content {
  flex: 1;
  padding: 10px;
  overflow: auto;
  white-space: pre-wrap;
  background-color: #1a1d23;
}

.code-explanation {
  border-top: 1px solid #2d3748;
  height: 200px;
}

.explanation-header {
  padding: 10px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #2d3748;
}

.explanation-content {
  padding: 10px;
  height: calc(100% - 40px);
  overflow: auto;
  font-size: 14px;
}

select {
  padding: 3px;
  border: 1px solid #2d3748;
  border-radius: 3px;
  background-color: #1a1d23;
  color: #e2e8f0;
}
</style>