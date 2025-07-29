# Giggle Academy 多语言翻译系统 - API文档

## 概述

本文档描述了Giggle Academy多语言翻译系统的RESTful API接口。所有API都遵循REST设计原则，使用JSON格式进行数据交换。

## 基础信息

- **Base URL**: `http://localhost:5000`
- **API Version**: `v1`
- **Content-Type**: `application/json`
- **字符编码**: UTF-8

## 认证

目前API使用简单的API Key认证方式：

```
Authorization: Bearer <your-api-key>
```

## 通用响应格式

### 成功响应
```json
{
  "status": "success",
  "data": {
    // 响应数据
  },
  "message": "操作成功"
}
```

### 错误响应
```json
{
  "status": "error",
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述",
    "details": {}
  }
}
```

## API端点

### 1. 健康检查

#### GET /health

检查服务健康状态。

**响应示例:**
```json
{
  "status": "healthy",
  "service": "giggle-translation-system",
  "version": "1.0.0",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### 2. 获取支持的语言

#### GET /api/v1/languages

获取系统支持的所有语言列表。

**响应示例:**
```json
{
  "languages": [
    {
      "code": "en",
      "name": "English"
    },
    {
      "code": "zh-CN",
      "name": "简体中文"
    },
    {
      "code": "zh-TW",
      "name": "繁體中文"
    },
    {
      "code": "ja",
      "name": "日本語"
    }
  ],
  "default_targets": ["zh-CN", "zh-TW", "ja"]
}
```

### 3. 任务管理

#### POST /api/v1/tasks

创建新的翻译任务。

**请求参数:**
```json
{
  "audio_file": "path/to/audio.mp3",
  "text_file": "path/to/text.json",
  "target_languages": ["zh-CN", "zh-TW", "ja"]
}
```

**参数说明:**
- `audio_file` (必需): 音频文件路径
- `text_file` (必需): 文本文件路径
- `target_languages` (可选): 目标语言列表，默认为 `["zh-CN", "zh-TW", "ja"]`

**响应示例:**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "Task created successfully"
}
```

#### GET /api/v1/tasks/{task_id}

获取任务状态。

**路径参数:**
- `task_id`: 任务ID

**响应示例:**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "progress": 60,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:05:00Z",
  "target_languages": ["zh-CN", "zh-TW", "ja"],
  "error": null
}
```

#### GET /api/v1/tasks/{task_id}/result

获取任务结果。

**路径参数:**
- `task_id`: 任务ID

**响应示例:**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "translations": {
    "zh-CN": "你好世界，这是一个儿童故事。",
    "zh-TW": "你好世界，這是一個兒童故事。",
    "ja": "こんにちは世界、これは子供の物語です。"
  },
  "audio_transcription": {
    "text": "Hello world, this is a children's story.",
    "confidence": 0.95,
    "language": "en"
  },
  "text_validation": {
    "similarity": 0.92,
    "original_text": "Hello world, this is a children's story.",
    "stt_text": "Hello world this is a children's story",
    "confidence": 0.95
  },
  "packaged_file": "/data/output/giggle_package_550e8400-e29b-41d4-a716-446655440000.gcp",
  "created_at": "2024-01-01T00:10:00Z"
}
```

#### DELETE /api/v1/tasks/{task_id}

取消任务。

**路径参数:**
- `task_id`: 任务ID

