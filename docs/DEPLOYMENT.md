# 部署指南

本文档详细介绍了婴幼儿营养RAG系统的部署方法，包括开发环境、测试环境和生产环境的部署配置。

## 系统要求

### 最低配置
- **CPU**: 2核心
- **内存**: 4GB RAM
- **存储**: 10GB 可用空间
- **操作系统**: Windows 10/11, Ubuntu 18.04+, macOS 10.15+
- **Python**: 3.8+

### 推荐配置
- **CPU**: 4核心以上
- **内存**: 8GB RAM以上
- **存储**: 20GB+ SSD
- **GPU**: 可选，用于加速AI模型推理

## 环境准备

### 1. Python环境

```bash
# 检查Python版本
python --version

# 如果版本低于3.8，请升级Python
# Windows: 从官网下载安装包
# Ubuntu: sudo apt update && sudo apt install python3.8
# macOS: brew install python@3.8
```

### 2. 虚拟环境

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate

# 升级pip
pip install --upgrade pip
```

### 3. 系统依赖

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install -y build-essential python3-dev
```

**CentOS/RHEL:**
```bash
sudo yum groupinstall "Development Tools"
sudo yum install python3-devel
```

**macOS:**
```bash
# 安装Xcode命令行工具
xcode-select --install
```

## 开发环境部署

### 1. 克隆项目

```bash
git clone <repository-url>
cd baby-nutrition-rag
```

### 2. 安装依赖

```bash
# 安装Python依赖
pip install -r requirements.txt

# 如果遇到安装问题，可以尝试分步安装
pip install fastapi uvicorn pydantic
pip install sentence-transformers
pip install faiss-cpu
pip install -r requirements.txt
```

### 3. 配置文件

```bash
# 复制配置模板
cp config.example.yaml config.yaml

# 编辑配置文件
nano config.yaml  # 或使用其他编辑器
```

**关键配置项：**
```yaml
# 开发环境配置
app:
  environment: "development"
  debug: true
  log_level: "DEBUG"

server:
  host: "127.0.0.1"
  port: 8000
  reload: true

# AI服务配置（开发环境可使用本地模型）
ai_providers:
  embedding:
    provider: "sentence_transformers"
    model: "all-MiniLM-L6-v2"
  llm:
    provider: "openai"  # 需要配置API密钥
    api_key: "your-api-key-here"
```

### 4. 初始化数据

```bash
# 创建数据目录
mkdir -p data/knowledge data/foods data/vector_index

# 系统会自动使用示例数据
# 或者添加自定义数据到相应目录
```

### 5. 启动开发服务器

```bash
# 使用启动脚本
python run.py --reload

# 或直接使用uvicorn
uvicorn src.presentation.main:create_app --factory --reload --host 127.0.0.1 --port 8000
```

### 6. 验证部署

```bash
# 健康检查
curl http://localhost:8000/health

# 访问API文档
# 浏览器打开: http://localhost:8000/docs
```

## 测试环境部署

### 1. 环境配置

```yaml
# config.yaml - 测试环境
app:
  environment: "testing"
  debug: false
  log_level: "INFO"

server:
  host: "0.0.0.0"
  port: 8000
  reload: false
  workers: 2

# 使用测试数据库和缓存
storage:
  vector_store:
    index_path: "./data/test_vector_index"

cache:
  embedding_cache:
    enabled: true
    max_size: 500
```

### 2. 运行测试

```bash
# 安装测试依赖
pip install pytest pytest-asyncio pytest-cov

# 运行单元测试
pytest tests/ -v

# 运行集成测试
pytest tests/integration/ -v

# 生成覆盖率报告
pytest --cov=src --cov-report=html
```

### 3. 性能测试

```bash
# 安装性能测试工具
pip install locust

# 运行性能测试
locust -f tests/performance/locustfile.py --host=http://localhost:8000
```

## 生产环境部署

### 方式一：传统部署

#### 1. 服务器准备

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装必要软件
sudo apt install -y nginx supervisor python3-pip python3-venv git

# 创建应用用户
sudo useradd -m -s /bin/bash ragapp
sudo su - ragapp
```

#### 2. 应用部署

```bash
# 克隆代码
git clone <repository-url> /home/ragapp/baby-nutrition-rag
cd /home/ragapp/baby-nutrition-rag

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置生产环境
cp config.example.yaml config.yaml
# 编辑配置文件，设置生产环境参数
```

#### 3. 生产配置

```yaml
# config.yaml - 生产环境
app:
  environment: "production"
  debug: false
  log_level: "WARNING"

