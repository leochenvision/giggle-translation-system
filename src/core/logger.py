"""
日志配置模块
"""

import logging
import sys
import structlog
from typing import Dict, Any
from src.core.config import Config

def setup_logger():
    """设置结构化日志"""
    
    # 配置structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # 设置根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, Config.LOG_LEVEL.upper()))
    
    # 添加控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, Config.LOG_LEVEL.upper()))
    
    # 设置格式
    if Config.LOG_FORMAT.lower() == 'json':
        formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}'
        )
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # 创建应用日志器
    app_logger = structlog.get_logger("giggle-translation")
    
    return app_logger

def get_logger(name: str = None) -> structlog.BoundLogger:
    """获取日志器实例"""
    if name:
        return structlog.get_logger(name)
    return structlog.get_logger("giggle-translation")

def log_task_event(task_id: str, event: str, **kwargs):
    """记录任务事件"""
    logger = get_logger("task")
    logger.info(
        f"Task {event}",
        task_id=task_id,
        **kwargs
    )

def log_error(error: Exception, context: Dict[str, Any] = None):
    """记录错误日志"""
    logger = get_logger("error")
    logger.error(
        f"Error occurred: {str(error)}",
        error_type=type(error).__name__,
        error_message=str(error),
        context=context or {}
    ) 