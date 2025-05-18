<script setup>
import { computed } from 'vue';
import { marked } from 'marked'; // 导入 marked 库

const props = defineProps({
  message: {
    type: Object,
    required: true,
    default: () => ({ role: 'assistant', text: '', isLoading: false, isError: false })
  }
});

// 计算属性，将 message.text 从 Markdown 转换为 HTML
const parsedHtml = computed(() => {
  if (props.message.text) {
    // 使用 marked 解析 Markdown。
    // 注意：为了安全，你可能需要配置 marked 或使用 DOMPurify 来清理 HTML
    // 配置 marked 以更好地处理换行符等
    marked.setOptions({
      breaks: true, // 将 GFM 换行符渲染为 <br>
      gfm: true,    // 启用 GitHub Flavored Markdown
    });
    return marked(props.message.text);
  }
  return '';
});

// 计算头像的占位符文本（例如，用户'U'，助手'A'）
const avatarInitial = computed(() => {
  return props.message.role === 'user' ? 'U' : 'A';
});

// 添加助手图标SVG
const assistantIcon = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width="18" height="18"><path d="M12 2a9.96 9.96 0 0 1 7.383 16.619 9.906 9.906 0 0 1-6.912 3.373 10.152 10.152 0 0 1-7.53-2.895A9.96 9.96 0 0 1 2 12c0-2.653 1.035-5.147 2.903-7.023C6.78 3.08 9.299 2 12 2Zm-.5 4a.5.5 0 0 0-.5.5v.5h-1a2 2 0 0 0-2 2v1a2 2 0 0 0 2 2h2v2h-3a.5.5 0 0 0 0 1h3v.5a.5.5 0 0 0 1 0V16h3a.5.5 0 0 0 0-1h-3v-2h2a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-1v-.5a.5.5 0 0 0-.5-.5ZM9 9h1v1H9V9Zm4 0h1v1h-1V9Z"/></svg>`;
</script>

<template>
  <div :class="['message', message.role, { error: message.isError }]">
    <!-- 头像 -->
    <div :class="['avatar', message.role]">
      <span v-if="message.role === 'user'">U</span>
      <span v-else v-html="assistantIcon"></span>
    </div>
    <!-- 气泡 -->
    <div class="bubble">
       <div v-if="message.isLoading" class="loading-dots">
         <span></span><span></span><span></span>
       </div>
       <!-- 使用计算属性渲染解析后的 HTML -->
       <div v-else v-html="parsedHtml" class="content"></div> 
    </div>
  </div>
</template>

<style scoped>
.message {
  display: flex;
  align-items: flex-start; /* Changed from center for better bubble alignment */
  margin-bottom: 15px;
  max-width: 80%;
  flex-shrink: 0;
}

/* 使用 role 进行样式选择 */
.message.user {
  justify-content: flex-end;
  margin-left: auto;
  flex-direction: row-reverse;
}

/* 使用 role 进行样式选择 */
.message.assistant {
  justify-content: flex-start;
  margin-right: auto;
  flex-direction: row;
}

/* 头像样式 */
.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background-color: #4a6cf7; /* Default blue for assistant */
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 1rem;
  flex-shrink: 0;
  margin-top: 2px; /* Slight adjustment for alignment */
}

/* 使用 role 进行样式选择 */
.avatar.user {
  background-color: #10b981;
  margin-left: 10px;
}

/* 使用 role 进行样式选择 */
.avatar.assistant {
  background-color: #6b7280;
  margin-right: 10px;
}

/* 气泡样式 */
.bubble {
  padding: 10px 15px; /* Adjusted padding */
  border-radius: 12px;
  word-wrap: break-word;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  position: relative;
  max-width: calc(100% - 48px); /* Adjusted max-width considering margin */
  overflow-y: auto;  /* 允许滚动 */
}

/* 用户气泡 */
/* 使用 role 进行样式选择 */
.message.user .bubble {
  background-color: #3b82f6;
  color: white;
  border-radius: 12px 12px 4px 12px; /* Top-left, top-right, bottom-right, bottom-left */
}

/* AI/Assistant 气泡 */
/* 使用 role 进行样式选择 */
.message.assistant .bubble {
  background-color: #ffffff;
  color: #333;
  border: 1px solid #e5e7eb;
  border-radius: 12px 12px 12px 4px; /* Top-left, top-right, bottom-right, bottom-left */
}

/* 错误消息气泡 */
.message.error .bubble {
    background-color: #fee2e2;
    color: #b91c1c;
    border: 1px solid #fecaca;
}

/* 加载指示器样式 */
.loading-dots span {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: currentColor;
  margin: 0 2px;
  animation: bounce 1.4s infinite ease-in-out both;
}
.loading-dots span:nth-child(1) { animation-delay: -0.32s; }
.loading-dots span:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1.0); }
}

/* 内部内容容器 */
.content {
  min-width: 1em;
}

.content :deep(*) {
  margin-top: 0; /* Reset default margins inside bubble */
  margin-bottom: 0.5em; /* Add some space between elements */
  padding: 0;
}
.content :deep(*:last-child) {
    margin-bottom: 0; /* Remove margin from the last element */
}


.content :deep(p) {
    line-height: 1.5;
}

.content :deep(ul),
.content :deep(ol) {
  padding-left: 1.5em;
}

.content :deep(pre) {
  background-color: #f3f4f6;
  padding: 10px;
  border-radius: 6px;
  overflow-x: auto;
  margin-top: 0.5em;
}

.content :deep(code) {
  font-family: Consolas, Monaco, 'Andale Mono', 'Ubuntu Mono', monospace;
  font-size: 0.9em;
  background-color: #e5e7eb;
  padding: 2px 4px;
  border-radius: 3px;
  word-break: break-all; /* Break long inline code */
}

.content :deep(pre) > code {
  background-color: transparent;
  padding: 0;
  word-break: normal; /* Don't break words in code blocks */
}

.content :deep(blockquote) {
  border-left: 3px solid #d1d5db;
  padding-left: 10px;
  margin-left: 0;
  color: #6b7280;
}

.content :deep(details) {
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  padding: 8px;
  background-color: #f9fafb;
}
.content :deep(summary) {
  cursor: pointer;
  font-weight: bold;
  color: #4b5563;
}

/* SVG图标样式 */
.avatar svg {
  width: 20px;
  height: 20px;
}
</style>