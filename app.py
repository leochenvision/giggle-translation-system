#!/usr/bin/env python3
"""
Giggle Academy 多语言翻译系统 - 主应用
"""

import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

from src.core.config import Config
from src.core.logger import setup_logger
from src.api.routes import api_bp
from src.services.task_service import TaskService
from src.utils.error_handler import ErrorHandler

# 加载环境变量
load_dotenv()

def create_app():
    """创建Flask应用实例"""
    app = Flask(__name__)
    
    # 配置应用
    app.config.from_object(Config)
    
    # 设置日志
    setup_logger()
    
    # 启用CORS
    CORS(app)
    
    # 注册蓝图
    app.register_blueprint(api_bp, url_prefix='/api/v1')
    
    # 错误处理
    ErrorHandler.register_handlers(app)
    
    # 健康检查
    @app.route('/health')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'service': 'giggle-translation-system',
            'version': '1.0.0'
        })
    
    # 根路径
    @app.route('/')
    def index():
        return jsonify({
            'message': 'Giggle Academy Translation System',
            'version': '1.0.0',
            'docs': '/api/v1/docs'
        })
    
    return app

def main():
    """主函数"""
    app = create_app()
    
    # 获取配置
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    
    # 启动应用
    app.run(
        host=host,
        port=port,
        debug=debug,
        threaded=True
    )

if __name__ == '__main__':
    main()