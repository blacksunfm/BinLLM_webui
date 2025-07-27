<script setup>
import { onMounted, onBeforeUnmount, ref } from 'vue';
// 导入组件
import LeftSidebar from './components/LeftSidebar.vue';
import HistorySidebar from './components/HistorySidebar.vue';
import ChatArea from './components/ChatArea.vue';
import AnalysisArea from './components/AnalysisArea.vue';
// ConfigModal is no longer imported or used
// 导入存储
import store from './store';

const chatWidth = ref(50); // 默认50%宽度

// 添加定时刷新会话列表的功能
let refreshInterval = null;

const handleChatResize = (width) => {
  chatWidth.value = width;
};

// 事件处理
const handleModelChange = async (modelId) => {
  await store.selectModel(modelId);
};

const handleNewChat = async () => {
  await store.createNewChat();
};

const handleSelectConversation = async (conversationId) => {
  await store.selectConversation(conversationId);
};

// handleSaveConfig removed

const handleSendMessage = async (queryText, fileIds = []) => {
  const isFirstMessage = store.currentMessages.value.length === 0;
  await store.sendMessage(queryText, fileIds);

  // 如果是第一条消息，自动生成标题
  if (isFirstMessage) {
    // 这里以用户问题的前20个字作为标题示例
    const title = queryText.slice(0, 15) + '...';
    await store.renameConversation(store.state.currentConversationId, title);
  }
};

const handleStopGenerating = () => {
  store.stopGeneratingResponse();
};

const handleDeleteConversation = async (conversationId) => {
  try {
    await store.deleteConversation(conversationId);
    console.log(`删除对话成功: ${conversationId}`);
  } catch (error) {
    alert(`删除对话失败: ${error.message}`);
  }
};

const analysisAreaRef = ref(null);
const analysisAreaCollapsed = ref(false);

function handleAnalysisResult(data) {
  if (analysisAreaRef.value && typeof analysisAreaRef.value.setAnalysisData === 'function') {
    analysisAreaRef.value.setAnalysisData(data);
  }
}

function handleToggleAnalysisArea(collapsed) {
  analysisAreaCollapsed.value = collapsed;
}

onMounted(async () => {
  // Initialize
  // store.checkBackendConfig(); // No longer needed
  await store.fetchConversations();
  
  // Create a new chat if none exist
  if (store.conversations.value.length === 0) {
    await store.createNewChat();
  } else {
    // Select the latest conversation
    const latestConversation = store.conversations.value[0];
    if (latestConversation) {
      await store.selectConversation(latestConversation.id);
    }
  }
  
  // Set up interval refresh
  refreshInterval = setInterval(async () => {
    if (!store.state.isLoadingConversations && !store.state.isLoadingHistory) {
      await store.fetchConversations();
    }
  }, 30000);
});

onBeforeUnmount(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval);
  }
});
</script>

<template>
  <div class="main-layout">
    <!-- 收起分析区时显示左侧栏和历史栏，flex:2:2:6 -->
    <LeftSidebar 
      v-if="analysisAreaCollapsed"
      style="flex:1"
      :models="store.state.models" 
      :selectedModel="store.state.selectedModel" 
      @select-model="handleModelChange"
    />
    <HistorySidebar 
      v-if="analysisAreaCollapsed"
      style="flex:3"
      :conversations="store.conversations.value" 
      :currentConversationId="store.state.currentConversationId" 
      :isLoading="store.state.isLoadingConversations" 
      @new-chat="handleNewChat" 
      @select-conversation="handleSelectConversation"
      @delete-conversation="handleDeleteConversation"
      @rename-conversation="store.renameConversation"
    />
    <!-- 对话区始终显示，flex 根据状态切换 -->
    <ChatArea 
      :messages="store.currentMessages.value" 
      :isLoading="store.state.isLoadingHistory"
      :isGenerating="store.isCurrentConversationSending.value"
      @send-message="handleSendMessage"
      @stop-generating="handleStopGenerating"
      @resize="handleChatResize"
      @analysis-result="handleAnalysisResult"
      :style="analysisAreaCollapsed ? { flex: 7 } : { flex: 1 }"
    />
    <!-- 展开分析区时只显示对话区和分析区，flex:1:3 -->
    <AnalysisArea 
      v-if="!analysisAreaCollapsed"
      ref="analysisAreaRef"
      :currentConversationId="store.state.currentConversationId"
      :currentModel="store.state.selectedModel"
      style="flex:3"
    />
    <!-- 悬浮按钮 -->
    <div 
      class="fixed-toggle-btn"
      @click="analysisAreaCollapsed = !analysisAreaCollapsed"
      :title="analysisAreaCollapsed ? '展开分析区' : '收起分析区'"
    >
      <svg v-if="analysisAreaCollapsed" width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M15 6L9 12L15 18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
      </svg>
      <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M9 6L15 12L9 18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
      </svg>
    </div>
  </div>
</template>

<style scoped>
.main-layout {
  display: flex;
  height: 100vh;
  min-height: 0;
  width: 100%;
  background-color: #1e1e1e;
  color: #e0e0e0;
  position: relative;
}
.main-layout > * {
  flex-shrink: 1;
  min-width: 0;
  min-height: 0;
}
.fixed-toggle-btn {
  position: fixed;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  background-color: #2563eb;
  color: white;
  padding: 12px 6px;
  border-radius: 4px 0 0 4px;
  cursor: pointer;
  z-index: 200;
  box-shadow: -2px 0 8px rgba(0, 0, 0, 0.1);
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}
.fixed-toggle-btn:hover {
  background-color: #1d4ed8;
  padding-right: 8px;
}
</style>