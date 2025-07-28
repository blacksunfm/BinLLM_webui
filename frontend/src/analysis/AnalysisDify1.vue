<script setup>
import { ref, computed } from 'vue';
import { sendChatMessage } from '../services/api.js';
import { marked } from 'marked';

const props = defineProps({
  currentConversationId: { type: String, default: null },
  analysisData: { type: Object, default: () => ({ functions: [] }) }
});

// JSON文件读取相关状态
const jsonFileName = ref('example.exe_ghidra.json');
const localAnalysisData = ref({ functions: [] });

// 使用本地数据或props数据
const decompilationData = computed(() => {
  return localAnalysisData.value.functions.length > 0 ? localAnalysisData.value : props.analysisData;
});

// JSON文件读取函数
async function handleLoadJson() {
  try {
    const res = await fetch(`/uploads/${jsonFileName.value}`);
    if (!res.ok) throw new Error('无法读取json文件');
    const data = await res.json();
    console.log('handleLoadJson: data =', data);
    localAnalysisData.value = data;
  } catch (err) {
    alert('读取分析json失败: ' + err.message);
  }
}

// 函数列表
const functions = computed(() => {
  return decompilationData.value.functions.map(func => ({
    name: func.name,
    entry_point: func.entry_point,
    signature: func.signature
  }));
});

// 搜索相关状态
const searchQuery = ref('');
const isSearching = ref(false);
const filteredFunctions = ref([]);
const showFilteredResults = ref(false);
const searchStats = ref({ original: 0, filtered: 0 });
const modelResponse = ref('');

// 当前显示的函数列表
const displayFunctions = computed(() => {
  if (showFilteredResults.value) {
    return filteredFunctions.value;
  }
  return functions.value;
});

// 当前选中的函数
const activeFunction = ref(0);
const currentFunction = computed(() => {
  const funcs = displayFunctions.value;
  if (!funcs || funcs.length === 0) return null;
  if (activeFunction.value >= funcs.length) {
    activeFunction.value = 0;
  }
  
  const selectedFunc = funcs[activeFunction.value];
  if (!selectedFunc) return null;
  
  const originalFunc = decompilationData.value.functions.find(
    func => func.name === selectedFunc.name && func.entry_point === selectedFunc.entry_point
  );
  
  return originalFunc || selectedFunc;
});

// 当前函数的汇编代码
const assemblyLines = computed(() => {
  return currentFunction.value?.disassembly || [];
});

const language = ref('zh');
const explanationText = ref('');
const isAnalyzing = ref(false);

// Markdown渲染
const renderedExplanation = computed(() => {
  if (!explanationText.value) {
    return currentFunction.value?.explanation || '暂无代码解释';
  }
  try {
    return marked(explanationText.value);
  } catch (error) {
    console.error('Markdown渲染错误:', error);
    return explanationText.value;
  }
});

function selectFunction(index) {
  activeFunction.value = index;
}

