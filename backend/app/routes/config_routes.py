from flask import Blueprint, request, jsonify
from .. import config as app_config

# 创建配置路由蓝图
config_bp = Blueprint('config', __name__, url_prefix='/config')

@config_bp.route('', methods=['POST'])
def configure_dify():
    """配置Dify API设置"""
    data = request.json
    model = data.get('model')
    api_url = data.get('api_url')
    api_key = data.get('api_key')

    if not model or not api_url or not api_key:
        return jsonify({"error": "缺少model、api_url或api_key参数"}), 400
    
    try:
        app_config.save_config(model, api_url, api_key)
        return jsonify({"message": f"{model}配置保存成功"}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        print(f"配置保存错误: {e}")
        return jsonify({"error": "配置保存失败"}), 500

@config_bp.route('', methods=['GET'])
def get_dify_config():
    """获取Dify API配置信息"""
    config_data = app_config.get_configs_for_frontend()
    return jsonify(config_data), 200 