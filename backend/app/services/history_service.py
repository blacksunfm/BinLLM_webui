import json
import os
import glob
import uuid
from datetime import datetime
import logging
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 根目录下创建模型子目录
HISTORY_DIR = os.path.join(os.path.dirname(__file__), '..', '..' ,'history')
if not os.path.exists(HISTORY_DIR):
    try:
        os.makedirs(HISTORY_DIR)
        print(f"Created history directory: {HISTORY_DIR}")
    except OSError as e:
        print(f"Error creating history directory {HISTORY_DIR}: {e}")

# 为每个模型创建子目录
def ensure_model_directory(model):
    """确保模型的历史目录存在"""
    model_dir = os.path.join(HISTORY_DIR, model)
    if not os.path.exists(model_dir):
        try:
            os.makedirs(model_dir)
            print(f"Created history directory for model {model}: {model_dir}")
        except OSError as e:
            print(f"Error creating history directory for model {model}: {e}")
    return model_dir

# 确保默认模型目录存在
model_ids = [f'dify{i}' for i in range(1, 11)] # 生成 dify1 到 dify10
for model in model_ids:
    ensure_model_directory(model)

# --- Internal Helper --- 
def _get_history_filepath(conversation_id: str, model: str = 'dify1') -> str:
    """Returns the full path for a conversation's history file."""
    # Basic validation/sanitization (prevent path traversal)
    if not conversation_id or '..' in conversation_id or '/' in conversation_id or '\\' in conversation_id:
        raise ValueError("Invalid conversation ID format.")
    
    # 获取模型目录
    model_dir = ensure_model_directory(model)
    return os.path.join(model_dir, f"{conversation_id}.json")

def _extract_conversation_name(history):
    """从历史记录中提取对话名称，优先使用第一条用户消息，跳过元数据"""
    if not history or not isinstance(history, list):
        return None
    
    # 过滤掉可能的元数据条目（包含creation_time或dify_conversation_id的字典）
    actual_messages = [msg for msg in history 
                       if not (isinstance(msg, dict) and 
                               ('creation_time' in msg or 'dify_conversation_id' in msg))]
    
    if not actual_messages:
        return None # 如果过滤后没有消息了，返回None
        
    # 优先寻找第一条用户消息作为对话名称
    for msg in actual_messages:
        if msg.get('sender') == 'user' and 'text' in msg:
            first_msg = msg['text'].strip()
            if first_msg:
                # 截取合适长度作为对话名称
                return first_msg[:30] + "..." if len(first_msg) > 30 else first_msg
    
    # 如果没有找到用户消息，使用过滤后的第一条消息
    first_message_obj = actual_messages[0]
    if first_message_obj.get('text'):
        first_msg = first_message_obj['text'].strip()
        if first_msg:
            return first_msg[:30] + "..." if len(first_msg) > 30 else first_msg
    
    # 如果连第一条消息的文本都没有，返回None
    return None

# --- Public Service Functions --- 

