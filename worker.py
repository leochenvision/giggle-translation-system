#!/usr/bin/env python3
"""
后台任务处理Worker
"""

import time
import signal
import sys
from dotenv import load_dotenv
from src.core.config import Config
from src.core.logger import setup_logger, get_logger
from src.services.task_service import TaskService

# 加载环境变量
load_dotenv()

# 设置日志
setup_logger()
logger = get_logger("worker")

class TranslationWorker:
    """翻译任务处理Worker"""
    
    def __init__(self):
        """初始化Worker"""
        self.task_service = TaskService()
        self.running = True
        self.processed_tasks = 0
        
        # 注册信号处理器
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """信号处理器"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    def start(self):
        """启动Worker"""
        logger.info("Starting translation worker...")
        
        while self.running:
            try:
                # 从队列获取任务
                if self.task_service.use_memory_storage:
                    # 使用内存存储模式
                    if self.task_service.task_queue:
                        task_id = self.task_service.task_queue.pop(0)  # 从队列头部获取任务
                        logger.info(f"Processing task from memory queue: {task_id}")
                        
                        # 处理任务
                        success = self.task_service.process_task(task_id)
                        
                        if success:
                            self.processed_tasks += 1
                            logger.info(f"Task {task_id} completed successfully")
                        else:
                            logger.error(f"Task {task_id} failed")
                    else:
                        # 队列为空，等待一段时间
                        time.sleep(1)
                else:
                    # 使用Redis模式
                    task_id = self.task_service.redis_client.brpop('task_queue', timeout=1)
                    
                    if task_id:
                        task_id = task_id[1].decode('utf-8')
                        logger.info(f"Processing task from Redis: {task_id}")
                        
                        # 处理任务
                        success = self.task_service.process_task(task_id)
                        
                        if success:
                            self.processed_tasks += 1
                            logger.info(f"Task {task_id} completed successfully")
                        else:
                            logger.error(f"Task {task_id} failed")
                
                # 检查内存使用情况
                self._check_memory_usage()
                
            except KeyboardInterrupt:
                logger.info("Worker interrupted by user")
                break
            except Exception as e:
                logger.error(f"Error in worker loop: {str(e)}")
                time.sleep(1)
        
        logger.info(f"Worker stopped. Processed {self.processed_tasks} tasks")
    
    def _check_memory_usage(self):
        """检查内存使用情况"""
        try:
            import psutil
            memory_percent = psutil.virtual_memory().percent
            
            if memory_percent > 80:
                logger.warning(f"High memory usage: {memory_percent}%")
                # 可以在这里实现内存清理逻辑
                
        except ImportError:
            # psutil未安装，跳过内存检查
            pass
        except Exception as e:
            logger.error(f"Error checking memory usage: {str(e)}")

def main():
    """主函数"""
    try:
        worker = TranslationWorker()
        worker.start()
    except Exception as e:
        logger.error(f"Worker failed to start: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main() 