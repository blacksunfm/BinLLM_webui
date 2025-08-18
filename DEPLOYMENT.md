# API部署指南

## 概述
本项目是一个基于Flask的API服务，可以为外网用户提供聊天和文件上传功能。

## 部署前准备

### 1. 服务器要求
- Linux服务器（推荐Ubuntu 20.04+）
- Python 3.8+
- 至少2GB内存
- 公网IP地址

### 2. 域名配置
- 申请域名并解析到服务器IP
- 配置SSL证书（推荐使用Let's Encrypt）

## 部署步骤

### 1. 安装依赖
```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置环境变量
```bash
cp env.example .env
# 编辑 .env 文件，设置正确的域名和密钥
```

### 3. 修改配置文件
编辑 `backend/config.json`，将 `your-public-domain.com` 替换为实际的域名。

### 4. 使用Gunicorn启动服务
```bash
cd backend
gunicorn -w 4 -b 0.0.0.0:5004 run_production:app
```

### 5. 配置Nginx反向代理（推荐）
```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/your/cert.pem;
    ssl_certificate_key /path/to/your/key.pem;
    
    location / {
        proxy_pass http://127.0.0.1:5004;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 6. 配置防火墙
```bash
# 开放必要端口
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow 5004  # 如果直接访问后端
```

## 安全建议

1. **API密钥管理**：将API密钥存储在环境变量中，而不是配置文件中
2. **CORS配置**：在生产环境中限制允许的源
3. **HTTPS**：强制使用HTTPS
4. **速率限制**：添加API调用频率限制
5. **日志监控**：配置日志记录和监控

## 监控和维护

1. **日志查看**：
   ```bash
   tail -f /var/log/nginx/access.log
   tail -f /var/log/nginx/error.log
   ```

2. **服务重启**：
   ```bash
   sudo systemctl restart nginx
   # 重启Gunicorn进程
   ```

3. **备份配置**：
   ```bash
   cp backend/config.json backup/
   cp backend/.env backup/
   ```

## 故障排除

1. **端口被占用**：检查端口5004是否被其他服务占用
2. **CORS错误**：检查前端域名是否在ALLOWED_ORIGINS中
3. **文件上传失败**：检查uploads目录权限
4. **API调用失败**：检查Dify服务是否可访问

## 性能优化

1. **使用多进程**：Gunicorn的-w参数控制worker数量
2. **静态文件缓存**：配置Nginx缓存静态文件
3. **数据库优化**：如果使用数据库，配置连接池
4. **CDN**：使用CDN加速静态资源 