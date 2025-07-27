/**
 * 聊天服务 - 封装与 Dify API 的消息发送和流式响应处理
 */
import * as api from './api.js';

/**
 * 发送消息并处理流式响应。
 * 此函数负责调用后端 API，解析 SSE 流，并通过回调函数实时反馈数据。
 *
 * @param {Object} params - 参数对象
 * @param {string} params.model - 模型ID
 * @param {string} params.conversationId - 对话ID (本地日期格式 或 null)
 * @param {string} params.query - 用户查询文本
 * @param {Array<string>} [params.file_ids=[]] - 关联的文件ID列表
 * @param {boolean} [params.stream=true] - 是否使用流式响应
 * @param {Function} [params.onChunk] - (chunk: string) => void - 接收每个文本块的回调
 * @param {Function} [params.onComplete] - (result: {text: string, conversationId: string}) => void - 流处理完成后的回调
 * @param {Function} [params.onError] - (error: Error) => void - 发生错误时的回调
 * @param {AbortSignal} [params.signal] - 用于中止流式响应的信号
 * @returns {Promise<Object>} 包含最终完整响应文本和对话ID的对象。注意：主要交互通过回调进行。
 */
export async function sendMessage({
  model,
  conversationId,
  query,
  file_ids = [],
  stream = true,
  onChunk = () => {},
  onComplete = () => {},
  onError = () => {},
  signal
}) {
  let streamReader = null;
  let fullResponseText = '';
  let finalConversationId = null; // 用于接收 Dify 可能返回的新对话 ID

  try {
    // 1. 调用 API 获取响应流，传递 signal
    console.log(`[ChatService] 发送消息 - 查询: "${query}", 文件IDs: ${JSON.stringify(file_ids)}`);
    
    // 手动构建符合Python示例格式的文件引用对象
    const formattedFiles = file_ids.map(fileId => {
      // 精确匹配Python脚本中的格式
      return {
        "type": "document",
        "transfer_method": "local_file", 
        "upload_file_id": fileId
      };
    });
    
    console.log(`[ChatService] 格式化后的文件引用: ${JSON.stringify(formattedFiles)}`);
    
    // 构建请求体，完全匹配Python脚本格式
    const requestData = {
      model,
      conversationId, // 可能是本地日期ID或null
      query,
      user: 'vue-app-user',
      inputs: {},
      response_mode: 'streaming'
    };
    
    // 只有在有文件时才添加files字段
    if (formattedFiles.length > 0) {
      requestData.files = formattedFiles;
    }
    
    const responseStream = await api.sendChatMessage({
      ...requestData,
      stream: true,
      signal
    });

    // 2. 处理流式响应
    streamReader = responseStream.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';
    
    console.log('[ChatService] 开始处理流...'); // 添加日志

    while (true) {
      // 在读取前检查是否已中止
      if (signal?.aborted) {
          console.log('[ChatService] 流被中止。');
          // 注意：即使中止，也需要调用 onComplete 和 return
          // 以便 store 能正确结束处理并保存已接收内容
          break;
      }
      
      const { done, value } = await streamReader.read();
      if (done) {
         console.log('[ChatService] 流处理完成。'); // 添加日志
         break;
      }

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n\n');
      buffer = lines.pop(); // 保留可能不完整的最后一行

      for (const line of lines) {
        if (line.startsWith('data:')) {
          const dataStr = line.substring(5).trim();
          if (!dataStr) continue;

          try {
            const data = JSON.parse(dataStr);
            console.log('[ChatService] 收到数据块:', data); // 打印收到的每个事件

            // 处理不同类型的事件
            if (data.event === 'agent_message' || data.event === 'message') {
              const chunk = data.answer || data.text || '';
              if (chunk) {
                console.log('[ChatService] 文本块:', chunk); // 添加日志
                fullResponseText += chunk;
                onChunk(chunk); // 通过回调发送文本块
              }
            } else if (data.event === 'message_end') {
              finalConversationId = data.conversation_id; // 记录 Dify 返回的对话 ID
              console.log(`[ChatService] 收到 message_end, Dify ID: ${finalConversationId}`); // 添加日志
            } else if (data.event === 'agent_thought') {
              console.log('[ChatService] 收到 agent_thought (通常忽略)'); // 添加日志
            } else if (data.event === 'error') {
              console.error("[ChatService] 流错误事件:", data);
              // 将完整错误消息传递给错误处理函数
              let errorMsg = data.message || data.error || '流处理错误';
              
              // 改进特定错误消息的可读性
              if (errorMsg.includes('Unsupported Extension Type:')) {
                errorMsg = '不支持的文件类型。请确保文件有有效的扩展名（如.txt、.pdf等）。';
              } else if (errorMsg.includes('file not accessible')) {
                errorMsg = '文件无法访问。可能文件已被删除或权限不足。';
              } else if (errorMsg.includes('type does not match')) {
                errorMsg = '文件类型与指定类型不匹配。请尝试使用不同格式的文件，如TXT或PDF。';
              }
              
              fullResponseText = `错误: ${errorMsg}`; // 记录错误信息作为响应文本
              onError(new Error(errorMsg));
              // 提前返回结果而不是抛出异常，这样UI可以显示错误消息
              const result = {
                text: fullResponseText,
                conversationId: finalConversationId || conversationId,
                isError: true
              };
              onComplete(result);
              return result;
            } else {
               console.warn('[ChatService] 未知事件类型:', data.event, data); // 添加日志
            }
          } catch (e) {
            console.error("[ChatService] 无法解析流数据块:", dataStr, e);
            onError(new Error(`无法解析响应数据: ${e.message}`));
          }
        }
      }
    }

    // 3. 流处理完成 (或被中止)
    const result = {
      text: fullResponseText,
      // 如果 Dify 返回了 ID，则使用 Dify ID，否则回退到请求时使用的本地 ID
      conversationId: finalConversationId || conversationId
    };
    console.log('[ChatService] 最终结果:', result); // 添加日志

    onComplete(result); // 总是调用 onComplete
    return result;

  } catch (error) {
    // 捕获 fetch 中止错误 (AbortError)
    if (error.name === 'AbortError') {
      console.log('[ChatService] Fetch 请求被中止。');
      // AbortError 是一种预期的停止方式，不应视为失败
      // 确保 onComplete 被调用（已在上面完成），并返回当前结果
      return {
        text: fullResponseText,
        conversationId: finalConversationId || conversationId
      };
    }
    
    // 处理已知错误类型，提供更友好的错误消息
    let errorMsg = error.message || "未知错误";
    if (errorMsg.includes('Unsupported Extension Type:') || 
        error.message.includes('Run failed:') ||
        error.message.includes('没有扩展名')) {
      errorMsg = '不支持的文件类型。请确保文件有有效的扩展名（如.txt、.pdf等）。';
    } else if (error.message.includes('file not accessible') || 
               error.message.includes('无法访问文件')) {
      errorMsg = '文件无法访问。可能文件已被删除或权限不足。';
    }
    
    console.error("[ChatService] 发送消息或处理流失败:", error, "友好错误消息:", errorMsg);
    
    // 用更友好的错误消息创建新错误
    const friendlyError = new Error(errorMsg);
    friendlyError.originalError = error;
    
    onError(friendlyError); // 通过回调通知错误
    throw friendlyError; // 重新抛出错误，让调用者 (store) 可以捕获
  } finally {
    // 4. 确保流读取器被关闭
    if (streamReader) {
      try {
        await streamReader.cancel();
      } catch (e) {
        // 忽略取消错误，可能表示流已经关闭
        // console.warn("ChatService: 取消流读取器时出错:", e);
      }
    }
  }
} 