server:
  host: "127.0.0.1"
  port: 8000
  reload: false
  workers: 4

# 安全配置
security:
  cors:
    allow_origins: ["https://yourdomain.com"]
  rate_limiting:
    enabled: true
    requests_per_minute: 60

# 日志配置
production:
  logging:
    level: "WARNING"
    file_path: "/var/log/ragapp/app.log"
    max_file_size_mb: 100
    backup_count: 5
```

#### 4. Supervisor配置

```ini
# /etc/supervisor/conf.d/ragapp.conf
[program:ragapp]
command=/home/ragapp/baby-nutrition-rag/venv/bin/python run.py --workers 4
directory=/home/ragapp/baby-nutrition-rag
user=ragapp
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/ragapp/supervisor.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
environment=PATH="/home/ragapp/baby-nutrition-rag/venv/bin"
```

```bash
# 启动服务
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start ragapp
```

#### 5. Nginx配置

```nginx
# /etc/nginx/sites-available/ragapp
server {
    listen 80;
    server_name yourdomain.com;
    
    # 重定向到HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    # SSL配置
    ssl_certificate /path/to/ssl/cert.pem;
    ssl_certificate_key /path/to/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # 安全头
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    # 代理配置
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时配置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # 静态文件缓存
    location /static/ {
        alias /home/ragapp/baby-nutrition-rag/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # 健康检查
    location /health {
        access_log off;
        proxy_pass http://127.0.0.1:8000/health;
    }
}
```

```bash
# 启用站点
sudo ln -s /etc/nginx/sites-available/ragapp /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 方式二：Docker部署

#### 1. Dockerfile

```dockerfile
# Dockerfile
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建非root用户
RUN useradd -m -u 1000 ragapp && chown -R ragapp:ragapp /app
USER ragapp

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["python", "run.py", "--workers", "4"]
```

#### 2. Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  ragapp:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./config.yaml:/app/config.yaml
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - ragapp
    restart: unless-stopped

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  redis_data:
```

#### 3. 部署命令

```bash
# 构建和启动
docker-compose up -d --build

# 查看日志
docker-compose logs -f ragapp

# 扩展服务
docker-compose up -d --scale ragapp=3

# 更新服务
docker-compose pull
docker-compose up -d
```

### 方式三：Kubernetes部署

#### 1. 部署配置

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ragapp
  labels:
    app: ragapp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ragapp
  template:
    metadata:
      labels:
        app: ragapp
    spec:
      containers:
      - name: ragapp
        image: ragapp:latest
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          value: "production"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        volumeMounts:
        - name: config
          mountPath: /app/config.yaml
          subPath: config.yaml
        - name: data
          mountPath: /app/data
      volumes:
      - name: config
        configMap:
          name: ragapp-config
      - name: data
        persistentVolumeClaim:
          claimName: ragapp-data
```

```yaml
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: ragapp-service
spec:
  selector:
    app: ragapp
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

#### 2. 部署命令

```bash
# 创建命名空间
kubectl create namespace ragapp

# 创建配置
kubectl create configmap ragapp-config --from-file=config.yaml -n ragapp

# 部署应用
kubectl apply -f k8s/ -n ragapp

# 查看状态
kubectl get pods -n ragapp
kubectl get services -n ragapp
```

## 监控和日志

### 1. 应用监控

```yaml
# 启用监控
monitoring:
  performance:
    enabled: true
    slow_query_threshold_ms: 1000
  health_check:
    enabled: true
    interval_seconds: 60
  metrics:
    enabled: true
    export_port: 9090
```

### 2. 日志配置

```python
# 日志轮转配置
from loguru import logger

logger.add(
    "/var/log/ragapp/app.log",
    rotation="10 MB",
    retention="7 days",
    compression="zip",
    level="INFO"
)
```

### 3. Prometheus监控

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'ragapp'
    static_configs:
      - targets: ['localhost:9090']
```

## 备份和恢复

### 1. 数据备份

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backup/ragapp/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

# 备份数据文件
cp -r /home/ragapp/baby-nutrition-rag/data $BACKUP_DIR/

# 备份配置文件
cp /home/ragapp/baby-nutrition-rag/config.yaml $BACKUP_DIR/

# 压缩备份
tar -czf $BACKUP_DIR.tar.gz -C /backup/ragapp $(basename $BACKUP_DIR)
rm -rf $BACKUP_DIR

echo "备份完成: $BACKUP_DIR.tar.gz"
```

### 2. 自动备份

```bash
# 添加到crontab
# 每天凌晨2点备份
0 2 * * * /home/ragapp/scripts/backup.sh
```

### 3. 恢复数据

```bash
#!/bin/bash
# restore.sh

BACKUP_FILE=$1
if [ -z "$BACKUP_FILE" ]; then
    echo "使用方法: $0 <backup_file.tar.gz>"
    exit 1
fi

# 停止服务
sudo supervisorctl stop ragapp

# 恢复数据
tar -xzf $BACKUP_FILE -C /tmp/
cp -r /tmp/*/data /home/ragapp/baby-nutrition-rag/
cp /tmp/*/config.yaml /home/ragapp/baby-nutrition-rag/

# 重启服务
sudo supervisorctl start ragapp

echo "恢复完成"
```

## 性能优化

### 1. 系统优化

```bash
# 增加文件描述符限制
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf

# 优化内核参数
echo "net.core.somaxconn = 65535" >> /etc/sysctl.conf
echo "net.ipv4.tcp_max_syn_backlog = 65535" >> /etc/sysctl.conf
sysctl -p
```

### 2. 应用优化

```yaml
# 缓存优化
cache:
  embedding_cache:
    enabled: true
    max_size: 10000
    ttl_seconds: 3600
  query_cache:
    enabled: true
    max_size: 5000
    ttl_seconds: 1800

# AI服务优化
ai_providers:
  embedding:
    batch_size: 64  # 增加批处理大小
  llm:
    max_tokens: 500  # 限制响应长度
    temperature: 0.3  # 降低随机性
```

### 3. 数据库优化

```python
# 向量索引优化
faiss_config = {
    "index_type": "IVF",  # 使用倒排索引
    "nlist": 100,        # 聚类数量
    "nprobe": 10         # 搜索聚类数
}
```

## 安全配置

### 1. 防火墙配置

```bash
# UFW配置
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw deny 8000/tcp  # 只允许内部访问
```

### 2. SSL证书

```bash
# Let's Encrypt证书
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com

# 自动续期
echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -
```

### 3. API安全

```yaml
# 启用API密钥
security:
  api_key:
    enabled: true
    key: "your-secure-api-key"
  rate_limiting:
    enabled: true
    requests_per_minute: 60
```

## 故障排除

### 常见问题

1. **服务启动失败**
   ```bash
   # 检查日志
   sudo supervisorctl tail ragapp stderr
   
   # 检查端口占用
   sudo netstat -tlnp | grep 8000
   ```

2. **内存不足**
   ```bash
   # 检查内存使用
   free -h
   
   # 调整worker数量
   # config.yaml中减少workers数量
   ```

3. **AI服务错误**
   ```bash
   # 检查API密钥
   # 验证网络连接
   curl -I https://api.openai.com
   ```

### 日志分析

```bash
# 查看错误日志
tail -f /var/log/ragapp/app.log | grep ERROR

# 分析访问模式
awk '{print $1}' /var/log/nginx/access.log | sort | uniq -c | sort -nr
```

## 更新和维护

### 1. 应用更新

```bash
#!/bin/bash
# update.sh

# 备份当前版本
./backup.sh

# 拉取最新代码
git pull origin main

# 更新依赖
source venv/bin/activate
pip install -r requirements.txt

# 重启服务
sudo supervisorctl restart ragapp

# 验证部署
curl -f http://localhost:8000/health
```

### 2. 定期维护

```bash
# 清理日志
find /var/log/ragapp -name "*.log" -mtime +7 -delete

# 清理缓存
curl -X POST http://localhost:8000/system/cache/reset

# 重建索引
curl -X POST http://localhost:8000/system/index/build
```

### 3. 监控检查

```bash
# 健康检查脚本
#!/bin/bash
HEALTH_URL="http://localhost:8000/health"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL)

if [ $RESPONSE -eq 200 ]; then
    echo "服务正常"
else
    echo "服务异常，状态码: $RESPONSE"
    # 发送告警
fi
```

## 扩展部署

### 负载均衡

```nginx
# nginx负载均衡配置
upstream ragapp_backend {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
}

server {
    location / {
        proxy_pass http://ragapp_backend;
    }
}
```

### 数据库集群

```yaml
# 多节点向量数据库配置
vector_store:
  type: "distributed_faiss"
  nodes:
    - host: "node1.example.com"
      port: 9000
    - host: "node2.example.com"
      port: 9000
```

这份部署指南涵盖了从开发到生产的完整部署流程，请根据实际需求选择合适的部署方式。