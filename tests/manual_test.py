#!/usr/bin/env python3
"""
手动测试模块
"""

import json
import os
import sys
import time
from dotenv import load_dotenv

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.config import Config
from src.core.logger import setup_logger, get_logger
from src.services.task_service import TaskService
from src.services.whisper_service import WhisperService
from src.services.translation_service import TranslationService
from src.services.packaging_service import PackagingService

# 加载环境变量
load_dotenv()

# 设置日志
setup_logger()
logger = get_logger("manual_test")

def test_whisper_service():
    """测试Whisper服务"""
    print("\n=== 测试 Whisper 服务 ===")
    
    whisper_service = WhisperService()
    
    # 测试可用模型
    try:
        models = whisper_service.get_available_models()
        print(f"可用模型: {models}")
    except Exception as e:
        print(f"获取模型列表失败: {e}")
    
    # 测试音频文件验证
    test_audio_file = "tests/test_data/sample_audio.mp3"
    is_valid = whisper_service.validate_audio_file(test_audio_file)
    print(f"音频文件验证: {is_valid}")
    
    print("Whisper 服务测试完成")

def test_translation_service():
    """测试翻译服务"""
    print("\n=== 测试翻译服务 ===")
    
    translation_service = TranslationService()
    
    # 测试支持的语言
    languages = translation_service.get_supported_languages()
    print(f"支持的语言: {languages}")
    
    # 测试翻译（需要OpenAI API密钥）
    if Config.OPENAI_API_KEY:
        test_text = "Hello world, this is a test."
        result = translation_service.translate_text(test_text, "zh-CN")
        print(f"翻译结果: {result}")
    else:
        print("未配置OpenAI API密钥，跳过翻译测试")
    
    print("翻译服务测试完成")

def test_packaging_service():
    """测试打包服务"""
    print("\n=== 测试打包服务 ===")
    
    packaging_service = PackagingService()
    
    # 测试数据
    task_id = "manual-test-123"
    original_text = "Hello world, this is a test story for children."
    translations = {
        "zh-CN": "你好世界，这是一个儿童测试故事。",
        "zh-TW": "你好世界，這是一個兒童測試故事。",
        "ja": "こんにちは世界、これは子供のテストストーリーです。"
    }
    audio_transcription = {
        "text": "Hello world this is a test story for children",
        "confidence": 0.92,
        "language": "en"
    }
    
    # 创建包
    package_path = packaging_service.create_package(
        task_id, original_text, translations, audio_transcription
    )
    
    if package_path and os.path.exists(package_path):
        print(f"包创建成功: {package_path}")
        
        # 读取包信息
        info = packaging_service.get_package_info(package_path)
        print(f"包信息: {json.dumps(info, indent=2, ensure_ascii=False)}")
        
        # 查询不同语言
        for lang in ["zh-CN", "zh-TW", "ja", "original", "audio"]:
            result = packaging_service.query_package(package_path, lang)
            if result:
                print(f"{lang}: {result['text'][:50]}...")
        
        # 验证包
        is_valid = packaging_service.validate_package(package_path)
        print(f"包验证: {is_valid}")
        
        # 清理测试文件
        os.remove(package_path)
        print("测试文件已清理")
    else:
        print("包创建失败")
    
    print("打包服务测试完成")

def test_task_service():
    """测试任务服务"""
    print("\n=== 测试任务服务 ===")
    
    task_service = TaskService()
    
    # 测试Redis连接
    is_healthy = task_service.check_redis_health()
    print(f"Redis连接状态: {is_healthy}")
    
    if not is_healthy:
        print("Redis未连接，跳过任务服务测试")
        return
    
    # 创建测试任务
    task_data = {
        'task_id': 'manual-test-task',
        'audio_file': 'tests/test_data/sample_audio.mp3',
        'text_file': 'tests/test_data/sample_text.json',
        'target_languages': ['zh-CN', 'zh-TW'],
        'status': 'pending'
    }
    
    # 创建任务
    success = task_service.create_task(task_data)
    print(f"任务创建: {success}")
    
    if success:
        # 获取任务
        task = task_service.get_task('manual-test-task')
        print(f"任务信息: {json.dumps(task, indent=2, ensure_ascii=False)}")
        
        # 更新任务状态
        task_service.update_task_status('manual-test-task', 'processing', 50)
        
        # 列出任务
        tasks = task_service.list_tasks()
        print(f"任务列表: {len(tasks['items'])} 个任务")
        
        # 取消任务
        cancel_success = task_service.cancel_task('manual-test-task')
        print(f"任务取消: {cancel_success}")
    
    print("任务服务测试完成")

def test_config():
    """测试配置"""
    print("\n=== 测试配置 ===")
    
    print(f"支持的语言: {Config.get_supported_languages()}")
    print(f"默认目标语言: {Config.DEFAULT_TARGET_LANGUAGES}")
    print(f"Redis URL: {Config.REDIS_URL}")
    print(f"Whisper 模型: {Config.WHISPER_MODEL}")
    print(f"Whisper 设备: {Config.WHISPER_DEVICE}")
    print(f"OpenAI 模型: {Config.OPENAI_MODEL}")
    
    # 测试语言支持
    test_languages = ['en', 'zh-CN', 'zh-TW', 'ja', 'invalid']
    for lang in test_languages:
        is_supported = Config.is_language_supported(lang)
        print(f"{lang}: {'支持' if is_supported else '不支持'}")
    
    print("配置测试完成")

def main():
    """主测试函数"""
    print("开始手动测试...")
    
    try:
        # 测试配置
        test_config()
        
        # 测试Whisper服务
        test_whisper_service()
        
        # 测试翻译服务
        test_translation_service()
        
        # 测试打包服务
        test_packaging_service()
        
        # 测试任务服务
        test_task_service()
        
        print("\n=== 所有测试完成 ===")
        
    except Exception as e:
        logger.error(f"测试过程中发生错误: {str(e)}")
        print(f"测试失败: {str(e)}")

if __name__ == '__main__':
    main() 