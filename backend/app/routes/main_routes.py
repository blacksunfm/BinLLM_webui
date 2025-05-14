from flask import Blueprint

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