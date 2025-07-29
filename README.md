# Giggle Academy 多语言翻译系统

## 项目简介

Giggle Academy 是一个儿童教育平台，本系统为平台提供多语言翻译功能，支持语音识别、文本翻译和紧凑编码打包，让全世界的儿童都能享受优质教育内容。

## 功能特性

- 🎤 **语音识别**: 使用 Whisper 进行音频转文本
- 🌍 **多语言翻译**: 支持英语、简体中文、繁体中文、日语
- 📦 **紧凑编码**: 高效的文件格式设计
- 🔄 **任务管理**: 完整的翻译任务生命周期管理
- 🚀 **分布式架构**: 支持高并发和故障转移

## 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web API       │    │   Task Queue    │    │   Translation   │
│   (Flask)       │◄──►│   (Redis)       │◄──►│   Workers       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   File Storage  │    │   Whisper       │    │   LLM API       │
│   (Local/Cloud) │    │   (GPU/CPU)     │    │   (OpenAI)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 环境要求

- Python 3.8+
- Redis 6.0+
- CUDA (可选，用于GPU加速)
- FFmpeg (音频处理)

## 安装步骤

### 1. 克隆项目
```bash
git clone <repository-url>
cd giggle-translation-system
```

### 2. 创建虚拟环境
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

### 4. 安装FFmpeg
- **Windows**: 下载并添加到PATH
- **Linux**: `sudo apt-get install ffmpeg`
- **Mac**: `brew install ffmpeg`

### 5. 配置环境变量
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填入必要的配置
OPENAI_API_KEY=your_openai_api_key
REDIS_URL=redis://localhost:6379
```

### 6. 启动Redis
```bash
# Windows (需要先安装Redis)
redis-server

# Linux/Mac
sudo systemctl start redis
```

## 启动说明

### 1. 启动API服务
```bash
python app.py
```
服务将在 http://localhost:5000 启动

### 2. 启动Worker进程
```bash
python worker.py
```

### 3. 启动监控面板（可选）
```bash
python monitor.py
```

## API文档

### 创建翻译任务
```bash
POST /api/v1/tasks
Content-Type: application/json

{
  "audio_file": "path/to/audio.mp3",
  "text_file": "path/to/text.json",
  "target_languages": ["zh-CN", "zh-TW", "ja"]
}
```

### 查询任务状态
```bash
GET /api/v1/tasks/{task_id}
```

### 获取翻译结果
```bash
GET /api/v1/tasks/{task_id}/result
```

## 测试说明

### 1. 单元测试
```bash
python -m pytest tests/ -v
```

### 2. 集成测试
```bash
python tests/integration_test.py
```

### 3. 性能测试
```bash
python tests/performance_test.py
```

### 4. 手动测试
```bash
# 使用提供的测试数据
python tests/manual_test.py
```

## 项目结构

```
giggle-translation-system/
├── app.py                 # Flask API 主程序
├── worker.py              # 后台任务处理
├── monitor.py             # 系统监控
├── requirements.txt       # Python 依赖
├── .env.example          # 环境变量模板
├── README.md             # 项目文档
├── docs/                 # 设计文档
│   ├── architecture.md   # 架构设计
│   ├── api.md           # API 文档
│   └── deployment.md    # 部署指南
├── src/                  # 源代码
│   ├── __init__.py
│   ├── api/             # API 模块
│   ├── core/            # 核心功能
│   ├── services/        # 业务服务
│   └── utils/           # 工具函数
├── tests/               # 测试文件
│   ├── __init__.py
│   ├── test_api.py
│   ├── test_services.py
│   └── test_data/       # 测试数据
└── data/                # 数据文件
    ├── audio/           # 音频文件
    ├── text/            # 文本文件
    └── output/          # 输出文件
```

## 部署指南

### Docker 部署
```bash
docker-compose up -d
```

### Kubernetes 部署
```bash
kubectl apply -f k8s/
```