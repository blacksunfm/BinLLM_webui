<script setup>
import { ref, watch, nextTick } from 'vue';
import ChatMessage from './ChatMessage.vue';
import MessageInput from './MessageInput.vue';

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

const emit = defineEmits(['send-message', 'stop-generating']);
const messagesContainer = ref(null);

function handleSendMessage(message, fileIds) {
  emit('send-message', message, fileIds);
}

function handleStopGenerating() {
  emit('stop-generating');
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
    />
  </div>
</template>

<style scoped>
.chat-area-component {
  flex: 4;
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: #1a1a1e;
  position: relative;
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