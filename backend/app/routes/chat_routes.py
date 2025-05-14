from flask import Blueprint, request, jsonify, Response
import requests
import json
import os
from werkzeug.utils import secure_filename
from .. import config as app_config
from ..services import dify_service, history_service
from datetime import datetime

# 创建聊天路由蓝图
chat_bp = Blueprint('chat', __name__, url_prefix='/chat')

# 允许的文件类型
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx', 'doc', 'md', 'jpg', 'jpeg', 'png', 'csv', 'xlsx', 'xls'}

def allowed_file(filename):
    """检查文件扩展名是否在允许列表中。"""
    # 如果没有扩展名，也先允许，后续处理中会添加扩展名
    if '.' not in filename:
        return True
    
    # 有扩展名的情况，检查是否在允许列表中
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS

# 文件上传路由
@chat_bp.route('/upload', methods=['POST'])
def upload_file():
    """处理文件上传请求。将文件保存到临时位置，然后上传到Dify API。"""
    if 'file' not in request.files:
        return jsonify({"error": "未找到上传文件"}), 400

    file = request.files['file']
    model = request.form.get('model', 'dify1')
    conversation_id = request.form.get('conversation_id') # 本地日期格式ID
    user = request.form.get('user', 'default-user') # 从表单获取用户ID，提供默认值

    if file.filename == '':
        return jsonify({"error": "未选择文件"}), 400

    if not conversation_id:
        return jsonify({"error": "未提供对话ID"}), 400

    try:
        current_config = app_config.get_model_config(model)
        api_url = current_config.get('api_url')
        api_key = current_config.get('api_key')

        if not api_url or not api_key:
            return jsonify({"error": f"{model} API未配置"}), 400

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            temp_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'uploads')
            os.makedirs(temp_dir, exist_ok=True)
            file_path = os.path.join(temp_dir, filename)
            file.save(file_path)

            try:
                base_url = api_url.rstrip('/')
                dify_files_url = f"{base_url}/files/upload"

                headers = {
                    'Authorization': f'Bearer {api_key}'
                }

                # 简化的用户数据
                dify_form_data = {
                    'user': user
                }
                
                print(f"上传文件到Dify: {filename}")

                # 打印请求详情以便调试
                print(f"Dify请求URL: {dify_files_url}")
                print(f"Dify请求头: Authorization: Bearer ***{api_key[-5:]}")

                # 将文件转发给Dify - 使用"text/plain"作为通用MIME类型
                with open(file_path, 'rb') as f:
                    try:
                        dify_response = requests.post(
                            dify_files_url,
                            headers=headers,
                            files={'file': (file.filename, f, "text/plain")},
                            data=dify_form_data,
                            timeout=60
                        )
                    except requests.exceptions.RequestException as req_err:
                        print(f"Dify文件上传请求异常: {req_err}")
                        return jsonify({"error": f"上传文件到Dify失败: {str(req_err)}"}), 500

                if not dify_response.ok:
                    error_message = "上传到Dify失败"
                    try:
                        error_data = dify_response.json()
                        print(f"Dify文件上传错误: {error_data}")
                        error_message = f"Dify错误: {error_data.get('message', error_data.get('error', '未知错误'))}"
                    except Exception as parse_error:
                        print(f"解析Dify错误响应失败: {parse_error}")
                        try:
                            print(f"错误响应文本: {dify_response.text[:1000]}")
                        except:
                            pass
                        error_message = f"Dify错误: {dify_response.status_code} {dify_response.reason}"
                    return jsonify({"error": error_message}), dify_response.status_code

                dify_result = dify_response.json()
                print(f"Dify文件上传成功: {dify_result}")

                # 尝试获取对应的Dify对话ID（如果存在）
                dify_conversation_id = dify_service.get_dify_conversation_id(conversation_id, model)

                return jsonify({
                    "success": True,
                    "file_id": dify_result.get('id'),
                    "name": filename,
                    "type": "document", # 默认文件类型
                    "dify_info": dify_result,
                    "dify_conversation_id": dify_conversation_id
                })

            finally:
                # 清理临时上传文件
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        print(f"错误：清理临时文件 '{file_path}' 失败: {e}")
        else:
            return jsonify({"error": f"不支持的文件类型。允许的类型: {', '.join(ALLOWED_EXTENSIONS)}"}), 400

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Dify API通信错误: {str(e)}"}), 500
    except Exception as e:
        print(f"文件上传处理中发生意外错误: {e}") # 保留此错误日志
        return jsonify({"error": f"文件上传处理错误"}), 500

