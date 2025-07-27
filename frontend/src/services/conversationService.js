/**
 * 对话管理服务
 */
import * as api from './api';
/**
 * 创建新对话 (调用后端API)
 * @param {string} model - 模型名称
 * @returns {Promise<Object>} - 新对话对象 {id (日期格式), name, timestamp, model}
 */
export async function createNewConversation(model) {
  try {
    // 调用后端 API 创建对话并获取日期格式 ID
    const response = await api.createNewConversation(model);
    const newConversationId = response.conversation_id;
    
    if (!newConversationId) {
      throw new Error("服务器未能返回有效的对话ID");
    }
    
    // 检查ID格式 (预期是日期格式)
    if (newConversationId.startsWith('new-')) {
      // 如果后端返回了 new- 前缀，说明后端创建文件失败，这是个问题
      console.error(`后端创建新对话失败，返回了备用ID: ${newConversationId}`);
      throw new Error("后端创建对话文件失败");
    }
    
    console.log(`Frontend: 从后端获取到新对话ID: ${newConversationId}`);
    // 返回新对话对象
    return {
      id: newConversationId,
      name: "聊天助手", // 修改初始名称
      timestamp: Date.now(),
      model: model
    };
  } catch (error) {
    console.error("调用后端创建新对话失败:", error);
    alert(`创建新对话失败: ${error.message || '未知错误'}`);
    // 这里不应再生成临时ID，让错误传递上去
    throw error; 
  }
}

/**
 * 加载对话列表
 * @param {string} model - 模型名称
 * @returns {Promise<Array>} - 对话列表
 */
export async function loadConversations(model) {
  try {
    return await api.fetchConversations(model);
  } catch (error) {
    console.error(`加载${model}对话列表失败:`, error);
    return [];
  }
}

/**
 * 加载对话历史消息
 * @param {string} conversationId - 对话ID
 * @param {string} model - 模型名称
 * @returns {Promise<Array>} - 消息列表
 */
export async function loadMessages(conversationId, model) {

  if (!conversationId) {
      return [];
  }
  
  try {
    return await api.fetchMessages(conversationId, model);
  } catch (error) {
    console.error(`加载对话${conversationId}的消息失败:`, error);
    return [];
  }
}

/**
 * 删除对话
 * @param {string} conversationId - 对话ID
 * @param {string} model - 模型名称
 * @returns {Promise<boolean>} - 是否删除成功
 */
export async function removeConversation(conversationId, model) {
  try {
    await api.deleteConversation(conversationId, model);
    return true;
  } catch (error) {
    console.error(`删除对话${conversationId}失败:`, error);
    throw error;
  }
} 