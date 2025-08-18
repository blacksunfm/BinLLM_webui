#!/usr/bin/env python3
"""
生产环境启动脚本
使用Gunicorn作为WSGI服务器
"""

import os
import sys
from app import create_app

# 设置生产环境变量
os.environ['FLASK_ENV'] = 'production'

app = create_app()

if __name__ == '__main__':
    # 开发模式直接运行
    print("Starting Flask production server...")
    app.run(host='0.0.0.0', port=5004, debug=False)
else:
    # Gunicorn模式
    # 使用: gunicorn -w 4 -b 0.0.0.0:5004 run_production:app
    pass 