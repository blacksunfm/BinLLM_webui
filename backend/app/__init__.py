from flask import Flask
from flask_cors import CORS
import os

# Import configuration functions
from . import config as app_config

def create_app():
    """Factory function to create the Flask application."""
    app = Flask(__name__)
    
    # 根据环境变量配置CORS
    if os.getenv('FLASK_ENV') == 'production':
        # 生产环境：限制允许的源
        allowed_origins = os.getenv('ALLOWED_ORIGINS', 'https://your-frontend-domain.com').split(',')
        CORS(app,
             resources={r"/*": {"origins": allowed_origins}},
             methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
             allow_headers=["Content-Type", "Authorization", "Accept", "X-Requested-With"],
             expose_headers=["Content-Length", "Content-Type"],
             supports_credentials=True
        )
        print(f"生产环境CORS配置已启用，允许的源: {allowed_origins}")
    else:
        # 开发环境：允许所有源
        CORS(app,
             resources={r"/*": {"origins": "*"}},
             methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
             allow_headers=["Content-Type", "Authorization", "Accept", "X-Requested-With"],
             expose_headers=["Content-Length", "Content-Type"],
             supports_credentials=True
        )
        print("开发环境CORS配置已启用，支持所有源。")

    print("Loading initial Dify configuration...")
    app_config.load_config()

    from .routes.main_routes import init_blueprints
    init_blueprints(app)
    print("Registered all blueprints.")

    @app.route('/')
    def index():
        return "Backend server is running."

    return app 