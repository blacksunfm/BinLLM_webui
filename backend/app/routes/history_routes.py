from flask import Blueprint, request, jsonify
from ..services import history_service
from datetime import datetime

# 创建历史记录路由蓝图 - 修改URL前缀为/chat以保持与前端接口一致
history_bp = Blueprint('history', __name__, url_prefix='/chat')

# --- 对话管理路由 ---

# 获取历史记录路由 - 前端使用 /chat/conversations
@history_bp.route('/conversations', methods=['GET'])
def get_conversations_list():
    """获取指定模型的对话列表"""
    # 从查询参数获取 model，如果未提供则默认为 'dify1'
    model = request.args.get('model', 'dify1') 
    print(f"历史路由: 请求获取模型 '{model}' 的对话列表")
    try:
        # 将获取到的 model 传递给 history_service
        conversations = history_service.list_conversations(model=model)
        print(f"历史路由: 返回 {len(conversations)} 个对话")
        return jsonify(conversations)
    except Exception as e:
        print(f"历史路由错误: 获取模型 '{model}' 的对话列表失败: {e}")
        return jsonify({"error": f"无法获取模型 '{model}' 的对话列表"}), 500

# 创建新对话路由 - 前端使用 /chat/conversations
@history_bp.route('/conversations', methods=['POST'])
def create_new_conversation_route():
    """创建新对话路由"""
    data = request.json
    model = data.get('model', 'dify1') # 从请求体获取 model
    print(f"历史路由: 请求为模型 '{model}' 创建新对话")
    try:
        conversation_id = history_service.create_new_conversation(model=model)
        # 返回包含ID和默认名称/时间戳的对象，以便前端可以直接使用
        new_conv_info = {
            "id": conversation_id,
            "name": "聊天助手", # 初始名称
            "timestamp": datetime.utcnow().isoformat() + 'Z' # 提供时间戳
        }
        print(f"历史路由: 新对话创建成功，ID: {conversation_id}")
        return jsonify(new_conv_info), 201
    except Exception as e:
        print(f"历史路由错误: 创建新对话失败 (模型: '{model}'): {e}")
        return jsonify({"error": f"无法为模型 '{model}' 创建新对话"}), 500

# 获取特定对话的消息历史路由 - 前端使用 /chat/conversations/<id>/messages
@history_bp.route('/conversations/<string:conversation_id>/messages', methods=['GET'])
def get_conversation_history_route(conversation_id):
    """获取特定对话的消息历史"""
    model = request.args.get('model', 'dify1') # 从查询参数获取 model
    print(f"历史路由: 请求获取对话 '{conversation_id}' (模型: '{model}') 的历史消息")
    try:
        messages = history_service.get_messages(conversation_id=conversation_id, model=model)
        print(f"历史路由: 返回 {len(messages)} 条消息")
        return jsonify(messages)
    except FileNotFoundError:
        print(f"历史路由错误: 对话 '{conversation_id}' (模型: '{model}') 未找到")
        return jsonify({"error": "对话未找到"}), 404
    except Exception as e:
        print(f"历史路由错误: 获取对话 '{conversation_id}' (模型: '{model}') 历史失败: {e}")
        return jsonify({"error": "无法获取对话历史"}), 500

