<script setup>
import { ref, computed } from 'vue';
import FileUploader from './FileUploader.vue';

const props = defineProps({
  isInputDisabled: {
    type: Boolean,
    default: false
  },
  isGenerating: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['send-message', 'stop-generating']);

const internalUserInput = ref('');
const fileUploaderRef = ref(null);

const sendIcon = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width="18" height="18"><path d="M3 13.0001h11.586l-5.293 5.293a1 1 0 1 0 1.414 1.414l7-7a.999.999 0 0 0 0-1.414l-7-7a1 1 0 1 0-1.414 1.414l5.293 5.293H3a1 1 0 1 0 0 2Z"></path></svg>`;
const fileIcon = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width="18" height="18"><path d="M14 13.5V8a1 1 0 0 0-2 0v5.5a3.5 3.5 0 1 0 7 0V8a5.5 5.5 0 0 0-11 0v8.5a1 1 0 0 0 2 0V16a.5.5 0 0 1 1 0v.5a1.5 1.5 0 1 1-3 0V8a3.5 3.5 0 0 1 7 0v5.5a1.5 1.5 0 0 1-3 0Z"></path></svg>`;
const stopIcon = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width="18" height="18"><path d="M7 7h10v10H7z"></path></svg>`;

const isSendDisabled = computed(() => {
  return fileUploaderRef.value?.isUploading || 
         (!internalUserInput.value.trim() && !fileUploaderRef.value?.hasPendingFiles);
});

const isStopDisabled = computed(() => {
  return !props.isGenerating;
});

function handleSend() {
  const messageText = internalUserInput.value.trim();
  if (!messageText && !fileUploaderRef.value?.hasPendingFiles) return;

  internalUserInput.value = '';

  if (fileUploaderRef.value?.hasPendingFiles) {
    fileUploaderRef.value.handleMultipleFileUploads();
  } else {
    emit('send-message', messageText);
  }
}

function handleUploadComplete(fileObjs) {
  const difyFiles = fileObjs.filter(f => f.type === 'dify');
  const binaryFiles = fileObjs.filter(f => f.type === 'binary');
  const messageText = internalUserInput.value.trim();

  // 只把dify文件id传给主聊天
  if (difyFiles.length > 0) {
    emit('send-message', messageText || `我上传了 ${difyFiles.length} 个文件。`, difyFiles.map(f => f.file_id));
  }
  // 二进制文件也发一条消息，并触发分析和弹窗
  if (binaryFiles.length > 0) {
    emit('send-message', messageText || `我上传了 ${binaryFiles.length} 个二进制文件。`, []);
    emit('analyze-binary', binaryFiles);
    alert(`已上传二进制文件：${binaryFiles.map(f => f.name).join(', ')}`);
  }
  internalUserInput.value = '';
}

function handleUploadError(error) {
  console.error('文件上传错误:', error);
}

function handleStop() {
  emit('stop-generating');
}
</script>

<template>
  <div class="message-input">
    <FileUploader
      ref="fileUploaderRef"
      :is-input-disabled="isInputDisabled"
      @upload-complete="handleUploadComplete"
      @upload-error="handleUploadError"
    />
    
    <div class="input-area">
      <textarea
        v-model="internalUserInput"
        @keyup.enter.exact="handleSend" 
        placeholder="输入消息... (Shift+Enter 换行)"
        class="dark-textarea"
        :disabled="isInputDisabled"
        rows="1"
      ></textarea>
      
      <button 
        @click="fileUploaderRef?.triggerFileInput()" 
        class="icon-button file-button" 
        title="附加文件"
        :disabled="isInputDisabled"
        v-html="fileIcon"
      ></button>
      
      <button 
        v-if="!isGenerating"
        @click="handleSend" 
        :disabled="isSendDisabled" 
        class="icon-button send-button" 
        :title="fileUploaderRef?.isUploading ? '正在上传...' : '发送'"
        v-html="sendIcon"
      >
      </button>
      <button
        v-else
        @click="handleStop"
        :disabled="isStopDisabled"
        class="icon-button stop-button"
        title="停止生成"
        v-html="stopIcon"
      >
      </button>
    </div>
  </div>
</template>

<style scoped>
.message-input {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.input-area {
  display: flex;
  align-items: flex-end;
  padding: 10px 15px;
  border-top: 1px solid #444;
  background-color: #2f2f33;
  gap: 10px;
}

.dark-textarea {
  flex-grow: 1;
  padding: 10px 15px;
  border: 1px solid #555;
  border-radius: 20px;
  resize: none;
  background-color: #3b3b40;
  color: #eee;
  min-height: 40px;
  max-height: 150px;
  overflow-y: auto;
  font-family: inherit;
  font-size: 1rem;
  line-height: 1.4;
}

.dark-textarea::placeholder {
  color: #888;
}

.dark-textarea:focus {
  outline: none;
  border-color: #68a2e0;
  box-shadow: 0 0 0 2px rgba(104, 162, 224, 0.3);
}

.dark-textarea:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  background-color: #4a4a50;
}

.icon-button {
  background-color: transparent;
  border: none;
  color: #aaa;
  padding: 8px;
  cursor: pointer;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.2s ease, color 0.2s ease;
  flex-shrink: 0;
  height: 40px;
  width: 40px;
}

.icon-button:hover:not(:disabled) {
  background-color: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.icon-button:focus {
  outline: none;
  box-shadow: 0 0 0 2px rgba(104, 162, 224, 0.3);
}

.icon-button:disabled {
  color: #666;
  cursor: not-allowed;
  background-color: transparent;
  opacity: 0.6;
}

.icon-button svg {
  display: block;
}

.stop-button {
  color: #f87171;
}

.stop-button:hover:not(:disabled) {
  background-color: rgba(248, 113, 113, 0.2);
  color: #ef4444;
}
</style> 