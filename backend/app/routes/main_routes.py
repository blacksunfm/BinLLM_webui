from flask import Blueprint
from flask import send_from_directory
from flask import current_app
import os

# 创建主蓝图
main_bp = Blueprint('main', __name__)

def init_blueprints(app):
    """初始化所有蓝图并注册到Flask应用"""
    # 导入蓝图 - 使用绝对导入
    from app.routes.chat_routes import chat_bp
    from app.routes.history_routes import history_bp
    
    # 将所有子蓝图注册到Flask应用
    app.register_blueprint(chat_bp)
    app.register_blueprint(history_bp)
    
    print("完成所有蓝图注册")

    # 新增：静态文件服务，暴露uploads目录
    import os
    from flask import send_from_directory
    @app.route('/uploads/<path:filename>')
    def serve_uploads(filename):
        uploads_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'uploads'))
        return send_from_directory(uploads_dir, filename) 