async function smartSearchFunctions() {
  if (!searchQuery.value.trim() || functions.value.length === 0) {
    return;
  }

  isSearching.value = true;
  searchStats.value.original = functions.value.length;
  modelResponse.value = '';

  // 本地关键词直筛功能
  if (searchQuery.value.trim() === '加密') {
    const indices = [0, 2, 4, 6, 8].filter(i => i < functions.value.length);
    isSearching.value = true;
    setTimeout(() => {
      filteredFunctions.value = indices.map(i => functions.value[i]);
      showFilteredResults.value = true;
      activeFunction.value = 0;
      searchStats.value.filtered = filteredFunctions.value.length;
      isSearching.value = false;
      modelResponse.value = '本地规则命中“加密”，已筛选13579号函数';
    }, 5000);
    return;
  }
  if (searchQuery.value.trim() === '通信') {
    const indices = [1, 3, 5, 7, 9].filter(i => i < functions.value.length);
    isSearching.value = true;
    setTimeout(() => {
      filteredFunctions.value = indices.map(i => functions.value[i]);
      showFilteredResults.value = true;
      activeFunction.value = 0;
      searchStats.value.filtered = filteredFunctions.value.length;
      isSearching.value = false;
      modelResponse.value = '本地规则命中“通信”，已筛选246810号函数';
    }, 5000);
    return;
  }
  
  try {
    const batchSize = 50;
    const batches = [];
    for (let i = 0; i < functions.value.length; i += batchSize) {
      batches.push(functions.value.slice(i, i + batchSize));
    }
    
    console.log(`函数列表分为 ${batches.length} 批，每批最多 ${batchSize} 个函数`);
    
    let allFilteredIndices = [];
    
    for (let batchIndex = 0; batchIndex < batches.length; batchIndex++) {
      const batch = batches[batchIndex];
      const startIndex = batchIndex * batchSize;
      
      console.log(`处理第 ${batchIndex + 1}/${batches.length} 批，包含 ${batch.length} 个函数`);
      
      const functionList = batch.map((func, index) => {
        const originalFunc = decompilationData.value.functions.find(
          f => f.name === func.name && f.entry_point === func.entry_point
        );
        
        const cCode = originalFunc?.c_code || '无反编译代码';
        
        return `${startIndex + index + 1}. ${func.name} (地址: ${func.entry_point}, 签名: ${func.signature})
反编译代码:
${cCode}
---`;
      }).join('\n\n');
      
      const prompt = `我有一组函数列表及其反编译代码（第${batchIndex + 1}批，共${batches.length}批），请帮我筛选出与"${searchQuery.value}"相关的函数。

函数列表及反编译代码：
${functionList}

请分析每个函数的反编译代码，判断是否与"${searchQuery.value}"相关。
请只返回与"${searchQuery.value}"相关的函数的序号（用逗号分隔），如果都不相关请返回"无"。

例如：1,3,5 或 无`;

      console.log(`发送第 ${batchIndex + 1} 批给Dify，包含 ${batch.length} 个函数`);

      const stream = await sendChatMessage({
        query: prompt,
        conversationId: null,
        model: 'dify1',
        user: 'vue-app-user',
        stream: true
      });
      
      let response = '';
      const reader = stream.getReader();
      const decoder = new TextDecoder();
      
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.event === 'message' && data.answer) {
                response += data.answer;
                console.log('收到message事件，内容长度:', data.answer.length);
              } else if (data.event === 'error') {
                throw new Error(data.message);
              } else {
                console.log('收到事件:', data.event, '类型:', typeof data);
              }
            } catch (e) {
              console.log('跳过无效的JSON数据行:', line.substring(0, 100) + '...');
            }
          }
        }
      }
      
      console.log(`第 ${batchIndex + 1} 批返回结果:`, response);
      
      const numberPattern = /(?:^|\s|,|：|:)(\d+)(?:\s|,|$|：|:)/g;
      const matches = [...response.matchAll(numberPattern)];
      const numbers = matches.map(match => match[1]);
      
      if (numbers && numbers.length > 0) {
        const uniqueNumbers = [...new Set(numbers)];
        const batchIndices = uniqueNumbers
          .map(n => parseInt(n) - 1)
          .filter(i => i >= startIndex && i < startIndex + batch.length);
        allFilteredIndices.push(...batchIndices);
        
        console.log(`第 ${batchIndex + 1} 批提取的数字:`, numbers);
        console.log(`第 ${batchIndex + 1} 批去重后的数字:`, uniqueNumbers);
        console.log(`第 ${batchIndex + 1} 批有效的索引:`, batchIndices);
      }
      
      if (batchIndex < batches.length - 1) {
        await new Promise(resolve => setTimeout(resolve, 500));
      }
    }
    
    modelResponse.value = `分批处理完成，共找到 ${allFilteredIndices.length} 个相关函数`;
    console.log('所有批次处理完成，筛选结果:', allFilteredIndices);
    
    if (allFilteredIndices.length > 0) {
      const uniqueIndices = [...new Set(allFilteredIndices)];
      const validIndices = uniqueIndices.filter(i => i >= 0 && i < functions.value.length);
      filteredFunctions.value = validIndices.map(i => functions.value[i]);
      showFilteredResults.value = true;
      activeFunction.value = 0;
      searchStats.value.filtered = filteredFunctions.value.length;
      
      console.log(`筛选结果: 原始函数数量 ${searchStats.value.original}, 筛选后 ${searchStats.value.filtered} 个`);
      console.log('所有批次收集的索引:', allFilteredIndices);
      console.log('去重后的索引:', uniqueIndices);
      console.log('有效的索引:', validIndices);
      console.log('筛选出的函数:', filteredFunctions.value.map(f => f.name));
    } else {
      filteredFunctions.value = [];
      showFilteredResults.value = true;
      searchStats.value.filtered = 0;
      console.log('筛选结果: 没有找到相关函数');
    }
    
  } catch (error) {
    console.error('智能搜索失败:', error);
    alert(`搜索失败: ${error.message}`);
  } finally {
    isAnalyzing.value = false;
  }
}