def create_new_conversation(model: str = 'dify1') -> str:
    """
    创建新的对话，并生成基于日期的对话ID
    Args:
        model: 使用的模型名称
    Returns:
        str: 新创建的对话ID
    """
    try:
        # 首先确保模型目录存在
        model_dir = ensure_model_directory(model)
        if not os.path.exists(model_dir):
            print(f"目录创建失败，尝试再次创建: {model_dir}")
            try:
                os.makedirs(model_dir, exist_ok=True)
            except Exception as mkdir_error:
                raise IOError(f"无法创建模型目录 {model_dir}: {mkdir_error}") 
                
        # 检查目录是否可写
        if not os.access(model_dir, os.W_OK):
            raise IOError(f"模型目录 {model_dir} 没有写入权限")
                
        # 生成基于日期的对话ID
        date_str = datetime.now().strftime("%Y%m%d")
        # 获取当天已有的对话数量，用于生成序号
        existing_files = glob.glob(os.path.join(model_dir, f"{date_str}*.json"))
        
        # 创建序号后缀
        suffix = len(existing_files) + 1
        # 生成最终的对话ID
        conversation_id = f"{date_str}_{suffix}_{uuid.uuid4().hex[:8]}"
        
        # 创建空的历史记录文件
        filepath = _get_history_filepath(conversation_id, model)
        
        # 添加元数据
        metadata = {
            "creation_time": datetime.utcnow().isoformat() + 'Z',
            "model": model,
            "conversation_id": conversation_id, # 本地日期ID
            "dify_conversation_id": None, # 初始化 Dify UUID 字段
            "custom_name": "聊天助手" # 默认对话名称
        }
        
        # 创建包含元数据的空历史记录
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump([metadata], f, ensure_ascii=False, indent=2)
            print(f"History Service: 成功创建新对话，ID: {conversation_id}，文件: {filepath}")
        except IOError as file_error:
            raise IOError(f"写入对话文件失败 {filepath}: {file_error}")
        
        return conversation_id
    
    except Exception as e:
        print(f"History Service Error: 创建新对话失败: {e}")
        # 如果创建失败，返回基于UUID的备用ID
        fallback_id = f"new_{uuid.uuid4().hex}"
        print(f"History Service: 使用备用ID: {fallback_id}")
        return fallback_id

def save_message(conversation_id: str, message: dict, model: str = 'dify1'):
    """
    Appends a message to the conversation's history file (identified by date-based ID).
    Creates the file if it doesn't exist (should normally exist).

    Args:
        conversation_id: The date-based ID of the conversation.
        message: A dictionary representing the message.
        model: The model this message belongs to.
    """
    # 确保消息格式正确 - 支持'sender'或'role'作为消息发送者标识
    if not isinstance(message, dict):
        print(f"History Service Error: 消息不是字典格式，无法保存 - {message}")
        return False
    
    # 处理前端可能使用 role 字段来标识发送者 (如 'user', 'assistant') 的情况
    # 标准化为 sender 字段
    if 'role' in message and 'sender' not in message:
        message['sender'] = message['role']
    
    # 确保必要字段存在
    if 'sender' not in message:
        print(f"History Service Error: 消息缺少 sender 字段，无法保存 - {message}")
        return False
    
    if 'text' not in message:
        print(f"History Service Error: 消息缺少 text 字段，无法保存 - {message}")
        return False
        
    # 添加 timestamp 到消息，如果消息中已有，则保留原有的
    message_with_timestamp = {
        **message,
        'timestamp': message.get('timestamp', datetime.utcnow().isoformat() + 'Z'),
        'model': model # 确保包含模型信息
    }
    
    if 'isLoading' in message_with_timestamp:
        del message_with_timestamp['isLoading']
    if 'isError' in message_with_timestamp:
        del message_with_timestamp['isError']

    try:
        filepath = _get_history_filepath(conversation_id, model)
        history = []
        
        # 读取现有历史记录
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                    if not isinstance(history, list):
                        print(f"Warning: History file {filepath} is not a list. Overwriting with metadata + new message.")
                        # 创建包含元数据的列表，如果文件内容无效
                        metadata = {
                            "creation_time": datetime.utcnow().isoformat() + 'Z',
                            "model": model,
                            "conversation_id": conversation_id,
                            "dify_conversation_id": None 
                        }
                        history = [metadata]
            except json.JSONDecodeError:
                print(f"Warning: Could not decode JSON from {filepath}. Overwriting with metadata + new message.")
                metadata = {
                    "creation_time": datetime.utcnow().isoformat() + 'Z',
                    "model": model,
                    "conversation_id": conversation_id,
                    "dify_conversation_id": None 
                }
                history = [metadata]
            except Exception as read_err:
                 print(f"Error reading history file {filepath}, cannot append: {read_err}")
                 return False
        else:
            print(f"Warning: History file {filepath} not found. Creating new file with metadata.")
            metadata = {
                "creation_time": datetime.utcnow().isoformat() + 'Z',
                "model": model,
                "conversation_id": conversation_id,
                "dify_conversation_id": None 
            }
            history = [metadata]

        # 跳过重复消息
        is_duplicate = False
        for existing_msg in history:
            if (isinstance(existing_msg, dict) and
                existing_msg.get('sender') == message_with_timestamp.get('sender') and
                existing_msg.get('text') == message_with_timestamp.get('text')):
                print(f"History Service: Skipping duplicate message for {conversation_id}")
                is_duplicate = True
                break
                
        if not is_duplicate:
            # 追加新消息
            history.append(message_with_timestamp)
            
            # 写回文件
            try:
                # 确保目录存在 (以防万一)
                model_dir = os.path.dirname(filepath)
                if not os.path.exists(model_dir):
                    os.makedirs(model_dir)
                    
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(history, f, ensure_ascii=False, indent=2)
                print(f"History Service: 成功保存消息到对话 {conversation_id} (模型: {model})")
                return True
            except OSError as write_err:
                 print(f"History Service Error: 无法写入文件 {filepath}. {write_err}")
                 return False

    except ValueError as e: # 来自 _get_history_filepath
        print(f"History Service Error: {e}")
        return False
    except Exception as e:
        print(f"History Service Error: 保存消息时发生意外错误: {e}")
        return False
        
    return True

