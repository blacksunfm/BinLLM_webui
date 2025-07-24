from flask import Blueprint, request, jsonify, Response, send_file
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
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx', 'doc', 'md', 'jpg', 'jpeg', 'png', 'csv', 'xlsx', 'xls', 'exe', 'bin'}

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
    """处理文件上传请求。EXE文件将永久保存，其他文件按原有流程处理"""
    if 'file' not in request.files:
        return jsonify({"error": "未找到上传文件"}), 400

    file = request.files['file']
    model = request.form.get('model', 'dify1')
    conversation_id = request.form.get('conversation_id')
    user = request.form.get('user', 'default-user')

    if file.filename == '':
        return jsonify({"error": "未选择文件"}), 400

    if not conversation_id:
        return jsonify({"error": "未提供对话ID"}), 400

    try:
        # 获取文件扩展名
        file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        is_binary_file = file_ext in ['exe', 'bin']

        if not allowed_file(file.filename):
            return jsonify({"error": f"不支持的文件类型。允许的类型: {', '.join(ALLOWED_EXTENSIONS)}"}), 400

        # 创建上传目录
        upload_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        
        # 安全处理文件名
        filename = secure_filename(file.filename)
        file_path = os.path.join(upload_dir, filename)
        
        # 保存文件到上传目录
        file.save(file_path)
        print(f"文件已保存到: {file_path}")

        # 二进制文件特殊处理 - 不转发到Dify，直接返回保存路径
        if is_binary_file:
            return jsonify({
                "success": True,
                "file_path": file_path,
                "name": filename,
                "type": "binary",
                "message": "二进制文件已保存"
            })

        # 非EXE文件原有处理逻辑
        current_config = app_config.get_model_config(model)
        api_url = current_config.get('api_url')
        api_key = current_config.get('api_key')

        if not api_url or not api_key:
            return jsonify({"error": f"{model} API未配置"}), 400

        base_url = api_url.rstrip('/')
        dify_files_url = f"{base_url}/files/upload"

        headers = {
            'Authorization': f'Bearer {api_key}'
        }

        dify_form_data = {
            'user': user
        }
        
        with open(file_path, 'rb') as f:
            dify_response = requests.post(
                dify_files_url,
                headers=headers,
                files={'file': (filename, f, "text/plain")},
                data=dify_form_data,
                timeout=60
            )

        if not dify_response.ok:
            error_message = "上传到Dify失败"
            try:
                error_data = dify_response.json()
                error_message = f"Dify错误: {error_data.get('message', error_data.get('error', '未知错误'))}"
            except Exception:
                error_message = f"Dify错误: {dify_response.status_code} {dify_response.reason}"
            return jsonify({"error": error_message}), dify_response.status_code

        dify_result = dify_response.json()
        dify_conversation_id = dify_service.get_dify_conversation_id(conversation_id, model)

        return jsonify({
            "success": True,
            "file_id": dify_result.get('id'),
            "name": filename,
            "type": "document",
            "dify_info": dify_result,
            "dify_conversation_id": dify_conversation_id
        })

    except Exception as e:
        print(f"文件上传处理中发生错误: {e}")
        return jsonify({"error": f"文件处理错误: {str(e)}"}), 500
    finally:
        # 仅清理非EXE文件的临时文件
        if not is_binary_file and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"错误：清理临时文件 '{file_path}' 失败: {e}")

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
    if not query or query == '我上传了 1 个文件。': # 如果只有文件，提供一个默认查询
        query = "请基于我上传的文件进行漏洞分析，一步步地思考，包括代码功能，明确的漏洞，代码修复意见等。"

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


@chat_bp.route('/analyze/binary', methods=['POST'])
def analyze_binary():
    """分析二进制文件，提取函数名、汇编和反编译代码"""
    data = request.json
    filename = data.get('filename')
    if not filename:
        return jsonify({'error': '缺少文件名参数'}), 400
    
    upload_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'uploads')
    file_path = os.path.join(upload_dir, filename)
    if not os.path.exists(file_path):
        return jsonify({'error': '文件不存在'}), 404

    # 生成Ghidra输出路径
    output_json = os.path.join(upload_dir, f'{filename}_ghidra.json')
    ghidra_path = '/disk1/users/laiqj/ghidra_11.3.2_PUBLIC/support/analyzeHeadless'
    project_dir = os.path.join(upload_dir, 'ghidra_proj')
    script_path = os.path.join(upload_dir, 'analyse', 'combined_export.py')

    # 确保Ghidra项目目录存在
    os.makedirs(project_dir, exist_ok=True)

    # 调用Ghidra headless分析
    import subprocess, traceback
    try:
        cmd = [
            ghidra_path,
            project_dir,
            'tmp',
            '-import', file_path,
            '-postScript', script_path,
            '-deleteProject'
        ]
        env = os.environ.copy()
        env['OUTPUT_FILE'] = output_json
        print(f"调用Ghidra命令: {' '.join(cmd)}")
        print(f"环境变量OUTPUT_FILE: {output_json}")
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=600)
        print(f"Ghidra stdout: {result.stdout}")
        print(f"Ghidra stderr: {result.stderr}")
        if result.returncode != 0:
            return jsonify({'error': 'Ghidra分析失败', 'stderr': result.stderr}), 500
        if not os.path.exists(output_json):
            return jsonify({'error': 'Ghidra未生成分析结果'}), 500
        with open(output_json, 'r', encoding='utf-8') as f:
            analysis = json.load(f)
        return jsonify({'success': True, 'analysis': analysis})
    except Exception as e:
        print(f"分析异常: {e}")
        print(traceback.format_exc())
        return jsonify({'error': f'后端分析异常: {str(e)}'}), 500


