#!/usr/bin/env python3
"""
监控服务
"""

import time
import os
import psutil
import redis
from prometheus_client import start_http_server, Gauge, Counter, Histogram
from dotenv import load_dotenv
from src.core.config import Config
from src.core.logger import setup_logger, get_logger

# 加载环境变量
load_dotenv()

# 设置日志
setup_logger()
logger = get_logger("monitor")

# Prometheus指标
TASK_COUNTER = Counter('giggle_tasks_total', 'Total number of tasks', ['status'])
TASK_DURATION = Histogram('giggle_task_duration_seconds', 'Task duration in seconds')
MEMORY_USAGE = Gauge('giggle_memory_bytes', 'Memory usage in bytes')
CPU_USAGE = Gauge('giggle_cpu_percent', 'CPU usage percentage')
REDIS_CONNECTIONS = Gauge('giggle_redis_connections', 'Redis active connections')
QUEUE_SIZE = Gauge('giggle_queue_size', 'Number of tasks in queue')

class MonitorService:
    """监控服务"""
    
    def __init__(self):
        """初始化监控服务"""
        self.redis_client = redis.from_url(Config.REDIS_URL)
        self.running = True
        
    def start_metrics_server(self):
        """启动Prometheus指标服务器"""
        port = int(os.getenv('PROMETHEUS_PORT', 9090))
        start_http_server(port)
        logger.info(f"Prometheus metrics server started on port {port}")
    
    def collect_system_metrics(self):
        """收集系统指标"""
        try:
            # 内存使用
            memory = psutil.virtual_memory()
            MEMORY_USAGE.set(memory.used)
            
            # CPU使用
            cpu_percent = psutil.cpu_percent(interval=1)
            CPU_USAGE.set(cpu_percent)
            
            logger.debug(f"System metrics - Memory: {memory.used} bytes, CPU: {cpu_percent}%")
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {str(e)}")
    
    def collect_redis_metrics(self):
        """收集Redis指标"""
        try:
            # Redis连接数
            info = self.redis_client.info()
            connections = info.get('connected_clients', 0)
            REDIS_CONNECTIONS.set(connections)
            
            # 队列大小
            queue_size = self.redis_client.llen('task_queue')
            QUEUE_SIZE.set(queue_size)
            
            logger.debug(f"Redis metrics - Connections: {connections}, Queue size: {queue_size}")
            
        except Exception as e:
            logger.error(f"Error collecting Redis metrics: {str(e)}")
    
    def collect_task_metrics(self):
        """收集任务指标"""
        try:
            # 获取所有任务
            task_keys = self.redis_client.keys('task:*')
            
            # 统计任务状态
            status_counts = {}
            for key in task_keys:
                task_data = self.redis_client.hgetall(key)
                if task_data:
                    status = task_data.get(b'status', b'unknown').decode('utf-8')
                    status_counts[status] = status_counts.get(status, 0) + 1
            
            # 更新Prometheus指标
            for status, count in status_counts.items():
                TASK_COUNTER.labels(status=status).inc(count)
            
            logger.debug(f"Task metrics - Status counts: {status_counts}")
            
        except Exception as e:
            logger.error(f"Error collecting task metrics: {str(e)}")
    
    def check_health(self):
        """健康检查"""
        try:
            # 检查Redis连接
            self.redis_client.ping()
            
            # 检查API服务
            import requests
            response = requests.get('http://localhost:5000/health', timeout=5)
            if response.status_code == 200:
                logger.info("Health check passed")
                return True
            else:
                logger.warning("Health check failed - API service")
                return False
                
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False
    
    def run(self):
        """运行监控服务"""
        logger.info("Starting monitor service...")
        
        # 启动Prometheus指标服务器
        self.start_metrics_server()
        
        # 主循环
        while self.running:
            try:
                # 收集指标
                self.collect_system_metrics()
                self.collect_redis_metrics()
                self.collect_task_metrics()
                
                # 健康检查
                self.check_health()
                
                # 等待下次收集
                time.sleep(30)  # 每30秒收集一次
                
            except KeyboardInterrupt:
                logger.info("Monitor service interrupted")
                break
            except Exception as e:
                logger.error(f"Error in monitor loop: {str(e)}")
                time.sleep(10)
        
        logger.info("Monitor service stopped")

def main():
    """主函数"""
    try:
        monitor = MonitorService()
        monitor.run()
    except Exception as e:
        logger.error(f"Monitor service failed to start: {str(e)}")

if __name__ == '__main__':
    main() 