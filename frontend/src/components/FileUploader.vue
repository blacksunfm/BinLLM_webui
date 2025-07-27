<script setup>
import { ref, computed } from 'vue';
import * as api from '../services/api.js';
import store from '../store';

const props = defineProps({
  isInputDisabled: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['upload-complete', 'upload-error']);

const fileInputRef = ref(null);
const selectedFiles = ref([]);
const isUploading = ref(false);
const uploadError = ref('');

const closeIcon = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width="16" height="16"><path d="M18.3 5.71a.996.996 0 0 0-1.41 0L12 10.59 7.11 5.7A.996.996 0 1 0 5.7 7.11L10.59 12 5.7 16.89a.996.996 0 1 0 1.41 1.41L12 13.41l4.89 4.89a.996.996 0 1 0 1.41-1.41L13.41 12l4.89-4.89c.38-.38.38-1.02 0-1.4z"/></svg>`;

const hasPendingFiles = computed(() => {
  return selectedFiles.value.filter(f => f.status === 'pending').length > 0;
});

function handleFileSelect(event) {
  const files = event.target.files;
  if (files) {
    const newFiles = Array.from(files).map(file => ({
      file,
      status: 'pending',
      error: null,
      id: null,
      key: `file_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    }));
    selectedFiles.value = [...selectedFiles.value, ...newFiles];
    uploadError.value = '';
  }
  if (fileInputRef.value) {
    fileInputRef.value.value = '';
  }
}

function removeSelectedFile(fileKey) {
  selectedFiles.value = selectedFiles.value.filter(f => f.key !== fileKey);
}

async function handleMultipleFileUploads() {
  const filesToUpload = selectedFiles.value.filter(f => f.status === 'pending' || f.status === 'error');
  if (filesToUpload.length === 0 || !store.state.currentConversationId) return;

  isUploading.value = true;
  uploadError.value = '';

  filesToUpload.forEach(f => f.status = 'uploading');

  const uploadPromises = filesToUpload.map(async (fileWrapper) => {
    try {
      const result = await api.uploadFile(
        fileWrapper.file,
        store.state.currentConversationId,
        store.state.selectedModel,
        'vue-app-user'
      );
      if (result.type === 'binary') {
        fileWrapper.status = 'success';
        fileWrapper.id = result.name;
        return { type: 'binary', name: result.name, file_path: result.file_path };
      } else {
      fileWrapper.status = 'success';
      fileWrapper.id = result.file_id;
        return { type: 'dify', file_id: result.file_id };
      }
    } catch (error) {
      console.error(`文件 ${fileWrapper.file.name} 上传失败:`, error);
      fileWrapper.status = 'error';
      fileWrapper.error = error.message || '上传失败';
      return null;
    }
  });

  try {
    const results = await Promise.all(uploadPromises);
    const successfulFiles = results.filter(r => r !== null);

    if (successfulFiles.length > 0) {
      emit('upload-complete', successfulFiles);
      selectedFiles.value = selectedFiles.value.filter(f => f.status !== 'success');
    } else {
      uploadError.value = "所有文件上传失败，请检查文件或网络后重试。";
      emit('upload-error', uploadError.value);
    }
  } catch (overallError) {
    console.error("处理文件上传时发生意外错误:", overallError);
    uploadError.value = "处理上传时发生未知错误。";
    emit('upload-error', uploadError.value);
    selectedFiles.value.filter(f => f.status === 'uploading').forEach(f => {
      f.status = 'error';
      f.error = '未知处理错误';
    });
  } finally {
    isUploading.value = false;
  }
}

function triggerFileInput() {
  if (fileInputRef.value) {
    fileInputRef.value.click();
  }
}

defineExpose({
  handleMultipleFileUploads,
  hasPendingFiles,
  isUploading,
  triggerFileInput
});
</script>

<template>
  <div class="file-uploader">
    <input 
      type="file" 
      ref="fileInputRef"
      @change="handleFileSelect" 
      class="hidden-file-input"
      accept=".txt,.pdf,.docx,.doc,.md,.jpg,.jpeg,.png,.csv,.xlsx,.xls,.exe,.bin"
      :disabled="isInputDisabled"
      multiple
    >
    
    <div v-if="uploadError" class="upload-error">
      <span>{{ uploadError }}</span>
      <button @click="uploadError = ''" class="close-error" title="关闭" v-html="closeIcon"></button>
    </div>
    
    <div v-if="selectedFiles.length > 0" class="file-list-container">
      <div v-for="fileWrapper in selectedFiles" :key="fileWrapper.key" class="file-item" :class="fileWrapper.status">
        <div class="file-item-info">
          <span class="file-icon">📄</span>
          <span class="file-item-name" :title="fileWrapper.file.name">{{ fileWrapper.file.name }}</span>
          <span class="file-item-size">({{ (fileWrapper.file.size / 1024).toFixed(1) }} KB)</span>
        </div>
        <div class="file-item-status">
          <span v-if="fileWrapper.status === 'pending'" class="status-pending">待上传</span>
          <span v-if="fileWrapper.status === 'uploading'" class="status-uploading">上传中...</span>
          <span v-if="fileWrapper.status === 'success'" class="status-success">成功</span> 
          <span v-if="fileWrapper.status === 'error'" class="status-error" :title="fileWrapper.error">失败</span>
          <button 
            @click="removeSelectedFile(fileWrapper.key)" 
            class="remove-file-button" 
            title="移除文件" 
            :disabled="fileWrapper.status === 'uploading'" 
            v-html="closeIcon">
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.file-uploader {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.hidden-file-input {
  display: none;
}

.file-list-container {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.file-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background-color: #3a3a3f;
  padding: 8px 15px;
  border-radius: 5px;
}

.file-item-info {
  display: flex;
  align-items: center;
  gap: 8px;
  overflow: hidden;
}

.file-icon {
  flex-shrink: 0;
}

.file-item-name {
  font-weight: 500;
  color: #ddd;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-item-size {
  color: #aaa;
  font-size: 0.85em;
  flex-shrink: 0;
}

.file-item-status {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-pending {
  color: #ff9e9e;
}

.status-uploading {
  color: #ff9e9e;
}

.status-success {
  color: #9e9e9e;
}

.status-error {
  color: #ff9e9e;
}

.remove-file-button {
  background: none;
  border: none;
  color: #888;
  cursor: pointer;
  padding: 4px;
  border-radius: 50%;
  flex-shrink: 0;
}

.remove-file-button:hover:not(:disabled) {
  color: #fff;
  background-color: rgba(255,255,255,0.1);
}

.remove-file-button:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.upload-error {
  background-color: #532724;
  color: #ff9e9e;
  padding: 10px 15px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 1px solid #733a37;
  font-size: 0.9em;
}

.upload-error span {
  flex-grow: 1;
  margin-right: 10px;
}

.close-error {
  background: none;
  border: none;
  color: #ff9e9e;
  cursor: pointer;
  padding: 4px;
  border-radius: 50%;
  flex-shrink: 0;
}

.close-error:hover {
  background-color: rgba(255,255,255,0.1);
}
</style> 