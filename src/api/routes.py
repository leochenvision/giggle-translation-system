"""
API路由模块
"""

import uuid
import os
from flask import Blueprint, request, jsonify
from werkzeug.exceptions import BadRequest, NotFound
from src.core.config import Config
from src.services.task_service import TaskService
from src.services.packaging_service import PackagingService
from src.utils.error_handler import ErrorHandler
from src.core.logger import get_logger, log_task_event

# 创建蓝图
api_bp = Blueprint('api', __name__)
logger = get_logger("api")

# 任务服务实例
task_service = TaskService()
packaging_service = PackagingService()

@api_bp.route('/tasks', methods=['POST'])
def create_task():
    """创建翻译任务"""
    try:
        data = request.get_json()
        if not data:
            raise BadRequest("Request body is required")
        
        # 验证必需字段
        required_fields = ['audio_file', 'text_file']
        for field in required_fields:
            if field not in data:
                raise BadRequest(f"Missing required field: {field}")
        
        # 获取目标语言
        target_languages = data.get('target_languages', Config.DEFAULT_TARGET_LANGUAGES)
        
        # 验证语言支持
        for lang in target_languages:
            if not Config.is_language_supported(lang):
                raise BadRequest(f"Unsupported language: {lang}")
        
        # 创建任务
        task_id = str(uuid.uuid4())
        task_data = {
            'task_id': task_id,
            'audio_file': data['audio_file'],
            'text_file': data['text_file'],
            'target_languages': target_languages,
            'status': 'pending'
        }
        
        # 保存任务
        if not task_service.create_task(task_data):
            raise Exception("Failed to create task")
        
        log_task_event(task_id, "created", target_languages=target_languages)
        
        return jsonify({
            'task_id': task_id,
            'status': 'pending',
            'message': 'Task created successfully'
        }), 201
        
    except BadRequest as e:
        logger.error(f"Bad request: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error creating task: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/tasks/<task_id>', methods=['GET'])
def get_task(task_id):
    """获取任务状态"""
    try:
        task = task_service.get_task(task_id)
        if not task:
            raise NotFound(f"Task not found: {task_id}")
        
        return jsonify({
            'task_id': task_id,
            'status': task.get('status', 'unknown'),
            'progress': task.get('progress', 0),
            'created_at': task.get('created_at'),
            'updated_at': task.get('updated_at'),
            'target_languages': task.get('target_languages', []),
            'error': task.get('error')
        })
        
    except NotFound as e:
        logger.error(f"Task not found: {task_id}")
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        logger.error(f"Error getting task {task_id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/tasks/<task_id>/result', methods=['GET'])
def get_task_result(task_id):
    """获取任务结果"""
    try:
        result = task_service.get_task_result(task_id)
        if not result:
            raise NotFound(f"Task result not found: {task_id}")
        
        return jsonify({
            'task_id': task_id,
            'status': result.get('status'),
            'translations': result.get('translations', {}),
            'audio_transcription': result.get('audio_transcription'),
            'text_validation': result.get('text_validation'),
            'packaged_file': result.get('packaged_file'),
            'created_at': result.get('created_at')
        })
        
    except NotFound as e:
        logger.error(f"Task result not found: {task_id}")
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        logger.error(f"Error getting task result {task_id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/tasks/<task_id>', methods=['DELETE'])
def cancel_task(task_id):
    """取消任务"""
    try:
        success = task_service.cancel_task(task_id)
        if not success:
            raise NotFound(f"Task not found: {task_id}")
        
        log_task_event(task_id, "cancelled")
        
        return jsonify({
            'task_id': task_id,
            'status': 'cancelled',
            'message': 'Task cancelled successfully'
        })
        
    except NotFound as e:
        logger.error(f"Task not found: {task_id}")
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        logger.error(f"Error cancelling task {task_id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/tasks', methods=['GET'])
def list_tasks():
    """列出所有任务"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        status = request.args.get('status')
        
        tasks = task_service.list_tasks(page=page, per_page=per_page, status=status)
        
        return jsonify({
            'tasks': tasks['items'],
            'total': tasks['total'],
            'page': page,
            'per_page': per_page,
            'pages': tasks['pages']
        })
        
    except Exception as e:
        logger.error(f"Error listing tasks: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/languages', methods=['GET'])
def get_supported_languages():
    """获取支持的语言列表"""
    try:
        languages = []
        for code, name in Config.SUPPORTED_LANGUAGES.items():
            languages.append({
                'code': code,
                'name': name
            })
        
        return jsonify({
            'languages': languages,
            'default_targets': Config.DEFAULT_TARGET_LANGUAGES
        })
        
    except Exception as e:
        logger.error(f"Error getting languages: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    try:
        # 检查Redis连接
        redis_healthy = task_service.check_redis_health()
        
        return jsonify({
            'status': 'healthy' if redis_healthy else 'unhealthy',
            'redis': 'connected' if redis_healthy else 'disconnected',
            'service': 'giggle-translation-api'
        })
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500 

@api_bp.route('/query', methods=['GET'])
def query_package_content():
    """查询打包文件内容 - 通过语言、文本编号、来源直接查询"""
    try:
        # 获取查询参数
        language = request.args.get('language')
        text_id = request.args.get('text_id', 'main')
        source = request.args.get('source')  # TEXT, AUDIO, 或 None表示任意来源
        
        # 验证必需参数
        if not language:
            raise BadRequest("language is required")
        
        # 扫描所有打包文件
        output_dir = Config.OUTPUT_FOLDER
        if not os.path.exists(output_dir):
            raise NotFound("No output directory found")
        
        # 查找所有.gcp文件
        gcp_files = [f for f in os.listdir(output_dir) if f.endswith('.gcp')]
        if not gcp_files:
            raise NotFound("No package files found")
        
        # 遍历所有文件查找匹配的内容
        for filename in gcp_files:
            filepath = os.path.join(output_dir, filename)
            
            try:
                package_data = packaging_service.read_package(filepath)
                if not package_data:
                    continue
                
                content = package_data.get('content', {})
                task_id = package_data.get('metadata', {}).get('task_id', 'unknown')
                
                # 查询逻辑
                found_result = None
                
                if language == 'original':
                    # 查询原始文本
                    original = content.get('original', {})
                    if original and (not source or original.get('source') == source):
                        found_result = {
                            'task_id': task_id,
                            'language': language,
                            'text_id': text_id,
                            'found': True,
                            'text': original.get('text', ''),
                            'source': original.get('source', 'TEXT'),
                            'filename': filename
                        }
                
                elif language == 'audio':
                    # 查询音频转录
                    audio = content.get('audio', {})
                    if audio and (not source or audio.get('source') == source):
                        found_result = {
                            'task_id': task_id,
                            'language': language,
                            'text_id': text_id,
                            'found': True,
                            'text': audio.get('text', ''),
                            'source': audio.get('source', 'AUDIO'),
                            'confidence': audio.get('confidence', 0),
                            'filename': filename
                        }
                
                else:
                    # 查询翻译
                    translations = content.get('translations', {})
                    if language in translations:
                        translation = translations[language]
                        if not source or translation.get('source') == source:
                            found_result = {
                                'task_id': task_id,
                                'language': language,
                                'text_id': text_id,
                                'found': True,
                                'text': translation.get('text', ''),
                                'source': translation.get('source', 'TEXT'),
                                'filename': filename
                            }
                
                # 如果找到匹配的内容，立即返回
                if found_result:
                    return jsonify(found_result)
                    
            except Exception as e:
                logger.warning(f"Error reading package {filename}: {str(e)}")
                continue
        
        # 如果没有找到匹配的内容
        return jsonify({
            'error': f'Content not found for language: {language}, text_id: {text_id}, source: {source or "any"}'
        }), 404
        
    except BadRequest as e:
        logger.error(f"Bad request in query: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except NotFound as e:
        logger.error(f"Not found in query: {str(e)}")
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        logger.error(f"Error in query: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/query/all', methods=['GET'])
def query_all_packages():
    """查询所有打包文件中的内容"""
    try:
        # 获取查询参数
        language = request.args.get('language')
        source = request.args.get('source')  # TEXT, AUDIO, 或 None表示任意来源
        
        # 验证必需参数
        if not language:
            raise BadRequest("language is required")
        
        # 扫描所有打包文件
        output_dir = Config.OUTPUT_FOLDER
        if not os.path.exists(output_dir):
            raise NotFound("No output directory found")
        
        # 查找所有.gcp文件
        gcp_files = [f for f in os.listdir(output_dir) if f.endswith('.gcp')]
        if not gcp_files:
            raise NotFound("No package files found")
        
        results = []
        
        # 遍历所有文件查找匹配的内容
        for filename in gcp_files:
            filepath = os.path.join(output_dir, filename)
            
            try:
                package_data = packaging_service.read_package(filepath)
                if not package_data:
                    continue
                
                content = package_data.get('content', {})
                task_id = package_data.get('metadata', {}).get('task_id', 'unknown')
                
                # 查询逻辑
                if language == 'original':
                    # 查询原始文本
                    original = content.get('original', {})
                    if original and (not source or original.get('source') == source):
                        results.append({
                            'task_id': task_id,
                            'language': language,
                            'text': original.get('text', ''),
                            'source': original.get('source', 'TEXT'),
                            'filename': filename
                        })
                
                elif language == 'audio':
                    # 查询音频转录
                    audio = content.get('audio', {})
                    if audio and (not source or audio.get('source') == source):
                        results.append({
                            'task_id': task_id,
                            'language': language,
                            'text': audio.get('text', ''),
                            'source': audio.get('source', 'AUDIO'),
                            'confidence': audio.get('confidence', 0),
                            'filename': filename
                        })
                
                else:
                    # 查询翻译
                    translations = content.get('translations', {})
                    if language in translations:
                        translation = translations[language]
                        if not source or translation.get('source') == source:
                            results.append({
                                'task_id': task_id,
                                'language': language,
                                'text': translation.get('text', ''),
                                'source': translation.get('source', 'TEXT'),
                                'filename': filename
                            })
                    
            except Exception as e:
                logger.warning(f"Error reading package {filename}: {str(e)}")
                continue
        
        return jsonify({
            'language': language,
            'source': source or 'any',
            'count': len(results),
            'results': results
        })
        
    except BadRequest as e:
        logger.error(f"Bad request in query all: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except NotFound as e:
        logger.error(f"Not found in query all: {str(e)}")
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        logger.error(f"Error in query all: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/packages/<task_id>/info', methods=['GET'])
def get_package_info(task_id):
    """获取打包文件信息"""
    try:
        filename = f"giggle_package_{task_id}.gcp"
        filepath = os.path.join(Config.OUTPUT_FOLDER, filename)
        
        if not os.path.exists(filepath):
            raise NotFound(f"Package file not found for task: {task_id}")
        
        info = packaging_service.get_package_info(filepath)
        if not info:
            raise NotFound(f"Invalid package file for task: {task_id}")
        
        return jsonify(info)
        
    except NotFound as e:
        logger.error(f"Package not found: {task_id}")
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        logger.error(f"Error getting package info {task_id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/packages/<task_id>/texts', methods=['GET'])
def get_all_texts(task_id):
    """获取打包文件中的所有文本"""
    try:
        filename = f"giggle_package_{task_id}.gcp"
        filepath = os.path.join(Config.OUTPUT_FOLDER, filename)
        
        if not os.path.exists(filepath):
            raise NotFound(f"Package file not found for task: {task_id}")
        
        texts = packaging_service.extract_texts(filepath)
        if not texts:
            raise NotFound(f"No texts found in package for task: {task_id}")
        
        return jsonify({
            'task_id': task_id,
            'texts': texts
        })
        
    except NotFound as e:
        logger.error(f"Package not found: {task_id}")
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        logger.error(f"Error getting texts {task_id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500 