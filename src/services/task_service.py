"""
任务服务模块
"""

import json
import time
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import redis
from src.core.config import Config
from src.core.logger import get_logger, log_task_event
from src.services.whisper_service import WhisperService
from src.services.translation_service import TranslationService
from src.services.packaging_service import PackagingService

logger = get_logger("task_service")

class TaskService:
    """任务服务类"""
    
    def __init__(self):
        """初始化任务服务"""
        self.redis_client = None
        self.use_memory_storage = False
        self.memory_storage = {}  # 内存存储
        self.task_queue = []      # 任务队列
        
        try:
            self.redis_client = redis.from_url(Config.REDIS_URL)
            # 测试Redis连接
            self.redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.warning(f"Redis connection failed: {str(e)}. Using memory storage.")
            self.use_memory_storage = True
        
        # 延迟初始化服务
        self.whisper_service = None
        self.translation_service = None
        self.packaging_service = None
        
    def create_task(self, task_data: Dict[str, Any]) -> bool:
        """创建新任务"""
        try:
            # 生成任务ID（如果不存在）
            if 'task_id' not in task_data:
                import uuid
                task_data['task_id'] = str(uuid.uuid4())
            
            task_id = task_data['task_id']
            task_data['created_at'] = datetime.now().isoformat()
            task_data['updated_at'] = datetime.now().isoformat()
            task_data['progress'] = 0
            task_data['status'] = 'pending'
            
            if self.use_memory_storage:
                # 使用内存存储
                self.memory_storage[f"task:{task_id}"] = task_data
                self.task_queue.append(task_id)
            else:
                # 保存到Redis
                self.redis_client.hset(
                    f"task:{task_id}",
                    mapping=task_data
                )
                # 添加到任务队列
                self.redis_client.lpush('task_queue', task_id)
            
            log_task_event(task_id, "created")
            return True
            
        except Exception as e:
            logger.error(f"Error creating task: {str(e)}")
            return False
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务信息"""
        try:
            if self.use_memory_storage:
                # 从内存存储获取
                task_data = self.memory_storage.get(f"task:{task_id}")
                return task_data
            else:
                # 从Redis获取
                task_data = self.redis_client.hgetall(f"task:{task_id}")
                if not task_data:
                    return None
                
                # 转换字节为字符串
                task = {}
                for key, value in task_data.items():
                    if isinstance(value, bytes):
                        task[key.decode('utf-8')] = value.decode('utf-8')
                    else:
                        task[key] = value
                
                return task
            
        except Exception as e:
            logger.error(f"Error getting task {task_id}: {str(e)}")
            return None
    
    def update_task_status(self, task_id: str, status: str, progress: int = None, error: str = None):
        """更新任务状态"""
        try:
            update_data = {
                'status': status,
                'updated_at': datetime.now().isoformat()
            }
            
            if progress is not None:
                update_data['progress'] = progress
            
            if error:
                update_data['error'] = error
            
            if self.use_memory_storage:
                # 更新内存存储
                task_key = f"task:{task_id}"
                if task_key in self.memory_storage:
                    self.memory_storage[task_key].update(update_data)
            else:
                # 更新Redis
                self.redis_client.hset(f"task:{task_id}", mapping=update_data)
            
            log_task_event(task_id, f"status_updated_to_{status}", progress=progress)
            
        except Exception as e:
            logger.error(f"Error updating task {task_id}: {str(e)}")
    
    def get_task_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务结果"""
        try:
            if self.use_memory_storage:
                # 从内存存储获取结果
                result_data = self.memory_storage.get(f"result:{task_id}")
                return result_data
            else:
                # 从Redis获取结果
                result_data = self.redis_client.hgetall(f"result:{task_id}")
                if not result_data:
                    return None
                
                # 转换字节为字符串
                result = {}
                for key, value in result_data.items():
                    if isinstance(value, bytes):
                        result[key.decode('utf-8')] = value.decode('utf-8')
                    else:
                        result[key] = value
                
                return result
            
        except Exception as e:
            logger.error(f"Error getting task result {task_id}: {str(e)}")
            return None
    
    def save_task_result(self, task_id: str, result_data: Dict[str, Any]):
        """保存任务结果"""
        try:
            result_data['created_at'] = datetime.now().isoformat()
            if self.use_memory_storage:
                self.memory_storage[f"result:{task_id}"] = result_data
            else:
                self.redis_client.hset(f"result:{task_id}", mapping=result_data)
            
        except Exception as e:
            logger.error(f"Error saving task result {task_id}: {str(e)}")
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        try:
            task = self.get_task(task_id)
            if not task:
                return False
            
            # 更新状态为取消
            self.update_task_status(task_id, 'cancelled')
            
            # 从队列中移除
            if self.use_memory_storage:
                if task_id in self.task_queue:
                    self.task_queue.remove(task_id)
            else:
                self.redis_client.lrem('task_queue', 0, task_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling task {task_id}: {str(e)}")
            return False
    
    def list_tasks(self, page: int = 1, per_page: int = 10, status: str = None) -> Dict[str, Any]:
        """列出任务"""
        try:
            if self.use_memory_storage:
                # 从内存存储获取所有任务
                task_keys = list(self.memory_storage.keys())
                tasks = []
                for key in task_keys:
                    if key.startswith("task:"):
                        task_id = key.split(':')[1]
                        task = self.memory_storage[key]
                        if task and (status is None or task.get('status') == status):
                            tasks.append(task)
            else:
                # 从Redis获取所有任务ID
                task_keys = self.redis_client.keys('task:*')
                tasks = []
                for key in task_keys:
                    task_id = key.decode('utf-8').split(':')[1]
                    task = self.get_task(task_id)
                    if task and (status is None or task.get('status') == status):
                        tasks.append(task)
            
            # 排序（最新的在前）
            tasks.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            # 分页
            total = len(tasks)
            start = (page - 1) * per_page
            end = start + per_page
            items = tasks[start:end]
            
            return {
                'items': items,
                'total': total,
                'page': page,
                'per_page': per_page,
                'pages': (total + per_page - 1) // per_page
            }
            
        except Exception as e:
            logger.error(f"Error listing tasks: {str(e)}")
            return {'items': [], 'total': 0, 'page': page, 'per_page': per_page, 'pages': 0}
    
    def check_redis_health(self) -> bool:
        """检查Redis连接健康状态"""
        try:
            if self.use_memory_storage:
                return True  # 内存存储总是可用的
            elif self.redis_client:
                self.redis_client.ping()
                return True
            return False
        except Exception as e:
            logger.error(f"Redis health check failed: {str(e)}")
            return False
    
    def process_task(self, task_id: str) -> bool:
        """处理任务"""
        try:
            task = self.get_task(task_id)
            if not task:
                logger.error(f"Task not found: {task_id}")
                return False
            
            # 初始化服务（如果需要）
            if self.whisper_service is None:
                from src.services.whisper_service import WhisperService
                self.whisper_service = WhisperService()
            
            if self.translation_service is None:
                from src.services.translation_service import TranslationService
                self.translation_service = TranslationService()
            
            if self.packaging_service is None:
                from src.services.packaging_service import PackagingService
                self.packaging_service = PackagingService()
            
            # 更新状态为处理中
            self.update_task_status(task_id, 'processing', 10)
            
            # 1. 语音识别
            logger.info(f"Starting speech recognition for task {task_id}")
            self.update_task_status(task_id, 'processing', 20)
            
            audio_file = task['audio_file']
            # 确保使用绝对路径
            if not os.path.isabs(audio_file):
                audio_file = os.path.abspath(audio_file)
            transcription = self.whisper_service.transcribe_audio(audio_file)
            
            if not transcription:
                self.update_task_status(task_id, 'failed', error="Speech recognition failed")
                return False
            
            # 2. 文本验证
            logger.info(f"Starting text validation for task {task_id}")
            self.update_task_status(task_id, 'processing', 40)
            
            text_file = task['text_file']
            validation_result = self._validate_text(transcription, text_file)
            
            # 3. 翻译
            logger.info(f"Starting translation for task {task_id}")
            self.update_task_status(task_id, 'processing', 60)
            
            target_languages = task['target_languages']
            translations = {}
            
            for lang in target_languages:
                translation = self.translation_service.translate_text(
                    transcription['text'], 
                    target_language=lang
                )
                if translation:
                    translations[lang] = translation
            
            # 4. 打包
            logger.info(f"Starting packaging for task {task_id}")
            self.update_task_status(task_id, 'processing', 80)
            
            packaged_file = self.packaging_service.create_package(
                task_id=task_id,
                original_text=transcription['text'],
                translations=translations,
                audio_transcription=transcription
            )
            
            # 5. 保存结果
            result_data = {
                'task_id': task_id,
                'status': 'completed',
                'translations': translations,
                'audio_transcription': transcription,
                'text_validation': validation_result,
                'packaged_file': packaged_file
            }
            
            self.save_task_result(task_id, result_data)
            self.update_task_status(task_id, 'completed', 100)
            
            log_task_event(task_id, "completed")
            return True
            
        except Exception as e:
            logger.error(f"Error processing task {task_id}: {str(e)}")
            self.update_task_status(task_id, 'failed', error=str(e))
            return False
    
    def _validate_text(self, transcription: Dict[str, Any], text_file: str) -> Dict[str, Any]:
        """验证文本准确性"""
        try:
            # 读取原始文本文件
            with open(text_file, 'r', encoding='utf-8') as f:
                original_text = json.load(f)
            
            stt_text = transcription['text']
            
            # 简单的文本比较
            similarity = self._calculate_similarity(stt_text, original_text.get('text', ''))
            
            return {
                'similarity': similarity,
                'original_text': original_text.get('text', ''),
                'stt_text': stt_text,
                'confidence': transcription.get('confidence', 0)
            }
            
        except Exception as e:
            logger.error(f"Error validating text: {str(e)}")
            return {
                'similarity': 0,
                'error': str(e)
            }
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度"""
        try:
            # 简单的字符级相似度计算
            if not text1 or not text2:
                return 0.0
            
            # 转换为小写并移除空格
            t1 = text1.lower().replace(' ', '')
            t2 = text2.lower().replace(' ', '')
            
            if not t1 or not t2:
                return 0.0
            
            # 计算编辑距离
            distance = self._levenshtein_distance(t1, t2)
            max_len = max(len(t1), len(t2))
            
            if max_len == 0:
                return 1.0
            
            similarity = 1 - (distance / max_len)
            return max(0.0, similarity)
            
        except Exception as e:
            logger.error(f"Error calculating similarity: {str(e)}")
            return 0.0
    
    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """计算Levenshtein距离"""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1] 