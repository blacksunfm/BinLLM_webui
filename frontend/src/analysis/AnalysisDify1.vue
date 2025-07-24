<script setup>
import { ref, computed } from 'vue';

defineProps({
  currentConversationId: {
    type: String,
    default: null
  }
});

// 直接内联JSON数据
const decompilationData = ref({
  "functions": [
    {
      "signature": "undefined8 __fastcall FUN_140001081(void)", 
      "disassembly": [
        {
          "address": "0x140001080", 
          "code": "LEA RAX,[0x140005e58]"
        }, 
        {
          "address": "0x140001087", 
          "code": "RET"
        }
      ], 
      "name": "FUN_140001080", 
      "entry_point": "0x140001080"
    }, 
    {
      "signature": "CWinApp * __fastcall FUN_140001090(CWinApp * param_1, uint param_2)", 
      "disassembly": [
        {
          "address": "0x140001090", 
          "code": "MOV qword ptr [RSP + 0x8],RBX"
        }, 
        {
          "address": "0x140001095", 
          "code": "PUSH RDI"
        }, 
        {
          "address": "0x140001096", 
          "code": "SUB RSP,0x20"
        }, 
        {
          "address": "0x14000109a", 
          "code": "MOV EDI,EDX"
        }, 
        {
          "address": "0x14000109c", 
          "code": "MOV RBX,RCX"
        }, 
        {
          "address": "0x14000109f", 
          "code": "CALL qword ptr [0x140005738]"
        }, 
        {
          "address": "0x1400010a5", 
          "code": "TEST DIL,0x1"
        }, 
        {
          "address": "0x1400010a9", 
          "code": "JZ 0x1400010d2"
        }, 
        {
          "address": "0x1400010ab", 
          "code": "MOV RCX,RBX"
        }, 
        {
          "address": "0x1400010ae", 
          "code": "TEST DIL,0x4"
        }, 
        {
          "address": "0x1400010b2", 
          "code": "JNZ 0x1400010c8"
        }, 
        {
          "address": "0x1400010b4", 
          "code": "CALL qword ptr [0x1400058a0]"
        }, 
        {
          "address": "0x1400010ba", 
          "code": "MOV RAX,RBX"
        }, 
        {
          "address": "0x1400010bd", 
          "code": "MOV RBX,qword ptr [RSP + 0x30]"
        }, 
        {
          "address": "0x1400010c2", 
          "code": "ADD RSP,0x20"
        }, 
        {
          "address": "0x1400010c6", 
          "code": "POP RDI"
        }, 
        {
          "address": "0x1400010c7", 
          "code": "RET"
        }, 
        {
          "address": "0x1400010c8", 
          "code": "MOV EDX,0x178"
        }, 
        {
          "address": "0x1400010cd", 
          "code": "CALL 0x140001350"
        }, 
        {
          "address": "0x1400010d2", 
          "code": "MOV RAX,RBX"
        }, 
        {
          "address": "0x1400010d5", 
          "code": "MOV RBX,qword ptr [RSP + 0x30]"
        }, 
        {
          "address": "0x1400010da", 
          "code": "ADD RSP,0x20"
        }, 
        {
          "address": "0x1400010de", 
          "code": "POP RDI"
        }, 
        {
          "address": "0x1400010df", 
          "code": "RET"
        }
      ], 
      "name": "FUN_140001090", 
      "entry_point": "0x140001090"
    }
  ]
});

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
  return decompilationData.value.functions[activeFunction.value];
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
            <span class="address">{{ func.entry_point }}:</span>
            <span class="name">{{ func.name }}</span>
          </div>
        </div>
      </div>

      <!-- 中间汇编代码 -->
      <div class="assembly-code">
        <div class="code-header">
          <h4>汇编代码 - {{ currentFunction.name }}</h4>
          <span class="signature">{{ currentFunction.signature }}</span>
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

      <!-- 右侧反编译代码 (暂时保留但隐藏) -->
      <div class="decompiled-code" style="display: none;">
        <!-- 反编译代码区域暂时隐藏 -->
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
</style>