"""
配置管理模块
"""

import os
from typing import List

class Config:
    """应用配置类"""
    
    # 基础配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    DEBUG = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    
    # Redis配置
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_DB = int(os.getenv('REDIS_DB', 0))
    
    # OpenAI配置
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
    
    # Whisper配置
    WHISPER_MODEL = os.getenv('WHISPER_MODEL', 'base')
    WHISPER_DEVICE = os.getenv('WHISPER_DEVICE', 'cpu')
    
    # 文件存储配置
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', './data/uploads')
    OUTPUT_FOLDER = os.getenv('OUTPUT_FOLDER', './data/output')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16777216))  # 16MB
    
    # 日志配置
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = os.getenv('LOG_FORMAT', 'json')
    
    # 任务配置
    MAX_WORKERS = int(os.getenv('MAX_WORKERS', 4))
    TASK_TIMEOUT = int(os.getenv('TASK_TIMEOUT', 300))  # 5分钟
    
    # 监控配置
    PROMETHEUS_PORT = int(os.getenv('PROMETHEUS_PORT', 9090))
    ENABLE_METRICS = os.getenv('ENABLE_METRICS', 'true').lower() == 'true'
    
    # 支持的语言
    SUPPORTED_LANGUAGES = {
        'en': 'English',
        'zh-CN': '简体中文',
        'zh-TW': '繁體中文',
        'ja': '日本語'
    }
    
    # 默认目标语言
    DEFAULT_TARGET_LANGUAGES = ['zh-CN', 'zh-TW', 'ja']
    
    @classmethod
    def get_supported_languages(cls) -> List[str]:
        """获取支持的语言列表"""
        return list(cls.SUPPORTED_LANGUAGES.keys())
    
    @classmethod
    def is_language_supported(cls, language: str) -> bool:
        """检查语言是否支持"""
        return language in cls.SUPPORTED_LANGUAGES
    
    @classmethod
    def get_language_name(cls, language_code: str) -> str:
        """获取语言名称"""
        return cls.SUPPORTED_LANGUAGES.get(language_code, language_code) 