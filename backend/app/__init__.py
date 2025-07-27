from flask import Flask
from flask_cors import CORS

# Import configuration functions
from . import config as app_config

def create_app():
    """Factory function to create the Flask application."""
    app = Flask(__name__)
    
    # 配置 CORS：允许所有来源，所有常见方法和必要的请求头
    CORS(app,
         resources={r"/*": {"origins": "*"}}, # 允许所有源 
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"], # 包括所有可能的HTTP方法
         allow_headers=["Content-Type", "Authorization", "Accept", "X-Requested-With"], # 允许所有常见请求头
         expose_headers=["Content-Length", "Content-Type"], # 暴露这些响应头给前端
         supports_credentials=True # 支持凭据，如果需要Cookie或认证
    )
    print("增强的CORS配置已启用，支持所有常见请求头和方法。")

    print("Loading initial Dify configuration...")
    app_config.load_config()

    from .routes.main_routes import init_blueprints
    init_blueprints(app)
    print("Registered all blueprints.")

    @app.route('/')
    def index():
        return "Backend server is running."

    return app 