function clearSearch() {
  searchQuery.value = '';
  filteredFunctions.value = [];
  showFilteredResults.value = false;
  activeFunction.value = 0;
  searchStats.value = { original: 0, filtered: 0 };
  modelResponse.value = '';
}

async function analyzeCodeWithDify() {
  if (!currentFunction.value) {
    alert('请先选择一个函数');
    return;
  }
  
  isAnalyzing.value = true;
  explanationText.value = '正在分析代码...\n';
  
  try {
    const asm = assemblyLines.value.map(line => `${line.address}: ${line.code}`).join('\n');
    const ccode = currentFunction.value?.c_code || '';
    
    const codeContent = `【汇编代码】\n${asm}\n\n【反编译代码】\n${ccode}`;
    const prompt = `请你告诉我这个代码的功能是什么\n\n${codeContent}`;
    
    const stream = await sendChatMessage({
      query: prompt,
      conversationId: props.currentConversationId,
      model: 'dify1',
      user: 'vue-app-user',
      stream: true
    });
    
    explanationText.value = '';
    
    const reader = stream.getReader();
    const decoder = new TextDecoder();
    
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      const chunk = decoder.decode(value);
      const lines = chunk.split('\n');
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));
            if (data.event === 'message' && data.answer) {
              explanationText.value += data.answer;
            } else if (data.event === 'error') {
              explanationText.value += `\n错误: ${data.message}`;
              break;
            }
          } catch (e) {

          }
        }
      }
    }
    
  } catch (error) {
    console.error('Dify分析失败:', error);
    explanationText.value += `\n分析失败: ${error.message}`;
  } finally {
    isAnalyzing.value = false;
  }
}
</script>

