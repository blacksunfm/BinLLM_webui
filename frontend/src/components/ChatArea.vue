<script setup>
import { ref, watch, nextTick } from 'vue';
import ChatMessage from './ChatMessage.vue';
import MessageInput from './MessageInput.vue';
import * as api from '../services/api.js';

const props = defineProps({
  messages: {
    type: Array,
    required: true,
    default: () => []
  },
  isLoading: {
    type: Boolean,
    default: false
  },
  isGenerating: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['send-message', 'stop-generating', 'resize', 'analysis-result']);
const messagesContainer = ref(null);

//拖拽宽度
const isResizing = ref(false);
const startX = ref(0);
const startWidth = ref(0);
const chatWidth = ref(50);

function handleSendMessage(message, fileIds) {
  emit('send-message', message, fileIds);
}

function handleStopGenerating() {
  emit('stop-generating');
}

async function handleAnalyzeBinary(binaryFiles) {
  for (const file of binaryFiles) {
    try {
      const res = await api.analyzeBinary(file.name);
      console.log('分析结果:', res);
      // 自动保存为json
      const blob = new Blob([JSON.stringify(res, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${file.name}_analysis.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      // 传递分析结果给父组件
      emit('analysis-result', res.analysis || res);
    } catch (err) {
      console.error('分析失败:', err);
    }
  }
}

function startResize(e){
  isResizing.value = true;
  startX.value = e.clientX;
  startWidth.value = chatWidth.value;
  document.addEventListener('mousemove', handleResize);
  document.addEventListener('mouseup',stopResize);
  document.body.classList.add('resizing');
  e.preventDefault();
}

function handleResize(e) {
  if (!isResizing.value) return;
  const deltaX = e.clientX - startX.value;
  const newWidth = Math.min(Math.max(startWidth.value + deltaX, 200), 800);
  emit('resize', newWidth);
  e.preventDefault();
}

function stopResize() {
  isResizing.value = false;
  document.removeEventListener('mousemove', handleResize);
  document.removeEventListener('mouseup', stopResize);
  document.body.classList.remove('resizing');
}

watch(() => props.messages, async () => {
  await nextTick();
  const container = messagesContainer.value;
  if (container) {
    container.scrollTop = container.scrollHeight;
  }
}, { deep: true });
</script>

<template>
  <div class="chat-area-component">
    <div 
      class="resize-handle left"
      @mousedown="startResize"
      title="拖拽调整宽度"
    ></div>

    <div v-if="isLoading" class="loading-indicator">加载历史记录...</div>
    
    <div class="messages" ref="messagesContainer">
      <ChatMessage 
        v-for="(message, index) in messages" 
        :key="message.id || index" 
        :message="message"
      />
    </div>
    
    <MessageInput
      :is-input-disabled="isGenerating"
      :is-generating="isGenerating"
      @send-message="handleSendMessage"
      @stop-generating="handleStopGenerating"
      @analyze-binary="handleAnalyzeBinary"
    />
  </div>
</template>

<style scoped>
.chat-area-component {
  flex:4;
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: #1a1a1e;
  position: relative;
}

.resize-handle {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 4px;
  background: transparent;
  cursor: col-resize;
  z-index: 10;
  transition: background 0.2s ease;
}


.resize-handle.left {
  left: -2px;
}

.resize-handle:hover,
.resize-handle:active {
  background: #2563eb;
}

.loading-indicator {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: #aaa;
  font-size: 0.9em;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.messages::-webkit-scrollbar {
  width: 8px;
}

.messages::-webkit-scrollbar-track {
  background: #1a1a1e;
}

.messages::-webkit-scrollbar-thumb {
  background: #444;
  border-radius: 4px;
}

.messages::-webkit-scrollbar-thumb:hover {
  background: #555;
}

</style> 

<style>
/* 全局拖拽样式 */
body.resizing {
  cursor: col-resize !important;
  user-select: none !important;
}
</style>