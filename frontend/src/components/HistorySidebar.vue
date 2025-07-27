<script setup>
import { ref, computed, nextTick } from 'vue';
import store from '../store'; // 导入 store

const props = defineProps({
  conversations: {
    type: Array,
    required: true,
    default: () => []
  },
  currentConversationId: {
    type: String,
    default: null
  },
  isLoading: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['new-chat', 'select-conversation', 'delete-conversation']);

// 重命名状态
const editingConversationId = ref(null);
const renameInput = ref('');
// 不再使用单个 ref，改为动态获取编辑中的输入框
// const inputRef = ref(null); // 用于聚焦输入框

// 计算属性: 格式化时间戳
function formatTimestamp(timestamp) {
  if (!timestamp) return '';
  const date = new Date(timestamp);
  // 可以根据需要调整格式
  return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

// --- 重命名相关方法 ---
async function startEditing(conversation) {
  editingConversationId.value = conversation.id;
  renameInput.value = conversation.name; // 将当前名称填入输入框
  await nextTick(); // 等待DOM更新
  
  // 使用 querySelector 直接获取当前编辑框元素并聚焦
  const inputElement = document.querySelector('.rename-input');
  if (inputElement) {
    inputElement.focus();
  }
}

function cancelEditing() {
  editingConversationId.value = null;
  renameInput.value = '';
}

async function saveRename(conversationId) {
  const newName = renameInput.value.trim();
  if (!newName || newName === props.conversations.find(c => c.id === conversationId)?.name) {
    // 如果名称为空或未改变，则取消编辑
    cancelEditing();
    return;
  }
  
  const success = await store.renameConversation(conversationId, newName);
  if (success) {
    cancelEditing(); // 成功后退出编辑模式
  } 
  // 失败时，store action 会处理回滚和提示
}

function handleInputKeydown(event, conversationId) {
  if (event.key === 'Enter') {
    event.preventDefault(); // 阻止默认的 Enter 行为 (如换行)
    saveRename(conversationId);
  } else if (event.key === 'Escape') {
    cancelEditing();
  }
}

// --- 其他方法 ---
function selectConversation(id) {
  if (id === editingConversationId.value) return; // 编辑模式下不切换
  emit('select-conversation', id);
}

function deleteConversation(id) {
  if (confirm(`确定要删除对话 "${props.conversations.find(c=>c.id===id)?.name || '此对话'}" 吗？`)) {
    emit('delete-conversation', id);
  }
}

// SVG Icons
const newChatIcon = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width="18" height="18"><path d="M11 11V5h2v6h6v2h-6v6h-2v-6H5v-2h6Z"></path></svg>`;
const editIcon = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" width="14" height="14"><path d="M11.013 1.413a1.75 1.75 0 0 1 2.475 2.474L6.226 11.148A.75.75 0 0 1 5.879 11.3L3.629 12a.75.75 0 0 1-.88-.88l.7-2.248a.75.75 0 0 1 .152-.347L11.013 1.413Zm1.07 1.057a.25.25 0 0 0-.354 0L4.47 9.728a.25.25 0 0 0-.05.116l-.467 1.495 1.495-.467a.25.25 0 0 0 .116-.05l7.252-7.252a.25.25 0 0 0 0-.354Z"></path></svg>`;
const deleteIcon = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" width="14" height="14"><path d="M3.72 3.72a.75.75 0 0 1 1.06 0L8 6.94l3.22-3.22a.75.75 0 1 1 1.06 1.06L9.06 8l3.22 3.22a.75.75 0 1 1-1.06 1.06L8 9.06l-3.22 3.22a.75.75 0 0 1-1.06-1.06L6.94 8 3.72 4.78a.75.75 0 0 1 0-1.06Z"></path></svg>`;
const saveIcon = `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 16 16" stroke-width="1.5" stroke="currentColor" width="14" height="14"><path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6-6m-6 6l6 6" /></svg>`; // Note: Check mark icon used here for simplicity
const cancelIcon = `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 16 16" stroke-width="1.5" stroke="currentColor" width="14" height="14"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>`;

// 添加聊天助手图标
const chatAssistantIcon = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width="16" height="16"><path d="M12 2a9.96 9.96 0 0 1 7.383 16.619 9.906 9.906 0 0 1-6.912 3.373 10.152 10.152 0 0 1-7.53-2.895A9.96 9.96 0 0 1 2 12c0-2.653 1.035-5.147 2.903-7.023C6.78 3.08 9.299 2 12 2Zm-.5 4a.5.5 0 0 0-.5.5v.5h-1a2 2 0 0 0-2 2v1a2 2 0 0 0 2 2h2v2h-3a.5.5 0 0 0 0 1h3v.5a.5.5 0 0 0 1 0V16h3a.5.5 0 0 0 0-1h-3v-2h2a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-1v-.5a.5.5 0 0 0-.5-.5ZM9 9h1v1H9V9Zm4 0h1v1h-1V9Z"/></svg>`;

</script>

<template>
  <div class="history-sidebar-component">
    <div class="sidebar-header">
      <button class="new-chat-button" @click="emit('new-chat')">
        <span v-html="newChatIcon" class="icon"></span>
        新对话
      </button>
    </div>
    
    <div class="conversation-list">
       <div v-if="isLoading" class="loading-text">加载中...</div>
       <div v-else-if="conversations.length === 0" class="empty-text">没有历史对话</div>
       
       <div v-else 
         v-for="conv in conversations" 
         :key="conv.id" 
         class="conversation-item" 
         :class="{ active: conv.id === currentConversationId && !editingConversationId }" 
         @click="selectConversation(conv.id)">
         
         <div class="conv-main-content">
            <!-- 显示模式 -->
            <span v-if="editingConversationId !== conv.id" class="conv-name" :title="conv.name">
              {{ conv.name }}
            </span>
            <!-- 编辑模式 - 移除 ref="inputRef" -->
            <input 
              v-else 
              type="text" 
              v-model="renameInput" 
              @blur="saveRename(conv.id)" 
              @keydown="handleInputKeydown($event, conv.id)"
              class="rename-input"
            />
            
            <!-- <span class="conv-timestamp">{{ formatTimestamp(conv.timestamp) }}</span> -->
         </div>
         
         <!-- 操作按钮 -->
         <div class="conv-actions" v-if="currentConversationId === conv.id">
             <!-- 编辑模式按钮 -->
             <template v-if="editingConversationId === conv.id">
                 <button class="action-button save-button" @click.stop="saveRename(conv.id)" title="保存" v-html="saveIcon"></button>
                 <button class="action-button cancel-button" @click.stop="cancelEditing" title="取消" v-html="cancelIcon"></button>
             </template>
             <!-- 显示模式按钮 -->
             <template v-else>
                 <button class="action-button edit-button" @click.stop="startEditing(conv)" title="重命名" v-html="editIcon"></button>
                 <button class="action-button delete-button" @click.stop="deleteConversation(conv.id)" title="删除" v-html="deleteIcon"></button>
             </template>
         </div>
       </div>
    </div>
  </div>
</template>

<style scoped>
.history-sidebar-component {
  flex: 1; /* 增加比例从1.5到2 */
  min-width: 200px; /* 从240px增加到260px */
  max-width: 380px; /* 从350px增加到380px */
  background-color: #202123; /* Darker sidebar */
  border-right: 1px solid #444;
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
  margin-right: 10px; /* 添加右边距，实现右移效果 */
}

.sidebar-header {
  display: flex;
  justify-content: center; /* 改为居中对齐 */
  padding: 10px 5px; /* 减小左右内边距 */
  border-bottom: 1px solid #444;
  flex-shrink: 0;
}

.new-chat-button {
  background-color: transparent;
  border: 1.5px solid #555;
  color: #eee;
  padding: 8px 12px; /* 减小按钮内边距 */
  border-radius: 3px;
  cursor: pointer;
  display: flex;
  align-items: center;
  transition: background-color 0.2s ease, border-color 0.2s ease;
  font-size: 0.95rem;
  font-weight: 500;
  width: 95%; /* 让按钮宽度几乎占满侧边栏 */
  justify-content: center; /* 文字和图标在按钮内居中 */
}
.new-chat-button .icon {
  margin-right: 8px;
  display: inline-block;
  vertical-align: middle;
}

.new-chat-button:hover {
  background-color: #333;
  border-color: #777;
}

.conversation-list {
  flex-grow: 1;
  overflow-y: auto;
  padding: 10px 0; /* Remove side padding */
}

.loading-text,
.empty-text {
  text-align: center;
  color: #888;
  padding: 20px;
}

.conversation-item {
  padding: 12px 20px; /* Increased padding */
  cursor: pointer;
  border-bottom: 1px solid #333; /* Subtle separator */
  transition: background-color 0.2s ease;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.conversation-item:last-child {
    border-bottom: none;
}

.conversation-item:hover {
  background-color: #303134;
}

.conversation-item.active {
  background-color: #40414f; /* Active item highlight */
  position: relative; /* For positioning action buttons */
}

.conv-main-content {
    flex-grow: 1;
    overflow: hidden;
    margin-right: 10px; /* Space for actions */
}

.conv-name {
  display: block; /* Ensure it takes full width */
  font-weight: 500;
  color: #ececf1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.rename-input {
    width: calc(100% - 10px); /* Adjust width */
    padding: 4px 6px;
    border: 1px solid #555;
    background-color: #333;
    color: #eee;
    border-radius: 3px;
    outline: none;
}

.conv-actions {
    display: flex;
    align-items: center;
    gap: 5px; /* Space between buttons */
    flex-shrink: 0; /* Prevent shrinking */
}

.action-button {
    background: none;
    border: none;
    color: #aaa;
    cursor: pointer;
    padding: 2px; /* Small padding */
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 3px;
}

.action-button:hover {
    color: #eee;
    background-color: #555;
}

/* Specific button colors on hover if needed */
.edit-button:hover {
    color: #aed581; /* Light green */
}
.delete-button:hover {
    color: #ef9a9a; /* Light red */
}
.save-button:hover {
     color: #aed581; /* Light green */
}
.cancel-button:hover {
    color: #ef9a9a; /* Light red */
}


/* Style for the SVG icons within buttons */
.action-button svg {
    width: 14px; 
    height: 14px;
}

.assistant-name {
  display: flex;
  align-items: center;
}

.assistant-icon {
  margin-right: 5px;
  display: flex;
  align-items: center;
  color: #71717a;
}

.assistant-icon svg {
  width: 16px;
  height: 16px;
}
</style>
