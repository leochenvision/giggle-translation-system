# Giggle Academy 多语言翻译系统 - 部署指南

## 概述

本文档提供了Giggle Academy多语言翻译系统的详细部署指南，包括开发环境、生产环境和容器化部署。

## 环境要求

### 系统要求
- **操作系统**: Linux (Ubuntu 18.04+), macOS, Windows 10+
- **Python**: 3.8+
- **内存**: 最少4GB，推荐8GB+
- **存储**: 最少10GB可用空间
- **网络**: 稳定的互联网连接

### 软件依赖
- **Redis**: 6.0+
- **FFmpeg**: 音频处理
- **CUDA**: 可选，用于GPU加速

## 开发环境部署

### 1. 克隆项目
```bash
git clone <repository-url>
cd giggle-translation-system
```

### 2. 创建虚拟环境
```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate
```

### 3. 安装依赖
```bash
# 升级pip
pip install --upgrade pip

# 安装依赖
pip install -r requirements.txt
```

### 4. 安装FFmpeg

#### Windows
1. 下载FFmpeg: https://ffmpeg.org/download.html
2. 解压到 `C:\ffmpeg`
3. 添加到PATH环境变量

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install ffmpeg
```

#### macOS
```bash
brew install ffmpeg
```

### 5. 安装Redis

#### Windows
1. 下载Redis: https://redis.io/download
2. 解压并运行 `redis-server.exe`

#### Linux
```bash
sudo apt install redis-server
sudo systemctl start redis
sudo systemctl enable redis
```

#### macOS
```bash
brew install redis
brew services start redis
```

### 6. 配置环境变量
```bash
# 复制环境变量模板
cp env.example .env

# 编辑.env文件
nano .env
```

配置示例:
```env
# API Configuration
FLASK_ENV=development
FLASK_DEBUG=true
SECRET_KEY=your-secret-key-here

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key-here

# Whisper Configuration
WHISPER_MODEL=base
WHISPER_DEVICE=cpu

# File Storage
UPLOAD_FOLDER=./data/uploads
OUTPUT_FOLDER=./data/output
```

### 7. 创建数据目录
```bash
mkdir -p data/uploads data/output data/audio data/text
```

### 8. 启动服务

#### 启动API服务
```bash
python app.py
```

#### 启动Worker进程（新终端）
```bash
python worker.py
```

#### 验证服务
```bash
curl http://localhost:5000/health
```

## Docker部署

### 1. 创建Dockerfile
```dockerfile
FROM python:3.9-slim

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建数据目录
RUN mkdir -p data/uploads data/output

# 暴露端口
EXPOSE 5000

# 启动命令
CMD ["python", "app.py"]
```

### 2. 创建docker-compose.yml
```yaml
version: '3.8'

services:
  redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

  api:
    build: .
    ports:
      - "5000:5000"
    environment:
      - REDIS_URL=redis://redis:6379/0
      - FLASK_ENV=production
    volumes:
      - ./data:/app/data
    depends_on:
      - redis
    restart: unless-stopped

  worker:
    build: .
    command: python worker.py
    environment:
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - ./data:/app/data
    depends_on:
      - redis
    restart: unless-stopped

volumes:
  redis_data:
```

### 3. 构建和运行
```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

## Kubernetes部署

### 1. 创建命名空间
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: giggle-translation
```

### 2. 创建ConfigMap
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: giggle-config
  namespace: giggle-translation
data:
  FLASK_ENV: "production"
  WHISPER_MODEL: "base"
  WHISPER_DEVICE: "cpu"
  UPLOAD_FOLDER: "/app/data/uploads"
  OUTPUT_FOLDER: "/app/data/output"
```

### 3. 创建Secret
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: giggle-secrets
  namespace: giggle-translation
type: Opaque
data:
  OPENAI_API_KEY: <base64-encoded-api-key>
  SECRET_KEY: <base64-encoded-secret>
```

### 4. 创建Redis部署
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: giggle-translation
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:6-alpine
        ports:
        - containerPort: 6379
        volumeMounts:
        - name: redis-storage
          mountPath: /data
      volumes:
      - name: redis-storage
        persistentVolumeClaim:
          claimName: redis-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: redis
  namespace: giggle-translation
spec:
  selector:
    app: redis
  ports:
  - port: 6379
    targetPort: 6379
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: redis-pvc
  namespace: giggle-translation
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
```

### 5. 创建API部署
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: giggle-api
  namespace: giggle-translation
