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

// 添加定时刷新会话列表的功能
let refreshInterval = null;

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
  await store.sendMessage(queryText, fileIds);
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
    <!-- Left Sidebar -->
    <LeftSidebar 
      :models="store.state.models" 
      :selectedModel="store.state.selectedModel" 
      @select-model="handleModelChange"
    />

    <!-- History Sidebar -->
    <HistorySidebar 
      :conversations="store.conversations.value" 
      :currentConversationId="store.state.currentConversationId" 
      :isLoading="store.state.isLoadingConversations" 
      @new-chat="handleNewChat" 
      @select-conversation="handleSelectConversation"
      @delete-conversation="handleDeleteConversation"
      @rename-conversation="store.renameConversation"
    />

    <!-- Chat Area -->
    <ChatArea 
      :messages="store.currentMessages.value" 
      :isLoading="store.state.isLoadingHistory"
      :isGenerating="store.isCurrentConversationSending.value"
      @send-message="handleSendMessage"
      @stop-generating="handleStopGenerating"
      :style="{ width: chatWidth + '%' }"
    />

    <!-- Analysis Area -->
    <AnalysisArea 
      :currentConversationId="store.state.currentConversationId"
      :currentModel="store.state.selectedModel"
    />
  </div>
</template>

<style scoped>
/* Main layout styles */
.main-layout {
  display: flex;
  height: 100vh;
  width: 100%;
  overflow: hidden;
  background-color: #1e1e1e; /* Dark background */
  color: #e0e0e0; /* Default light text */
}
</style>