def update_dify_conversation_id(local_id: str, dify_id: str, model: str = 'dify1'):
    """更新本地历史文件，记录 Dify 返回的真实会话 ID"""
    if not local_id or not dify_id:
        print("Update Dify ID Error: Missing local_id or dify_id")
        return
        
    try:
        filepath = _get_history_filepath(local_id, model)
        if not os.path.exists(filepath):
            print(f"Update Dify ID Warning: File not found {filepath}, cannot update.")
            # 如果文件不存在，可能意味着初始创建失败，或者已经被意外删除
            # 此时无法更新 Dify ID，后续保存消息可能会重建文件（不含Dify ID）
            return

        history = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                history = json.load(f)
            if not isinstance(history, list) or not history:
                print(f"Update Dify ID Warning: File {filepath} is empty or not a list. Cannot update Dify ID.")
                return 
        except Exception as read_err:
            print(f"Update Dify ID Error: Failed to read file {filepath}: {read_err}")
            return

        # 查找或创建元数据条目来更新 Dify ID
        metadata_updated = False
        for item in history:
            if isinstance(item, dict) and 'creation_time' in item and 'conversation_id' in item:
                item['dify_conversation_id'] = dify_id
                metadata_updated = True
                break # 假设只有一个元数据条目
        
        # 如果没有找到元数据条目（理论上不应该，除非文件被手动修改）
        # 可以选择插入一个新的元数据条目，或者放弃更新
        if not metadata_updated:
            print(f"Update Dify ID Warning: Metadata entry not found in {filepath}. Cannot set Dify ID.")
            # 为了健壮性，可以考虑添加一个元数据条目，但这可能不符合预期
            # metadata_entry = {"dify_conversation_id": dify_id}
            # history.insert(0, metadata_entry) # 插入到开头
            return # 暂时选择不更新

        # 写回更新后的历史记录
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
            print(f"History Service: Updated Dify ID in {local_id} to {dify_id}")
        except OSError as write_err:
            print(f"Update Dify ID Error: Failed to write updated file {filepath}: {write_err}")

    except ValueError as e: # 来自 _get_history_filepath
        print(f"Update Dify ID Error: {e}")
    except Exception as e:
        print(f"Update Dify ID Error: Unexpected error: {e}")