**响应示例:**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "cancelled",
  "message": "Task cancelled successfully"
}
```

#### GET /api/v1/tasks

列出所有任务。

**查询参数:**
- `page` (可选): 页码，默认为1
- `per_page` (可选): 每页数量，默认为10
- `status` (可选): 任务状态过滤

**响应示例:**
```json
{
  "tasks": [
    {
      "task_id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "completed",
      "progress": 100,
      "created_at": "2024-01-01T00:00:00Z",
      "target_languages": ["zh-CN", "zh-TW"]
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 10,
  "pages": 1
}
```

## 任务状态

| 状态 | 描述 |
|------|------|
| `pending` | 等待处理 |
| `processing` | 处理中 |
| `completed` | 已完成 |
| `failed` | 处理失败 |
| `cancelled` | 已取消 |

## 错误代码

| 错误代码 | HTTP状态码 | 描述 |
|----------|------------|------|
| `INVALID_REQUEST` | 400 | 请求参数无效 |
| `MISSING_FIELD` | 400 | 缺少必需字段 |
| `UNSUPPORTED_LANGUAGE` | 400 | 不支持的语言 |
| `TASK_NOT_FOUND` | 404 | 任务不存在 |
| `RESULT_NOT_FOUND` | 404 | 结果不存在 |
| `INTERNAL_ERROR` | 500 | 内部服务器错误 |
| `SERVICE_UNAVAILABLE` | 503 | 服务不可用 |

## 文件格式

### 音频文件
- **支持格式**: MP3, WAV, M4A, FLAC, OGG
- **最大大小**: 100MB
- **采样率**: 建议16kHz或以上

### 文本文件
- **格式**: JSON
- **编码**: UTF-8
- **结构示例**:
```json
{
  "title": "故事标题",
  "text": "故事内容",
  "language": "en",
  "category": "children_story",
  "difficulty": "beginner"
}
```

## 紧凑编码包格式

### 文件扩展名
`.gcp` (Giggle Compact Package)

### 文件结构
```
GIGGLE_PACKAGE_v1.0\n
[Base64编码的压缩JSON数据]
```

### 包内容结构
```json
{
  "metadata": {
    "task_id": "任务ID",
    "created_at": "创建时间",
    "version": "版本号",
    "format": "giggle-compact-v1"
  },
  "content": {
    "original": {
      "text": "原始文本",
      "source": "TEXT"
    },
    "audio": {
      "text": "音频转录文本",
      "source": "AUDIO",
      "confidence": 0.95,
      "language": "en"
    },
    "translations": {
      "zh-CN": "简体中文翻译",
      "zh-TW": "繁体中文翻译",
      "ja": "日语翻译"
    }
  }
}
```

## 查询接口

### 查询包内容
```
语言 -> 文本编号 -> 文本来源(TEXT / AUDIO)
```

**查询示例:**
- `zh-CN` -> `main` -> `TEXT` (简体中文翻译)
- `original` -> `main` -> `TEXT` (原始文本)
- `audio` -> `main` -> `AUDIO` (音频转录)

## 速率限制

- **API请求**: 1000次/小时
- **文件上传**: 10MB/分钟
- **任务创建**: 100次/小时

## 最佳实践

### 1. 错误处理
```javascript
try {
  const response = await fetch('/api/v1/tasks', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer your-api-key'
    },
    body: JSON.stringify(taskData)
  });
  
  if (!response.ok) {
    const error = await response.json();
    console.error('Error:', error.error.message);
  }
} catch (error) {
  console.error('Network error:', error);
}
```

### 2. 轮询任务状态
```javascript
async function pollTaskStatus(taskId) {
  const maxAttempts = 60; // 最多轮询60次
  let attempts = 0;
  
  while (attempts < maxAttempts) {
    const response = await fetch(`/api/v1/tasks/${taskId}`);
    const task = await response.json();
    
    if (task.status === 'completed') {
      return task;
    } else if (task.status === 'failed') {
      throw new Error('Task failed');
    }
    
    await new Promise(resolve => setTimeout(resolve, 5000)); // 等待5秒
    attempts++;
  }
  
  throw new Error('Task timeout');
}
```

### 3. 批量处理
```javascript
async function batchTranslate(texts, targetLanguages) {
  const tasks = [];
  
  for (const text of texts) {
    const task = await createTask({
      text_file: text,
      target_languages: targetLanguages
    });
    tasks.push(task);
  }
  
  // 等待所有任务完成
  const results = await Promise.all(
    tasks.map(task => pollTaskStatus(task.task_id))
  );
  
  return results;
}
```

## 更新日志

### v1.0.0 (2024-01-01)
- 初始版本发布
- 支持基本的任务管理功能
- 支持Whisper语音识别
- 支持OpenAI翻译
- 支持紧凑编码打包 