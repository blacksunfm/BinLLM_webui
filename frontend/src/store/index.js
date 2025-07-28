/**
 * 应用状态管理 (Vuex-like)
 */
import { reactive, computed, readonly } from 'vue';
import * as api from '../services/api.js';

// 生成模型 ID 列表 (dify1 到 dify10)
const model_ids = Array.from({ length: 11 }, (_, i) => `dify${i + 1}`);

// 用于存储当前消息发送的 AbortController
let currentAbortController = null;

// ---- Reactive State ----
const state = reactive({
  models: model_ids.map(id => ({ id: id, name: `Dify ${id.substring(4)}` })),
  selectedModel: model_ids[0],

  // 对话列表 (按模型区分)
  modelConversations: model_ids.reduce((acc, id) => {
    acc[id] = [];
    return acc;
  }, {}),
  currentConversationId: null, // 当前选中的对话ID (本地日期格式)

  // 消息存储 (按对话ID索引)
  messagesMap: {},

  // 加载状态
  isLoadingConversations: false, // 是否正在加载对话列表
  isLoadingHistory: false,       // 是否正在加载当前对话的消息

  // 发送状态 (按对话ID索引)
  sendingMessages: {}, // 格式: { [conversationId]: boolean }
});

// ---- Computed Properties ----
// 当前选中模型的对话列表
const conversations = computed(() => {
  return state.modelConversations[state.selectedModel] || [];
});

// 当前对话的消息列表
const currentMessages = computed(() => {
  return state.messagesMap[state.currentConversationId] || [];
});

// 当前对话是否正在发送消息
const isCurrentConversationSending = computed(() => {
  return !!state.sendingMessages[state.currentConversationId];
});

