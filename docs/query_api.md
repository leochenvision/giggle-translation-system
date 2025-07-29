# 查询接口API文档

## 概述

新的查询接口允许您通过语言、文本编号和来源直接查询打包文件中的文本内容，无需指定具体的任务ID。

## 接口列表

### 1. 单个查询接口

**接口地址:** `GET /api/v1/query`

**功能:** 查询第一个匹配的文本内容

**参数:**
- `language` (必需): 语言代码
- `source` (可选): 来源类型 (TEXT, AUDIO)
- `text_id` (可选): 文本编号，默认为 'main'

**响应示例:**
```json
{
  "task_id": "bf8ee615-737c-4899-9d88-f2bb88146368",
  "language": "zh-CN",
  "text_id": "main",
  "found": true,
  "text": "蒂莉，一只小狐狸，喜欢她明亮的红色气球。",
  "source": "TEXT",
  "filename": "giggle_package_bf8ee615-737c-4899-9d88-f2bb88146368.gcp"
}
```

### 2. 批量查询接口

**接口地址:** `GET /api/v1/query/all`

**功能:** 查询所有匹配的文本内容

**参数:**
- `language` (必需): 语言代码
- `source` (可选): 来源类型 (TEXT, AUDIO)

**响应示例:**
```json
{
  "language": "zh-CN",
  "source": "TEXT",
  "count": 2,
  "results": [
    {
      "task_id": "bf8ee615-737c-4899-9d88-f2bb88146368",
      "language": "zh-CN",
      "text": "蒂莉，一只小狐狸，喜欢她明亮的红色气球。",
      "source": "TEXT",
      "filename": "giggle_package_bf8ee615-737c-4899-9d88-f2bb88146368.gcp"
    },
    {
      "task_id": "7946b3ec-37f5-402e-97a0-1f67a83f5e44",
      "language": "zh-CN",
      "text": "另一段中文翻译文本",
      "source": "TEXT",
      "filename": "giggle_package_7946b3ec-37f5-402e-97a0-1f67a83f5e44.gcp"
    }
  ]
}
```

## 支持的语言代码

### 特殊语言
- `original`: 原始文本
- `audio`: 音频转录

### 翻译语言
- `zh-CN`: 简体中文
- `zh-TW`: 繁体中文
- `ja`: 日语
- `ko`: 韩语
- `en`: 英语
- `fr`: 法语
- `de`: 德语
- `es`: 西班牙语
- `pt`: 葡萄牙语
- `ru`: 俄语

## 来源类型

- `TEXT`: 基于文本的翻译或原始文本
- `AUDIO`: 基于音频转录的内容

## 使用示例

### 查询原始文本
```bash
curl "http://localhost:5000/api/v1/query?language=original&source=TEXT"
```

### 查询音频转录
```bash
curl "http://localhost:5000/api/v1/query?language=audio&source=AUDIO"
```

### 查询中文翻译
```bash
curl "http://localhost:5000/api/v1/query?language=zh-CN&source=TEXT"
```

### 查询所有中文翻译
```bash
curl "http://localhost:5000/api/v1/query/all?language=zh-CN&source=TEXT"
```

### 查询日文翻译
```bash
curl "http://localhost:5000/api/v1/query?language=ja&source=TEXT"
```

## 错误响应

### 400 Bad Request
```json
{
  "error": "language is required"
}
```

### 404 Not Found
```json
{
  "error": "Content not found for language: fr-FR, text_id: main, source: any"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error"
}
```

## 特点

1. **无需任务ID**: 自动扫描所有打包文件
2. **精确查询**: 支持按语言和来源精确查询
3. **批量查询**: 支持查询所有匹配的内容
4. **详细信息**: 返回任务ID和文件名信息
5. **错误处理**: 完善的错误处理和响应

## 性能说明

- 接口会自动扫描 `data/output` 目录下的所有 `.gcp` 文件
- 查询按文件顺序进行，找到第一个匹配项即返回
- 批量查询会遍历所有文件并返回所有匹配项
- 建议在生产环境中考虑添加缓存机制以提高性能 