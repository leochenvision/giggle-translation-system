"""
紧凑编码打包服务
"""

import json
import gzip
import base64
import os
from datetime import datetime
from typing import Dict, Any, Optional
from src.core.config import Config
from src.core.logger import get_logger

logger = get_logger("packaging_service")

class PackagingService:
    """紧凑编码打包服务"""
    
    def __init__(self):
        """初始化打包服务"""
        self.output_dir = Config.OUTPUT_FOLDER
        os.makedirs(self.output_dir, exist_ok=True)
    
    def create_package(self, task_id: str, original_text: str, translations: Dict[str, str], 
                      audio_transcription: Dict[str, Any]) -> str:
        """创建紧凑编码包"""
        try:
            # 构建包数据结构
            package_data = {
                'metadata': {
                    'task_id': task_id,
                    'created_at': datetime.now().isoformat(),
                    'version': '1.0',
                    'format': 'giggle-compact-v1'
                },
                'content': {
                    'original': {
                        'text': original_text,
                        'source': 'TEXT'
                    },
                    'audio': {
                        'text': audio_transcription.get('text', ''),
                        'source': 'AUDIO',
                        'confidence': audio_transcription.get('confidence', 0),
                        'language': audio_transcription.get('language', 'unknown')
                    },
                    'translations': {}
                }
            }
            
            # 添加翻译
            for lang_code, translation in translations.items():
                package_data['content']['translations'][lang_code] = {
                    'text': translation,
                    'source': 'TEXT'  # 基于原始文本翻译
                }
            
            # 创建紧凑编码
            compact_data = self._create_compact_encoding(package_data)
            
            # 保存文件
            filename = f"giggle_package_{task_id}.gcp"
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, 'wb') as f:
                f.write(compact_data)
            
            logger.info(f"Package created: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error creating package for task {task_id}: {str(e)}")
            return ""
    
    def _create_compact_encoding(self, data: Dict[str, Any]) -> bytes:
        """创建紧凑编码"""
        try:
            # 1. 转换为JSON
            json_str = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
            
            # 2. 压缩
            compressed = gzip.compress(json_str.encode('utf-8'))
            
            # 3. Base64编码
            encoded = base64.b64encode(compressed)
            
            # 4. 添加文件头
            header = b'GIGGLE_PACKAGE_v1.0\n'
            return header + encoded
            
        except Exception as e:
            logger.error(f"Error creating compact encoding: {str(e)}")
            raise
    
    def read_package(self, filepath: str) -> Optional[Dict[str, Any]]:
        """读取紧凑编码包"""
        try:
            with open(filepath, 'rb') as f:
                data = f.read()
            
            # 检查文件头
            if not data.startswith(b'GIGGLE_PACKAGE_v1.0\n'):
                logger.error("Invalid package format")
                return None
            
            # 移除文件头
            encoded_data = data[len(b'GIGGLE_PACKAGE_v1.0\n'):]
            
            # 解码
            compressed = base64.b64decode(encoded_data)
            json_str = gzip.decompress(compressed).decode('utf-8')
            
            # 解析JSON
            package_data = json.loads(json_str)
            
            return package_data
            
        except Exception as e:
            logger.error(f"Error reading package {filepath}: {str(e)}")
            return None
    
    def query_package(self, filepath: str, language: str, text_id: str = None) -> Optional[Dict[str, Any]]:
        """查询包内容"""
        try:
            package_data = self.read_package(filepath)
            if not package_data:
                return None
            
            content = package_data.get('content', {})
            
            # 查询指定语言
            if language in content.get('translations', {}):
                translation = content['translations'][language]
                return {
                    'language': language,
                    'text': translation['text'],
                    'source': translation['source'],
                    'text_id': text_id or 'main'
                }
            
            # 查询原始文本
            if language == 'original':
                original = content.get('original', {})
                return {
                    'language': 'original',
                    'text': original.get('text', ''),
                    'source': original.get('source', 'TEXT'),
                    'text_id': text_id or 'main'
                }
            
            # 查询音频转录
            if language == 'audio':
                audio = content.get('audio', {})
                return {
                    'language': 'audio',
                    'text': audio.get('text', ''),
                    'source': audio.get('source', 'AUDIO'),
                    'confidence': audio.get('confidence', 0),
                    'text_id': text_id or 'main'
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error querying package {filepath}: {str(e)}")
            return None
    
    def get_package_info(self, filepath: str) -> Optional[Dict[str, Any]]:
        """获取包信息"""
        try:
            package_data = self.read_package(filepath)
            if not package_data:
                return None
            
            metadata = package_data.get('metadata', {})
            content = package_data.get('content', {})
            
            # 统计信息
            translations = content.get('translations', {})
            
            info = {
                'task_id': metadata.get('task_id'),
                'created_at': metadata.get('created_at'),
                'version': metadata.get('version'),
                'format': metadata.get('format'),
                'available_languages': list(translations.keys()),
                'translation_count': len(translations),
                'has_audio': 'audio' in content,
                'has_original': 'original' in content
            }
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting package info {filepath}: {str(e)}")
            return None
    
    def validate_package(self, filepath: str) -> bool:
        """验证包完整性"""
        try:
            package_data = self.read_package(filepath)
            if not package_data:
                return False
            
            # 检查必需字段
            required_fields = ['metadata', 'content']
            for field in required_fields:
                if field not in package_data:
                    logger.error(f"Missing required field: {field}")
                    return False
            
            # 检查内容
            content = package_data.get('content', {})
            if not content:
                logger.error("Empty content")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating package {filepath}: {str(e)}")
            return False
    
    def extract_texts(self, filepath: str) -> Dict[str, str]:
        """提取所有文本"""
        try:
            package_data = self.read_package(filepath)
            if not package_data:
                return {}
            
            content = package_data.get('content', {})
            texts = {}
            
            # 原始文本
            if 'original' in content:
                texts['original'] = content['original'].get('text', '')
            
            # 音频转录
            if 'audio' in content:
                texts['audio'] = content['audio'].get('text', '')
            
            # 翻译
            translations = content.get('translations', {})
            for lang, trans in translations.items():
                texts[lang] = trans.get('text', '')
            
            return texts
            
        except Exception as e:
            logger.error(f"Error extracting texts from {filepath}: {str(e)}")
            return {} 