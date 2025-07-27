import requests
import json
from flask import Response
import os

def get_dify_conversation_id(conversation_id, model):
    """
    从本地历史记录文件中获取 Dify 对话 ID。

    Args:
        conversation_id: 本地对话 ID (日期格式)。
        model: 模型名称。

    Returns:
        str or None: Dify 对话 ID，如果未找到或发生错误则返回 None。
    """
    if not conversation_id:
        print("Dify Service: 未提供本地对话ID，将创建新对话")
        return None

    try:
        history_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'history')
        model_dir = os.path.join(history_dir, model)
        print(f"Dify Service: 查找对话ID {conversation_id} 的Dify ID，模型: {model}")

        # 基础安全检查，防止路径遍历
        if '..' in conversation_id or '/' in conversation_id or '\\' in conversation_id:
            print(f"警告：无效的本地对话ID格式 '{conversation_id}'")
            return None

        filepath = os.path.join(model_dir, f"{conversation_id}.json")
        print(f"Dify Service: 尝试读取历史文件: {filepath}")

        if not os.path.exists(filepath):
            print(f"Dify Service: 历史文件不存在: {filepath}，将创建新对话")
            return None # 文件不存在，表示没有对应的 Dify ID

        with open(filepath, 'r', encoding='utf-8') as f:
            history = json.load(f)
            print(f"Dify Service: 成功读取历史文件，包含 {len(history)} 条记录")

        # Dify ID 存储在历史记录的第一个元素（元数据）中
        if history and isinstance(history[0], dict):
            dify_id = history[0].get('dify_conversation_id')
            print(f"Dify Service: 从历史记录中获取到 Dify ID: {dify_id}")
            return dify_id
        else:
            print(f"Dify Service: 历史记录结构异常，无法找到元数据")
            return None
    except FileNotFoundError:
        print(f"Dify Service: 找不到历史文件: {filepath}")
        return None # 明确处理文件找不到的情况
    except json.JSONDecodeError as json_err:
        print(f"Dify Service: 历史文件JSON解析错误: {json_err}")
        return None
    except Exception as e:
        print(f"错误：获取 Dify 对话 ID 时失败 (对话: {conversation_id}, 模型: {model}): {e}")
        return None

def stream_dify_chat(api_url, api_key, payload):
    """处理流式接口调用，向Dify发送请求并流式返回结果"""
    
    # 确保URL格式正确
    base_url = api_url.rstrip('/')
    dify_chat_url = f"{base_url}/chat-messages"
    
    # 获取必要参数
    local_conversation_id = payload.get('conversation_id', '')
    model = payload.get('model', '')
    
    # 标准化payload
    # 如果已有Dify对话ID，使用它；否则使用空字符串让Dify创建新对话
    dify_conversation_id = ''
    
    # 如果提供了本地对话ID且不是临时ID，查询对应的Dify ID
    if local_conversation_id and not local_conversation_id.startswith('temp-'):
        print(f"Dify Service: 处理本地对话ID: {local_conversation_id}, 模型: {model}")
        try:
            dify_conversation_id = get_dify_conversation_id(local_conversation_id, model)
            if dify_conversation_id:
                print(f"Dify Service: 查询对应的Dify对话ID: {dify_conversation_id}")
                print(f"Dify Service: 使用已存在的Dify对话ID: {dify_conversation_id}")
            else:
                print(f"Dify Service: 未找到对应的Dify对话ID，将创建新对话")
        except Exception as e:
            print(f"Dify Service: 查询Dify对话ID时出错: {e}")
            # 错误时使用空ID，让Dify创建新对话
            dify_conversation_id = ''
    
    # 构建发送到Dify的payload
    # "inputs": {"task": payload.get('model', 'dify1')},
    dify_payload = {
        "inputs": payload.get('inputs', {}),
        "query": payload.get('query', ''),
        "user": payload.get('user', 'vue-app-user'),
        "response_mode": payload.get('response_mode', 'streaming'),
    }
    
    # 只有存在有效对话ID时才添加
    if dify_conversation_id:
        dify_payload["conversation_id"] = dify_conversation_id
    
    # 文件处理 - 直接使用payload中的files字段，确保格式与Python脚本完全一致
    files = payload.get('files', [])
    if files:
        print(f"Dify Service: 收到文件ID列表: {files}")
        # 直接将文件引用数组添加到payload
        dify_payload["files"] = files
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    try:
        # 打印最终发送的 payload (去除敏感信息)
        log_payload = {k: v for k, v in dify_payload.items() if k != 'api_key'}
        print(f"Dify Service: 发送最终 Payload 到 {dify_chat_url}: {json.dumps(log_payload, ensure_ascii=False)}")

        # 发送请求到 Dify
        response = requests.post(
            dify_chat_url,
            headers=headers,
            json=dify_payload,
            stream=True,
            timeout=120
        )

        # 检查 HTTP 错误状态
        if not response.ok:
            try:
                error_json = response.json()
                print(f"Dify Service: API 错误响应: {error_json}")
                
                # 返回一个包含错误信息的事件，让前端能够正确显示
                error_text = "Dify API错误"
                
                # 文件类型错误特殊处理
                if error_json.get('code') == 'invalid_param' and 'type does not match' in error_json.get('message', ''):
                    error_text = f"文件类型错误: Dify无法处理您上传的文件类型。请尝试使用TXT或PDF格式。"
                elif error_json.get('code') == 'file_not_accessible':
                    error_text = f"文件无法访问: 服务器无法读取您上传的文件。请重新上传。"
                else:
                    error_text = f"Dify API错误: {error_json.get('message', '')}"
                
                # 生成错误事件
                yield f"data: {{\"event\": \"error\", \"message\": \"{error_text}\"}}\n\n".encode('utf-8')
                
                # 如果已返回错误事件，就不要再抛出异常了
                print(f"Dify Service: 已发送错误事件到前端: {error_text}")
                return
                
            except Exception as json_err:
                print(f"Dify Service: 解析API错误响应失败: {json_err}")
                print(f"Dify Service: API 返回非 JSON 错误: {response.text[:500]}...")
                # 生成通用错误事件
                error_text = f"服务器错误，状态码: {response.status_code}"
                yield f"data: {{\"event\": \"error\", \"message\": \"{error_text}\"}}\n\n".encode('utf-8')
                return

        # 只有在没有发送错误事件的情况下才继续
        response.raise_for_status()

        # 流式返回响应内容
        for chunk in response.iter_content(chunk_size=None):
            if chunk:
                yield chunk

    except requests.exceptions.RequestException as e:
        print(f"Dify Service: 调用 Dify API 时出错 ({dify_chat_url}): {e}")
        error_text = f"调用Dify API时出错: {str(e)}"
        yield f"data: {{\"event\": \"error\", \"message\": \"{error_text}\"}}\n\n".encode('utf-8')
        raise