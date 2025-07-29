"""
错误处理模块
"""

from flask import jsonify
from werkzeug.exceptions import HTTPException
from src.core.logger import get_logger

logger = get_logger("error_handler")

class ErrorHandler:
    """错误处理器"""
    
    @staticmethod
    def register_handlers(app):
        """注册错误处理器"""
        
        @app.errorhandler(400)
        def bad_request(error):
            logger.error(f"Bad request: {error}")
            return jsonify({
                'error': 'Bad request',
                'message': str(error),
                'status_code': 400
            }), 400
        
        @app.errorhandler(404)
        def not_found(error):
            logger.error(f"Not found: {error}")
            return jsonify({
                'error': 'Not found',
                'message': 'The requested resource was not found',
                'status_code': 404
            }), 404
        
        @app.errorhandler(500)
        def internal_error(error):
            logger.error(f"Internal server error: {error}")
            return jsonify({
                'error': 'Internal server error',
                'message': 'An unexpected error occurred',
                'status_code': 500
            }), 500
        
        @app.errorhandler(Exception)
        def handle_exception(error):
            logger.error(f"Unhandled exception: {error}")
            return jsonify({
                'error': 'Internal server error',
                'message': 'An unexpected error occurred',
                'status_code': 500
            }), 500
        
        @app.errorhandler(HTTPException)
        def handle_http_exception(error):
            logger.error(f"HTTP exception: {error}")
            return jsonify({
                'error': error.name,
                'message': error.description,
                'status_code': error.code
            }), error.code 