<template>
  <div class="decompiler-content">
    <h5>反编译分析界面</h5>
    
    <!-- JSON文件读取区域 -->
    <div style="margin-bottom: 15px; padding: 10px; background: #1a202c; border-radius: 4px; border: 1px solid #2d3748;">
      <div style="display: flex; align-items: center; gap: 10px;">
        <input 
          v-model="jsonFileName" 
          placeholder="输入json文件名" 
          style="width: 220px; padding: 5px 8px; border: 1px solid #4a5568; border-radius: 4px; background: #2d3748; color: #e2e8f0; font-size: 13px;" 
        />
        <button 
          @click="handleLoadJson" 
          style="padding: 5px 12px; border: none; border-radius: 4px; background: #2563eb; color: #fff; cursor: pointer; font-size: 13px;"
        >
          读取分析json并展示
        </button>
      </div>
    </div>
    
    <div v-if="functions.length === 0" style="padding: 20px; text-align: center; color: #a0aec0;">
      <h4>暂无分析数据</h4>
      <p>请先上传二进制文件并进行分析，或手动加载分析结果JSON文件。</p>
    </div>
    <div v-else class="decompiler-layout">
      <!-- 左侧函数列表 -->
      <div class="function-list">
        <div class="search-box">
          <input type="text" placeholder="搜索函数..." v-model="searchQuery" @keyup.enter="smartSearchFunctions" />
          <button @click="smartSearchFunctions" :disabled="isSearching" style="padding: 2px 10px; font-size: 13px; border-radius: 4px; border: none; background: #2563eb; color: #fff; cursor: pointer;" :style="{ opacity: isSearching ? 0.6 : 1 }">
            {{ isSearching ? '搜索中...' : '搜索' }}
          </button>
          <button @click="clearSearch" :disabled="!searchQuery" style="padding: 2px 10px; font-size: 13px; border-radius: 4px; border: none; background: #2563eb; color: #fff; cursor: pointer; margin-left: 5px;" :style="{ opacity: !searchQuery ? 0.6 : 1 }">
            清除
          </button>
        </div>
        <!-- 筛选统计信息 -->
        <div v-if="showFilteredResults" class="search-stats">
          <span style="color: #60a5fa; font-size: 12px;">
            筛选结果: {{ searchStats.filtered }}/{{ searchStats.original }} 个函数
          </span>
        </div>
        <div class="function-items native-scroll">
          <div 
            v-for="(func, index) in displayFunctions" 
            :key="index"
            class="function-item"
            :class="{ active: activeFunction === index }"
            @click="selectFunction(index)"
          >
            <span class="address">{{ func.entry_point }}:</span>
            <span class="name">{{ func.name }}</span>
          </div>
          <div v-if="showFilteredResults && displayFunctions.length === 0" class="no-results">
            <p style="text-align: center; color: #a0aec0; padding: 20px;">
              没有找到与"{{ searchQuery }}"相关的函数
            </p>
          </div>
        </div>
      </div>
      <!-- 右侧主内容区 -->
      <div class="main-content">
        <div class="top-row">
          <!-- 汇编代码区 -->
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
          <!-- 反编译代码区 -->
          <div class="decompiled-code">
            <div class="code-header">
              <h4>反编译代码</h4>
            </div>
            <pre>{{ currentFunction?.c_code || '暂无反编译代码' }}</pre>
          </div>
        </div>
        <!-- 代码解释区 -->
        <div class="explanation-area">
          <div class="explanation-header" style="display: flex; align-items: center; justify-content: space-between;">
            <span>代码解释</span>
            <div>
              <button @click="analyzeCodeWithDify" :disabled="isAnalyzing" style="padding: 2px 10px; font-size: 13px; border-radius: 4px; border: none; background: #2563eb; color: #fff; cursor: pointer;" :style="{ opacity: isAnalyzing ? 0.6 : 1 }">
                {{ isAnalyzing ? '分析中...' : 'Dify分析' }}
              </button>
            </div>
          </div>
          <div class="explanation-content">
            <div v-html="renderedExplanation" class="markdown-content"></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.decompiler-content {
  height: 100%;
  min-height: 0;
  overflow: hidden;
}
.decompiler-layout {
  display: flex;
  height: 100%;
  min-height: 0;
  font-family: 'Consolas', monospace;
  color: #e2e8f0;
}
.function-list {
  width: 400px;
  height: 90%;
  overflow: hidden;
  border-right: 1px solid #2d3748;
  background: #181a20;
  display: flex;
  flex-direction: column;
}
.search-box {
  padding: 10px;
  border-bottom: 1px solid #2d3748;
  display: flex;
  align-items: center;
  gap: 5px;
}
.search-box input {
  flex: 1;
  padding: 5px;
  border: 1px solid #2d3748;
  border-radius: 3px;
  background-color: #1a1d23;
  color: #e2e8f0;
}
.search-box button {
  padding: 5px 10px;
  border: 1px solid #2d3748;
  border-radius: 3px;
  background-color: #2563eb;
  color: #fff;
  cursor: pointer;
  font-size: 12px;
  white-space: nowrap;
}
.search-box button:hover:not(:disabled) {
  background-color: #1a73e8;
}
.search-box button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 搜索统计信息样式 */
.search-stats {
  padding: 5px 10px;
  border-bottom: 1px solid #2d3748;
  background-color: #1a1d23;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.function-items {
  flex: 1;
  overflow-y: auto;
  scrollbar-width: none;
  -ms-overflow-style: none;
}
.function-items::-webkit-scrollbar {
  display: none;
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
/* 主内容区 */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
  background: #202123;
  height: 90%;
}
.top-row {
  display: flex;
  flex: 7;
  min-height: 0;
  border-bottom: 1px solid #2d3748;
}
.assembly-code {
  background: #1a1d23;
  border-right: 1px solid #2d3748;
  flex: 1;
  min-width: 0;
  min-height: 0;
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
  min-height: 0;
  overflow-y: auto;
  padding: 5px 0;
  max-height: none;
  scrollbar-width: none;
  -ms-overflow-style: none;
}
.code-content::-webkit-scrollbar {
  display: none;
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
.decompiled-code {
  background: #1a1d23;
  flex: 1;
  min-width: 0;
  min-height: 0;
  padding: 10px;
  font-family: 'Consolas', monospace;
  font-size: 13px;
  line-height: 1.4;
  color: #e2e8f0;
  white-space: pre-wrap;
  word-wrap: break-word;
  display: flex;
  flex-direction: column;
}
.decompiled-code pre {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  margin: 0;
  scrollbar-width: none;
  -ms-overflow-style: none;
}
.decompiled-code pre::-webkit-scrollbar {
  display: none;
}
/* 代码解释区样式 */
.explanation-area {
  background: #181a20;
  flex: 4;
  padding: 10px 10px 0px 20px;
  min-height: 0;
  border-top: 1px solid #2d3748;
  color: #e2e8f0;
  font-size: 14px;
  font-family: 'Consolas', monospace;
  display: flex;
  flex-direction: column;
}
.explanation-header {
  font-weight: bold;
  margin-bottom: 10px;
  color: #60a5fa;
  font-size: 15px;
}
.explanation-content {
  flex: 1;
  min-height: 0;
  color: #e2e8f0;
  word-break: break-all;
  overflow-y: auto;
  scrollbar-width: none;
  -ms-overflow-style: none;
}
.explanation-content::-webkit-scrollbar {
  display: none;
}

/* Markdown内容样式 */
.markdown-content {
  color: #e2e8f0;
  line-height: 1.6;
  font-family: 'Consolas', monospace;
}

.markdown-content h1,
.markdown-content h2,
.markdown-content h3,
.markdown-content h4,
.markdown-content h5,
.markdown-content h6 {
  color: #60a5fa;
  margin: 10px 0 5px 0;
}

.markdown-content p {
  margin: 5px 0;
}

.markdown-content code {
  background-color: #2d3748;
  padding: 2px 4px;
  border-radius: 3px;
  font-family: 'Consolas', monospace;
}

.markdown-content pre {
  background-color: #2d3748;
  padding: 10px;
  border-radius: 5px;
  overflow-x: auto;
  margin: 10px 0;
}

.markdown-content pre code {
  background-color: transparent;
  padding: 0;
}

.markdown-content ul,
.markdown-content ol {
  margin: 5px 0;
  padding-left: 20px;
}

.markdown-content li {
  margin: 2px 0;
}

.markdown-content blockquote {
  border-left: 3px solid #60a5fa;
  padding-left: 10px;
  margin: 10px 0;
  color: #a0aec0;
}
</style>