// ---- Actions ----
const actions = {
  /**
   * 切换当前选中的模型。
   * @param {string} modelId - 要切换到的模型ID。
   */
  async selectModel(modelId) {
    if (state.selectedModel !== modelId) {
      state.selectedModel = modelId;
      state.currentConversationId = null; // 清除当前对话 ID
      await this.fetchConversations(); // 获取新模型的对话列表
      // 自动选择第一个对话，或创建新对话
      if (conversations.value.length > 0) {
         await this.selectConversation(conversations.value[0].id);
      } else {
          await this.createNewChat();
      }
    }
  },

  /**
   * 获取当前选中模型的对话列表。
   */
  async fetchConversations() {
    state.isLoadingConversations = true;
    try {
      const fetchedConversations = await api.fetchConversations(state.selectedModel);
      // 按时间戳降序排序
      fetchedConversations.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
      state.modelConversations[state.selectedModel] = fetchedConversations;
    } catch (error) {
      console.error(`获取对话列表失败 (${state.selectedModel}):`, error);
      state.modelConversations[state.selectedModel] = []; // 出错时清空
    } finally {
      state.isLoadingConversations = false;
    }
  },

  /**
   * 为当前模型创建新的对话。
   */
  async createNewChat() {
    try {
      const newConversation = await api.createNewConversation(state.selectedModel);
      // 将新对话添加到列表顶部
      state.modelConversations[state.selectedModel].unshift(newConversation);
      await this.selectConversation(newConversation.id); // 创建后立即选中
    } catch (error) {
      console.error("创建新对话失败:", error);
      alert("创建新对话失败: " + error.message);
    }
  },

  /**
   * 选中指定的对话，并加载其历史消息。
   * @param {string} conversationId - 要选中的对话ID (本地日期格式)。
   */
  async selectConversation(conversationId) {
    if (state.currentConversationId === conversationId) return;

    state.currentConversationId = conversationId;
    // 如果没有消息缓存，则显示加载状态并加载消息
    if (!state.messagesMap[conversationId] || state.messagesMap[conversationId].length === 0) {
        state.isLoadingHistory = true;
        try {
            const history = await api.fetchMessages(conversationId, state.selectedModel);
            state.messagesMap[conversationId] = history;
        } catch (error) {
            console.error("加载对话历史失败:", error);
            alert("加载对话历史失败: " + error.message);
            state.messagesMap[conversationId] = []; // 出错时设为空数组
        } finally {
            state.isLoadingHistory = false;
        }
    } else {
        state.isLoadingHistory = false; // 有缓存，无需加载
    }
  },

  /**
   * 发送消息 (文本和/或文件) 到当前对话。
   * @param {string} queryText - 用户输入的文本。
   * @param {Array<string>} [fileIds=[]] - 关联的文件ID列表。
   */
  async sendMessage(queryText, fileIds = []) {
    const conversationId = state.currentConversationId;
    const modelId = state.selectedModel;
    const chatService = await import('../services/chatService.js');

    if (!conversationId) {
      alert("请先选择或创建一个对话。");
      return;
    }

    // 1. 决定实际发送给后端的查询内容 (queryToSend)
    let queryToSend = queryText.trim();
    if (fileIds.length > 0 && !queryToSend) {
      // 只有文件时，使用明确的默认查询
      queryToSend = "请基于我上传的文件进行分析或回答。"; // <--- 更明确的指令
    } else if (fileIds.length === 0 && !queryToSend) {
      // 既无文本也无文件
      return;
    }
    // 如果 queryText 和 fileIds 都存在，queryToSend 就是 queryText

    if (state.sendingMessages[conversationId]) {
      console.warn("消息正在发送中，请稍候...");
      return;
    }

    // AbortController logic remains the same...
    if (currentAbortController) {
        currentAbortController.abort();
    }
    currentAbortController = new AbortController();
    const signal = currentAbortController.signal;

    // --- 2. 更新前端UI状态 (显示用户消息和AI占位符) ---
    state.sendingMessages[conversationId] = true;
    if (!state.messagesMap[conversationId]) {
      state.messagesMap[conversationId] = [];
    }

    // 准备用于在聊天记录中显示的用户消息文本 (userMessageText)
    let userMessageText = queryText.trim(); // 优先使用用户输入的文本
     if (fileIds.length > 0) {
       const fileText = ` [包含${fileIds.length}个文件]`;
       // 如果用户没输文本，给个简单的显示提示
       userMessageText = userMessageText ? userMessageText + fileText : `已上传 ${fileIds.length} 个文件`;
     }

    const userMessage = {
      id: `temp-user-${Date.now()}`,
      role: 'user',
      text: userMessageText, // 这个文本用于显示
      timestamp: new Date().toISOString(),
      fileIds: fileIds.length > 0 ? fileIds : undefined
    };
    state.messagesMap[conversationId].push(userMessage);

    // AI 消息占位符 (logic remains the same)
    const aiMessageId = `temp-ai-${Date.now()}`;
    const aiMessagePlaceholder = {
      id: aiMessageId,
      role: 'assistant',
      text: '',
      isLoading: true,
      isError: false,
      timestamp: new Date().toISOString()
    };
    state.messagesMap[conversationId].push(aiMessagePlaceholder);
    const aiMessageIndex = state.messagesMap[conversationId].length - 1;

    // --- 3. 调用 chatService 发送消息 (使用 queryToSend) --- 
    try {
      console.log(`Store: 发送消息，文本: "${queryToSend}", 文件IDs: ${JSON.stringify(fileIds)}`);
      
      await chatService.sendMessage({
        model: modelId,
        conversationId: conversationId,
        query: queryToSend, // ** 使用决定好的查询内容 **
        file_ids: fileIds, // 传递文件ID列表
        stream: true,
        signal: signal,
        onChunk: (chunk) => {
          if (state.messagesMap[conversationId]?.[aiMessageIndex] && !state.messagesMap[conversationId][aiMessageIndex].isError) {
            state.messagesMap[conversationId][aiMessageIndex].text += chunk;
            state.messagesMap[conversationId][aiMessageIndex].isLoading = false;
          }
        },
        onComplete: (result) => {
          if (state.messagesMap[conversationId]?.[aiMessageIndex]) {
            state.messagesMap[conversationId][aiMessageIndex].isLoading = false;
            
            // 如果结果中包含错误标志，则设置错误状态
            if (result && result.isError) {
              console.log("Store: 处理错误结果:", result);
              state.messagesMap[conversationId][aiMessageIndex].isError = true;
              state.messagesMap[conversationId][aiMessageIndex].text = result.text || "服务器返回错误";
            } 
            // 如果最终文本为空且没有错误，显示提示
            else if (!state.messagesMap[conversationId][aiMessageIndex].text && 
                    !state.messagesMap[conversationId][aiMessageIndex].isError) {
              state.messagesMap[conversationId][aiMessageIndex].text = '[未收到有效回复]';
            }
          }
          // 更新对话列表的时间戳，将当前对话移到顶部
          const convIndex = state.modelConversations[modelId].findIndex(c => c.id === conversationId);
          if (convIndex !== -1) {
            state.modelConversations[modelId][convIndex].timestamp = new Date().toISOString();
            const updatedConv = state.modelConversations[modelId].splice(convIndex, 1)[0];
            state.modelConversations[modelId].unshift(updatedConv);
          }
        },
        onError: (error) => {
          console.error("消息流处理错误:", error);
          if (state.messagesMap[conversationId]?.[aiMessageIndex]) {
            state.messagesMap[conversationId][aiMessageIndex].isError = true;
            
            // 使用友好的错误信息代替原始错误消息
            let errorMsg = error.message || '未知错误';
            // 已知的LLM文件处理错误
            if (errorMsg.includes('Unsupported Extension') || 
                errorMsg.includes('不支持的文件类型') ||
                errorMsg.includes('Run failed')) {
              errorMsg = '文件格式有问题，请尝试其他格式的文件，如TXT或PDF。';
            }
            
            state.messagesMap[conversationId][aiMessageIndex].text = `错误: ${errorMsg}`;
            state.messagesMap[conversationId][aiMessageIndex].isLoading = false;
          }
        }
      });

      // --- 4. (异步) 保存消息到后端历史记录 --- 
      const saveHistory = async () => {
          try {
              // 保存用户消息 (使用显示的文本 userMessageText)
              await api.saveMessageToHistory(modelId, conversationId, userMessage);
              // 保存 AI 回复消息 (logic remains same)
              const aiMessage = state.messagesMap[conversationId]?.[aiMessageIndex];
              if (aiMessage && !aiMessage.isLoading && aiMessage.text && !aiMessage.isError) {
                  await api.saveMessageToHistory(modelId, conversationId, {
                      id: aiMessage.id,
                      text: aiMessage.text,
                      sender: 'assistant',
                      role: 'assistant',
                      timestamp: aiMessage.timestamp
                  });
              }
          } catch (saveError) {
              console.error(`保存历史记录失败 (对话: ${conversationId}):`, saveError);
              // 保存失败通常不直接通知用户，只记录日志
          }
      };
      saveHistory();

    } catch (error) {
      // chatService.sendMessage 抛出的错误 (例如网络问题或 Dify API 严重错误)
      console.error("发送消息失败:", error);
      if (state.messagesMap[conversationId]?.[aiMessageIndex]) {
        state.messagesMap[conversationId][aiMessageIndex].text = `发送失败: ${error.message || '未知错误'}`;
        state.messagesMap[conversationId][aiMessageIndex].isLoading = false;
        state.messagesMap[conversationId][aiMessageIndex].isError = true;
      }
      // 仅当用户仍在查看该对话时弹窗提示
      if (state.currentConversationId === conversationId) {
        alert("发送消息失败: " + error.message);
      }
    } finally {
      // --- 5. 清理状态 ---
      state.sendingMessages[conversationId] = false;
      if (currentAbortController?.signal === signal) {
        currentAbortController = null;
      }
    }
  },

  /**
   * 请求停止当前正在进行的 AI 响应生成。
   */
  stopGeneratingResponse() {
    if (currentAbortController) {
      console.log("Store: 请求停止生成响应...");
      currentAbortController.abort();
      // AbortController 设为 null 的操作由 sendMessage 的 finally 块处理
    } else {
      console.warn("Store: 请求停止生成响应，但当前没有正在进行的请求。");
    }
  },

  /**
   * 重命名对话。
   * @param {string} conversationId - 要重命名的对话ID (本地日期格式)。
   * @param {string} newName - 新的对话名称。
   * @returns {Promise<boolean>} 是否成功。
   */
  async renameConversation(conversationId, newName) {
      const modelId = state.selectedModel;
      const convIndex = state.modelConversations[modelId].findIndex(c => c.id === conversationId);
      if (convIndex === -1) return false;

      const originalName = state.modelConversations[modelId][convIndex].name;

      state.modelConversations[modelId][convIndex].name = newName;

      try {
          await api.renameConversation(conversationId, newName, modelId);
          return true;
      } catch (error) {
          console.error("重命名对话失败:", error);
          // 回滚 UI 更新
          state.modelConversations[modelId][convIndex].name = originalName;
          alert(`重命名失败: ${error.message || '请稍后重试'}`);
          return false;
      }
  },

  /**
   * 删除对话。
   * @param {string} conversationId - 要删除的对话ID (本地日期格式)。
   */
  async deleteConversation(conversationId) {
      const modelId = state.selectedModel;
      const originalConversations = [...state.modelConversations[modelId]];
      const originalCurrentId = state.currentConversationId;

      // 乐观 UI 更新
      state.modelConversations[modelId] = state.modelConversations[modelId].filter(c => c.id !== conversationId);
      delete state.messagesMap[conversationId]; // 同时清除消息缓存

      // 如果删除的是当前对话，则选择其他对话或创建新对话
      if (state.currentConversationId === conversationId) {
          state.currentConversationId = null;
          if (state.modelConversations[modelId].length > 0) {
              await this.selectConversation(state.modelConversations[modelId][0].id);
          } else {
              await this.createNewChat();
          }
      }

      try {
          await api.deleteConversation(conversationId, modelId);
      } catch (error) {
          console.error("删除对话失败:", error);
          // 回滚 UI 更新
          state.modelConversations[modelId] = originalConversations;
          // 如果删除了当前对话又失败了，需要恢复
          if (originalCurrentId === conversationId) {
              state.currentConversationId = originalCurrentId;
              // 可能需要重新加载消息，但 selectConversation 会处理
              await this.selectConversation(originalCurrentId); 
          }
          // 将错误抛出给调用者 (App.vue) 处理
          throw error;
      }
  }
};

// ---- Export Store ----
export default {
  state: readonly(state), // 导出只读状态
  // 导出计算属性
  conversations,
  currentMessages,
  isCurrentConversationSending,
  // 导出 Actions
  ...actions
}; 