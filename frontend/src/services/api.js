/**
 * API 服务 - 提供与后端通信的方法
 */

// 根据当前主机动态确定后端URL
export const BACKEND_URL = location.hostname === 'localhost' 
  ? 'http://localhost:5004' 
  : `http://${location.hostname}:5004`;

/**
 * 统一处理 API 响应
 * @param {Response} response - Fetch API 的响应对象
 * @returns {Promise<any>} 解析后的 JSON 数据
 * @throws {Error} 如果响应不成功，则抛出包含错误信息的 Error 对象
 */
async function handleResponse(response) {
  if (!response.ok) {
    let errorData = {};
    try {
      errorData = await response.json();
    } catch (e) {
      // 如果无法解析 JSON，使用状态文本
    }
    const errorMessage = errorData.error || errorData.message || `HTTP错误! 状态: ${response.status} ${response.statusText}`;
    throw new Error(errorMessage);
  }
  // 对于 204 No Content 等情况，直接返回成功状态
  if (response.status === 204) {
    return { success: true };
  }
  // 尝试解析 JSON，如果失败则认为成功（例如对于非 JSON 响应）
  try {
    return await response.json();
  } catch (e) {
     console.warn("API响应不是有效的JSON，但请求成功。", response.url);
     return { success: true };
  }
}



/**
 * 获取指定模型的对话列表
 * @param {string} model - 模型名称
 * @returns {Promise<Array>} 对话摘要列表
 */
export async function fetchConversations(model) {
  try {
    const response = await fetch(`${BACKEND_URL}/chat/conversations?model=${model}`);
    return await handleResponse(response);
  } catch (error) {
    console.error(`获取 ${model} 对话列表错误:`, error);
    throw error;
  }
}

/**
 * 获取指定对话的历史消息
 * @param {string} conversationId - 对话ID (本地日期格式)
 * @param {string} model - 模型名称
 * @returns {Promise<Array>} 消息列表
 */
export async function fetchMessages(conversationId, model) {
  // 对于临时前端ID，不向后端请求
  if (!conversationId || conversationId.startsWith('temp-')) {
    return [];
  }
  
  try {
    const response = await fetch(`${BACKEND_URL}/chat/conversations/${conversationId}/messages?model=${model}`);
    return await handleResponse(response);
  } catch (error) {
    console.error(`获取对话 ${conversationId} 历史消息错误:`, error);
    throw error;
  }
}

/**
 * 创建新对话
 * @param {string} model - 模型名称
 * @returns {Promise<Object>} 新对话信息 (包含ID, name, timestamp)
 */
export async function createNewConversation(model) {
  try {
    const response = await fetch(`${BACKEND_URL}/chat/conversations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model }),
    });
    return await handleResponse(response);
  } catch (error) {
    console.error("创建新对话错误:", error);
    throw error;
  }
}

/**
 * 发送聊天消息 (包括文本和文件ID)
 * @param {Object} params - 请求参数
 * @param {string} params.query - 查询文本
 * @param {string} params.conversationId - 对话ID (本地日期格式或null)
 * @param {string} params.model - 模型名称
 * @param {string} [params.user='vue-app-user'] - 用户标识
 * @param {Object} [params.inputs={}] - Dify 输入参数
 * @param {Array<string>} [params.files=[]] - 文件ID列表
 * @param {boolean} [params.stream=true] - 是否请求流式响应
 * @param {AbortSignal} [params.signal] - 用于中止请求的 AbortSignal
 * @returns {Promise<ReadableStream>} Dify 返回的响应流
 */
export async function sendChatMessage(params) {
  const { 
    query, 
    conversationId, 
    model, 
    user = 'vue-app-user', 
    inputs = {}, 
    files = [],
    stream = true,
    signal
  } = params;
  
  // 保持conversationId不变，让后端处理会话管理
  const effectiveConversationId = conversationId;
  
  try {
    // 构造完整的文件引用对象
    let formattedFileIds = [];
    
    // 如果有文件，为每个文件构造正确的引用对象
    if (files && files.length > 0) {
      formattedFileIds = files.map(fileId => {
        // 如果已经是对象格式，直接使用
        if (typeof fileId === 'object' && fileId.upload_file_id) {
          return fileId;
        }
        
        // 否则构造标准格式对象
        return {
          type: "document", // 文档类型
          transfer_method: "local_file",
          upload_file_id: fileId
        };
      });
    }
    
    // 构造请求体 - 确保符合Dify API要求
    const requestBody = {
      query: query, // 查询文本
      conversation_id: effectiveConversationId,
      model,
      user,
      inputs: {}, // 空对象
      response_mode: stream ? 'streaming' : 'blocking',
    };
    
    // 只有当有文件时才添加files字段，避免发送空数组
    if (formattedFileIds.length > 0) {
      requestBody.files = formattedFileIds;
    }
    
    console.log('API: 发送聊天请求体:', JSON.stringify(requestBody));
    
    const response = await fetch(`${BACKEND_URL}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestBody),
      signal
    });

    // 流式响应不使用 handleResponse 处理
    if (!response.ok || !response.body) {
      let errorData = {};
      try {
        errorData = await response.json();
        console.error('聊天请求错误详情:', errorData);
      } catch (e) {}
      const errorMessage = errorData.error || errorData.message || `HTTP错误! 状态: ${response.status}`;
      throw new Error(errorMessage);
    }
    
    return response.body;
  } catch (error) {
    console.error('发送消息错误:', error);
    throw error;
  }
}