def rename_conversation_name(conversation_id: str, new_name: str, model: str = 'dify1'):
    """更新存储在历史文件元数据中的对话名称"""
    if not conversation_id or not new_name:
        print("Rename Name Error: Missing conversation_id or new_name")
        return False
    
    new_name = new_name.strip()
    if not new_name: # 不允许空名称
        print("Rename Name Error: New name cannot be empty after stripping whitespace")
        return False
        
    try:
        filepath = _get_history_filepath(conversation_id, model)
        if not os.path.exists(filepath):
            print(f"Rename Name Error: File not found {filepath}")
            return False

        history = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                history = json.load(f)
            if not isinstance(history, list) or not history:
                print(f"Rename Name Error: File {filepath} is empty or not a list.")
                return False 
        except Exception as read_err:
            print(f"Rename Name Error: Failed to read file {filepath}: {read_err}")
            return False

        # 查找元数据条目并更新 custom_name
        metadata_updated = False
        for item in history:
            if isinstance(item, dict) and 'creation_time' in item and 'conversation_id' in item:
                item['custom_name'] = new_name # 添加或更新自定义名称字段
                metadata_updated = True
                break 
        
        if not metadata_updated:
            print(f"Rename Name Error: Metadata entry not found in {filepath}. Cannot set custom name.")
            # 如果没有元数据，这是一个异常情况，不应该发生
            return False

        # 写回更新后的历史记录
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
            print(f"History Service: Updated custom name in {conversation_id} to '{new_name}'")
            return True
        except OSError as write_err:
            print(f"Rename Name Error: Failed to write updated file {filepath}: {write_err}")
            return False

    except ValueError as e: # 来自 _get_history_filepath
        print(f"Rename Name Error: Invalid ID format. {e}")
        return False
    except Exception as e:
        print(f"Rename Name Error: Unexpected error: {e}")
        return False

def get_messages(conversation_id: str, model: str = 'dify1') -> list:
    """Reads and returns the list of messages for a conversation, excluding metadata."""
    try:
        filepath = _get_history_filepath(conversation_id, model)
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                    if not isinstance(history, list):
                        return [] # Or raise error?
                        
                    # 过滤掉元数据条目
                    actual_messages = [msg for msg in history 
                                       if not (isinstance(msg, dict) and 
                                               ('creation_time' in msg or 'dify_conversation_id' in msg))]
                    return actual_messages
                    
            except (json.JSONDecodeError, Exception) as e:
                print(f"History Service Error: Could not read or parse {filepath}: {e}")
                return [] # Return empty list on error
        else:
            return [] # No history found
    except ValueError as e:
         print(f"History Service Error: {e}")
         return []

def list_conversations(model: str = 'dify1') -> list:
    """Lists available conversations based on history files for a specific model."""
    conversations = []
    try:
        model_dir = ensure_model_directory(model)
        history_files = glob.glob(os.path.join(model_dir, '*.json'))
        
        for filepath in history_files:
            try:
                conv_id = os.path.splitext(os.path.basename(filepath))[0]
                mtime = os.path.getmtime(filepath)
                
                conv_name = "聊天助手" # 默认名称
                
                # 尝试读取文件以获取自定义名称
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        history = json.load(f)
                        if history and isinstance(history[0], dict):
                            custom_name = history[0].get('custom_name')
                            if custom_name:
                                conv_name = custom_name # 使用自定义名称
                except Exception as read_err:
                    print(f"Warning: Could not read file {filepath} to get custom name: {read_err}")
                
                conversations.append({
                    "id": conv_id, 
                    "name": conv_name,
                    "timestamp": int(mtime * 1000),
                    "model": model
                })
            except Exception as e:
                print(f"History Service: Error processing file {filepath}: {e}")
                continue 
        
        conversations.sort(key=lambda x: x['timestamp'], reverse=True)
        
    except Exception as e:
        print(f"History Service Error: Could not list conversations for model {model}: {e}")

    return conversations

def delete_conversation(conversation_id: str, model: str = 'dify1') -> bool:
    """删除指定模型的会话历史记录文件

    Args:
        conversation_id: 会话ID
        model: 模型名称

    Returns:
        bool: 删除是否成功
    """
    try:
        filepath = _get_history_filepath(conversation_id, model)
        if os.path.exists(filepath):
            os.remove(filepath)
            print(f"History Service: Deleted conversation file: {filepath}")
            return True
        else:
            print(f"History Service: Conversation file not found: {filepath}")
            return False
    except ValueError as e:
        print(f"History Service Error: {e}")
        return False
    except OSError as e:
        print(f"History Service Error: Could not delete file {filepath}. {e}")
        return False
    except Exception as e:
        print(f"History Service Error: An unexpected error occurred deleting conversation: {e}")
        return False 