# 聊天主路由，用于向dify请求
@chat_bp.route('', methods=['POST'])
def chat_with_dify():
    """处理聊天请求，与Dify API交互并返回流式响应。"""
    data = request.json
    query = data.get('query')
    model = data.get('model', 'dify1')
    conversation_id_from_req = data.get('conversation_id') # 本地日期格式ID或null
    user = data.get('user', 'default-user')
    inputs = data.get('inputs', {})

    # 从请求中获取文件ID列表 - 前端可能使用 file_ids 或 files 字段
    file_ids = data.get('files', []) or data.get('file_ids', [])
    
    print(f"聊天路由：接收到的请求数据：{json.dumps(data, ensure_ascii=False)}")
    print(f"聊天路由：处理的文件ID列表：{file_ids}")

    if not query and not file_ids: # 如果没有文本查询也没有文件，则无效
        return jsonify({"error": "缺少query或file_ids参数"}), 400
    if not query: # 如果只有文件，提供一个默认查询
        query = "请基于我上传的文件进行分析或回答。"

    try:
        current_config = app_config.get_model_config(model)
        api_url = current_config.get('api_url')
        api_key = current_config.get('api_key')

        if not api_url or not api_key:
            return jsonify({"error": f"{model} API未配置"}), 400

        # 按照Python示例和Dify API文档准备payload
        payload = {
            "inputs": {}, # 空对象
            "query": query,
            "response_mode": "streaming", # 始终使用流式响应
            "conversation_id": conversation_id_from_req or "", # 传递本地ID、null或空字符串
            "user": user,
            "model": model
        }
        
        # 只有在有文件时才添加files字段，确保与Python脚本格式完全一致
        if file_ids:
            # 转换格式为与Python脚本完全相同的格式
            formatted_files = []
            for file_id in file_ids:
                # 确保每个文件引用都使用标准格式
                if isinstance(file_id, dict) and 'upload_file_id' in file_id:
                    # 已经是格式化的对象，确保格式正确
                    file_ref = {
                        "type": "document",
                        "transfer_method": "local_file",
                        "upload_file_id": file_id['upload_file_id']
                    }
                    formatted_files.append(file_ref)
                else:
                    # 简单的ID字符串，转换为正确格式
                    file_ref = {
                        "type": "document",
                        "transfer_method": "local_file",
                        "upload_file_id": file_id
                    }
                    formatted_files.append(file_ref)
            
            # 添加格式化后的文件引用到payload
            payload["files"] = formatted_files
        
        print(f"聊天路由：发送到Dify服务的payload: {json.dumps(payload, ensure_ascii=False)}")

        # 调用Dify服务层处理与API的交互
        stream_generator = dify_service.stream_dify_chat(api_url, api_key, payload)

        # 自定义流生成器，用于在流结束后更新本地存储的Dify对话ID
        def custom_stream_generator():
            dify_uuid_received = None
            original_local_id = conversation_id_from_req

            for chunk in stream_generator:
                # 尝试从流的结束事件中解析Dify返回的对话ID
                try:
                    decoded_chunk = chunk.decode('utf-8', errors='ignore')
                    if decoded_chunk.strip().startswith('data:'):
                        data_str = decoded_chunk.strip()[5:].strip()
                        if data_str:
                            try:
                                data = json.loads(data_str)
                                if data.get('event') == 'message_end' and data.get('conversation_id'):
                                    dify_uuid_received = data['conversation_id']
                            except json.JSONDecodeError:
                                pass
                except Exception as e:
                    print(f"警告：解析流数据块以获取Dify ID时出错: {e}")

                yield chunk # 将原始数据块传递给客户端

            # 流结束后，如果这是一个新的本地对话且收到了Dify ID，则更新历史记录
            if original_local_id and dify_uuid_received and original_local_id != dify_uuid_received:
                 # 仅当我们自己的日期格式ID时才更新
                 if '_' in original_local_id:
                     try:
                         history_service.update_dify_conversation_id(original_local_id, dify_uuid_received, model)
                         print(f"信息：更新本地对话 {original_local_id} 的 Dify ID 为 {dify_uuid_received}")
                     except Exception as update_e:
                         print(f"错误：更新 Dify ID 时失败: {update_e}")

        return Response(custom_stream_generator(), mimetype='text/event-stream')

    except ValueError as e: # 配置或请求数据问题
        return jsonify({"error": str(e)}), 400
    except requests.exceptions.RequestException as e: # Dify API通信错误
        print(f"错误：与Dify API通信失败: {e}") # 保留此错误日志
        error_message = f"与Dify API通信失败: {str(e)}"
        status_code = 500
        if e.response is not None:
             status_code = e.response.status_code
             try:
                 # 尝试解析Dify返回的错误信息
                 error_detail = e.response.json()
                 msg = error_detail.get('message', error_detail.get('error', '未知错误'))
                 code = error_detail.get('code', '')
                 error_message = f"Dify API 错误: {msg} {code}".strip()
             except:
                 error_message = f"Dify API 错误: {e.response.status_code} {e.response.reason}"

        return jsonify({"error": error_message}), status_code
    except Exception as e:
        print(f"聊天处理中发生意外错误: {e}") # 保留此错误日志
        return jsonify({"error": "服务器内部错误"}), 500