/**
 * 保存消息到后端本地历史记录
 * @param {string} model - 模型名称 
 * @param {string} conversationId - 对话ID (本地日期格式)
 * @param {Object} messageData - 消息数据 { id, role, text, timestamp, fileIds? }
 * @returns {Promise<Object>} 后端响应
 */
export async function saveMessageToHistory(model, conversationId, messageData) {
  if (!conversationId || !messageData || !messageData.role || !messageData.text) {
    console.error(`API: 保存消息失败 - 缺少必要参数`, { model, conversationId, messageData });
    return Promise.reject(new Error('缺少必要的消息数据 (role, text)'));
  }

  // 准备要保存的消息数据，确保字段完整
  const messageToSave = { 
    id: messageData.id || `${messageData.role}-${Date.now()}`,
    role: messageData.role,
    text: messageData.text,
    sender: messageData.sender || messageData.role, // 兼容旧格式
    timestamp: messageData.timestamp || new Date().toISOString(),
    fileIds: messageData.fileIds || undefined // 添加文件ID
  };
  
  try {
    const response = await fetch(`${BACKEND_URL}/chat/conversations/${conversationId}/messages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        model, 
        message: messageToSave 
      }),
    });
    return await handleResponse(response);
  } catch (error) {
    console.error(`API: 保存消息到历史记录错误:`, error);
    throw error;
  }
}

/**
 * 删除对话
 * @param {string} conversationId - 对话ID (本地日期格式)
 * @param {string} model - 模型名称
 * @returns {Promise<Object>} 后端响应
 */
export async function deleteConversation(conversationId, model) {
  try {
    const response = await fetch(`${BACKEND_URL}/chat/conversations/${conversationId}?model=${model}`, {
      method: 'DELETE',
    });
    // 删除成功通常返回 204 No Content 或 200 OK
    return await handleResponse(response);
  } catch (error) {
    console.error(`删除对话 ${conversationId} 错误:`, error);
    throw error;
  }
}

/**
 * 重命名对话
 * @param {string} conversationId - 对话ID (本地日期格式)
 * @param {string} newName - 新名称
 * @param {string} model - 模型名称
 * @returns {Promise<Object>} 后端响应
 */
export async function renameConversation(conversationId, newName, model) {
  try {
    const response = await fetch(`${BACKEND_URL}/chat/conversations/${conversationId}/name?model=${model}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: newName }),
    });
    return await handleResponse(response);
  } catch (error) {
    console.error(`重命名对话 ${conversationId} 失败:`, error);
    throw error;
  }
}

/**
 * 上传文件到指定对话
 * @param {File} file - 要上传的文件对象
 * @param {string} conversationId - 对话ID (本地日期格式)
 * @param {string} model - 模型名称
 * @param {string} user - 用户标识
 * @returns {Promise<Object>} 上传结果，包含 Dify 返回的文件信息 (如 file_id)
 */
export async function uploadFile(file, conversationId, model, user = 'vue-app-user') {
  try {
    // 1. 确保文件名有扩展名 - 采用与Python脚本相同的方法处理文件
    const fileName = file.name;
    
    // 文件上传时不需要处理文件类型，简单地传递文件即可
    // 在请求中统一使用 "text/plain" 作为MIME类型，与Python脚本保持一致
    console.log(`API: 上传文件 ${fileName}`);
    
    // 构建最简单的FormData，与Python脚本保持一致
    const formData = new FormData();
    // 使用原始文件，不修改其内容或类型
    formData.append('file', file);
    formData.append('user', user);
    formData.append('model', model);
    formData.append('conversation_id', conversationId);
    
    // 发送请求，保持与后端相同的简单格式
    const response = await fetch(`${BACKEND_URL}/chat/upload`, {
      method: 'POST',
      body: formData, // FormData会自动设置正确的Content-Type
    });
    
    // 错误处理保持简单明了
    if (!response.ok) {
      let errorData = {};
      try {
        errorData = await response.json();
      } catch(e){}
      
      const errorMessage = errorData.error || `上传失败! HTTP状态: ${response.status}`;
      throw new Error(errorMessage);
    }

    return await response.json(); // 返回后端处理后的成功结果
  } catch (error) {
    console.error('文件上传失败:', error);
    throw error;
  }
}

/**
 * 调用后端分析二进制文件API
 * @param {string} filename - 二进制文件名
 * @returns {Promise<Object>} 分析结果
 */
export async function analyzeBinary(filename) {
  try {
    const response = await fetch(`${BACKEND_URL}/chat/analyze/binary`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filename })
    });
    if (!response.ok) {
      let errorData = {};
      try { errorData = await response.json(); } catch(e){}
      const errorMessage = errorData.error || `分析失败! HTTP状态: ${response.status}`;
      throw new Error(errorMessage);
    }
    return await response.json();
  } catch (error) {
    console.error('二进制分析API调用失败:', error);
    throw error;
  }
}