spec:
  replicas: 3
  selector:
    matchLabels:
      app: giggle-api
  template:
    metadata:
      labels:
        app: giggle-api
    spec:
      containers:
      - name: api
        image: giggle-translation:latest
        ports:
        - containerPort: 5000
        env:
        - name: REDIS_URL
          value: "redis://redis:6379/0"
        - name: FLASK_ENV
          valueFrom:
            configMapKeyRef:
              name: giggle-config
              key: FLASK_ENV
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: giggle-secrets
              key: OPENAI_API_KEY
        volumeMounts:
        - name: data-storage
          mountPath: /app/data
      volumes:
      - name: data-storage
        persistentVolumeClaim:
          claimName: data-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: giggle-api
  namespace: giggle-translation
spec:
  selector:
    app: giggle-api
  ports:
  - port: 80
    targetPort: 5000
  type: LoadBalancer
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: data-pvc
  namespace: giggle-translation
spec:
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 10Gi
```

### 6. 创建Worker部署
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: giggle-worker
  namespace: giggle-translation
spec:
  replicas: 2
  selector:
    matchLabels:
      app: giggle-worker
  template:
    metadata:
      labels:
        app: giggle-worker
    spec:
      containers:
      - name: worker
        image: giggle-translation:latest
        command: ["python", "worker.py"]
        env:
        - name: REDIS_URL
          value: "redis://redis:6379/0"
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: giggle-secrets
              key: OPENAI_API_KEY
        volumeMounts:
        - name: data-storage
          mountPath: /app/data
      volumes:
      - name: data-storage
        persistentVolumeClaim:
          claimName: data-pvc
```

### 7. 部署到Kubernetes
```bash
# 应用所有配置
kubectl apply -f k8s/

# 检查部署状态
kubectl get pods -n giggle-translation

# 查看服务
kubectl get svc -n giggle-translation

# 查看日志
kubectl logs -f deployment/giggle-api -n giggle-translation
```

## 生产环境配置

### 1. 安全配置
```bash
# 生成强密钥
openssl rand -hex 32

# 配置防火墙
sudo ufw allow 5000
sudo ufw allow 6379
```

### 2. 性能优化
```bash
# 调整Redis配置
echo "maxmemory 1gb" >> /etc/redis/redis.conf
echo "maxmemory-policy allkeys-lru" >> /etc/redis/redis.conf

# 调整系统参数
echo "vm.max_map_count=262144" >> /etc/sysctl.conf
sysctl -p
```

### 3. 监控配置
```bash
# 安装Prometheus
wget https://github.com/prometheus/prometheus/releases/download/v2.30.0/prometheus-2.30.0.linux-amd64.tar.gz
tar xvf prometheus-*.tar.gz
cd prometheus-*

# 配置Prometheus
cat > prometheus.yml << EOF
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'giggle-api'
    static_configs:
      - targets: ['localhost:5000']
EOF

# 启动Prometheus
./prometheus --config.file=prometheus.yml
```

## 故障排除

### 常见问题

#### 1. Redis连接失败
```bash
# 检查Redis状态
redis-cli ping

# 重启Redis
sudo systemctl restart redis
```

#### 2. Whisper模型下载失败
```bash
# 手动下载模型
python -c "import whisper; whisper.load_model('base')"
```

#### 3. 内存不足
```bash
# 检查内存使用
free -h

# 调整Worker数量
export MAX_WORKERS=2
```

#### 4. 文件权限问题
```bash
# 修复权限
sudo chown -R $USER:$USER data/
chmod -R 755 data/
```

### 日志查看
```bash
# 查看应用日志
tail -f logs/app.log

# 查看Worker日志
tail -f logs/worker.log

# 查看Redis日志
sudo journalctl -u redis -f
```

## 备份和恢复

### 1. 数据备份
```bash
# 备份Redis数据
redis-cli BGSAVE

# 备份文件数据
tar -czf backup_$(date +%Y%m%d).tar.gz data/
```

### 2. 数据恢复
```bash
# 恢复Redis数据
redis-cli FLUSHALL
redis-cli RESTORE key 0 value

# 恢复文件数据
tar -xzf backup_20240101.tar.gz
```

## 更新和升级

### 1. 代码更新
```bash
# 拉取最新代码
git pull origin main

# 更新依赖
pip install -r requirements.txt

# 重启服务
sudo systemctl restart giggle-api
sudo systemctl restart giggle-worker
```

### 2. 数据库迁移
```bash
# 备份当前数据
./backup.sh

# 执行迁移
python migrate.py

# 验证数据
python verify_data.py
```

## 总结

本部署指南涵盖了从开发环境到生产环境的完整部署流程。根据实际需求选择合适的部署方式，并确保遵循安全最佳实践。 