# 保存单条消息到特定对话的历史路由 - 前端使用 /chat/conversations/<id>/messages
@history_bp.route('/conversations/<string:conversation_id>/messages', methods=['POST'])
def save_message_route(conversation_id):
    """接收前端发送的单条消息并保存到历史记录"""
    data = request.json
    message = data.get('message')
    model = data.get('model') # 从请求体获取 model
    
    if not message or not isinstance(message, dict):
        print(f"历史路由错误: 无效的消息数据: {message}")
        return jsonify({"error": "无效的消息数据"}), 400
    if not model:
         # 如果前端没传 model，尝试从 message 中获取，或使用默认值
         model = message.get('model', 'dify1') 
         print(f"历史路由警告: 请求体缺少 'model'，使用推断/默认值: {model}")

    print(f"历史路由: 请求保存消息到对话 '{conversation_id}' (模型: '{model}')")
    
    try:
        # 调用 history_service 保存消息
        # 注意：history_service.save_message 会自动添加时间戳
        result = history_service.save_message(conversation_id=conversation_id, message=message, model=model)
        if result:
            print(f"历史路由: 消息成功保存到对话 '{conversation_id}'")
            return jsonify({"message": "消息保存成功"}), 201
        else:
            print(f"历史路由错误: 消息保存失败")
            return jsonify({"error": "消息保存失败"}), 500
    except ValueError as e: # 可能来自 history_service 的 ID 验证
        print(f"历史路由错误: 保存消息时出错 (ValueError): {e}")
        return jsonify({"error": str(e)}), 400
    except FileNotFoundError:
         print(f"历史路由错误: 对话 '{conversation_id}' (模型: '{model}') 未找到，无法保存消息")
         return jsonify({"error": "对话未找到，无法保存消息"}), 404
    except IOError as e:
        print(f"历史路由错误: 保存消息时发生IO错误: {e}")
        return jsonify({"error": "保存消息时发生文件写入错误"}), 500
    except Exception as e:
        print(f"历史路由错误: 保存消息时发生意外错误: {e}")
        return jsonify({"error": "服务器内部错误"}), 500

# 重命名对话路由 - 前端使用 /chat/conversations/<id>/name
@history_bp.route('/conversations/<string:conversation_id>/name', methods=['PUT'])
def rename_conversation_route(conversation_id):
    """重命名对话路由"""
    data = request.json
    # print(f"调试 历史路由: 请求重命名对话 data信息: {data}") # data信息: {'name': '聊天助手1'}
    # print(f"调试 历史路由: 请求重命名对话 request.args信息: {request.args}") # request.args信息: ImmutableMultiDict([('model', 'dify2')])
    new_name = data.get('name')
    model = request.args.get('model', 'dify1') # 从查询参数获取 model
    
    if not new_name:
        return jsonify({"error": "缺少新的对话名称 'name'"}), 400
        
    print(f"历史路由: 请求重命名对话 '{conversation_id}' (模型: '{model}') 为 '{new_name}'")
    try:
        success = history_service.rename_conversation_name(conversation_id=conversation_id, new_name=new_name, model=model)
        if success:
            print(f"历史路由: 对话 '{conversation_id}' 重命名成功")
            return jsonify({"message": "重命名成功"}), 200
        else:
            # rename_conversation_name 内部可能已经处理了文件不存在等情况
            print(f"历史路由错误: 重命名对话 '{conversation_id}' (模型: '{model}') 失败 (Service层返回False)")
            return jsonify({"error": "重命名失败"}), 404
    except Exception as e:
        print(f"历史路由错误: 重命名对话 '{conversation_id}' (模型: '{model}') 时发生异常: {e}")
        return jsonify({"error": "服务器内部错误"}), 500

# 删除对话路由 - 前端使用 /chat/conversations/<id>
@history_bp.route('/conversations/<string:conversation_id>', methods=['DELETE'])
def delete_conversation_route(conversation_id):
    """删除对话路由"""
    # model 应该从查询参数获取，因为 DELETE 请求通常没有 body
    model = request.args.get('model', 'dify1') 
    print(f"历史路由: 请求删除对话 '{conversation_id}' (模型: '{model}')")
    try:
        success = history_service.delete_conversation(conversation_id=conversation_id, model=model)
        if success:
            print(f"历史路由: 对话 '{conversation_id}' 删除成功")
            return jsonify({"message": "删除成功"}), 200
        else:
            print(f"历史路由错误: 删除对话 '{conversation_id}' (模型: '{model}') 失败 (未找到或无法删除)")
            return jsonify({"error": "删除失败，对话未找到或无法删除"}), 404
    except Exception as e:
        print(f"历史路由错误: 删除对话 '{conversation_id}' (模型: '{model}') 时发生异常: {e}")
        return jsonify({"error": "服务器内部错误"}), 500 