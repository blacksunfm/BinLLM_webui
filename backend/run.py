from app import create_app
# from flask_cors import CORS 不需要在这里导入

app = create_app()

# 不在这里配置CORS，已在app/__init__.py中完成配置
# CORS(app, 
#      resources={r"/*": {"origins": "*"}}, 
#      methods=["GET", "POST", "PUT", "DELETE"], 
#      allow_headers=["Content-Type"] 
# )

if __name__ == '__main__':
    print("Starting Flask development server...")
    app.run(host='0.0.0.0', port=5004, debug=True)