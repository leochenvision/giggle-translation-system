#!/usr/bin/env python3
"""
集成测试模块
"""

import pytest
import json
import os
import time
from unittest.mock import patch, MagicMock
from src.services.task_service import TaskService
from src.services.whisper_service import WhisperService
from src.services.translation_service import TranslationService
from src.services.packaging_service import PackagingService

class TestIntegration:
    """集成测试类"""
    
    @pytest.fixture
    def task_service(self):
        """创建任务服务实例"""
        return TaskService()
    
    @pytest.fixture
    def sample_task_data(self):
        """示例任务数据"""
        return {
            'task_id': 'test-task-123',
            'audio_file': 'tests/test_data/sample_audio.mp3',
            'text_file': 'tests/test_data/sample_text.json',
            'target_languages': ['zh-CN', 'zh-TW', 'ja'],
            'status': 'pending'
        }
    
    def test_task_creation_and_processing(self, task_service, sample_task_data):
        """测试任务创建和处理流程"""
        # 创建任务
        success = task_service.create_task(sample_task_data)
        assert success == True
        
        # 获取任务
        task = task_service.get_task(sample_task_data['task_id'])
        assert task is not None
        assert task['task_id'] == sample_task_data['task_id']
        assert task['status'] == 'pending'
    
    @patch('src.services.whisper_service.whisper.load_model')
    def test_whisper_service(self, mock_load_model):
        """测试Whisper服务"""
        # 模拟Whisper模型
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            'text': 'Hello world',
            'language': 'en',
            'segments': [{'avg_logprob': -0.1}]
        }
        mock_load_model.return_value = mock_model
        
        whisper_service = WhisperService()
        
        # 测试音频验证
        is_valid = whisper_service.validate_audio_file('tests/test_data/sample_audio.mp3')
        # 由于文件不存在，应该返回False
        assert is_valid == False
    
    @patch('openai.ChatCompletion.create')
    def test_translation_service(self, mock_openai):
        """测试翻译服务"""
        # 模拟OpenAI响应
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "你好世界"
        mock_openai.return_value = mock_response
        
        translation_service = TranslationService()
        
        # 测试翻译
        result = translation_service.translate_text("Hello world", "zh-CN")
        assert result == "你好世界"
    
    def test_packaging_service(self):
        """测试打包服务"""
        packaging_service = PackagingService()
        
        # 测试数据
        task_id = "test-task-123"
        original_text = "Hello world"
        translations = {
            "zh-CN": "你好世界",
            "zh-TW": "你好世界",
            "ja": "こんにちは世界"
        }
        audio_transcription = {
            "text": "Hello world",
            "confidence": 0.95,
            "language": "en"
        }
        
        # 创建包
        package_path = packaging_service.create_package(
            task_id, original_text, translations, audio_transcription
        )
        
        assert package_path != ""
        assert os.path.exists(package_path)
        
        # 读取包
        package_data = packaging_service.read_package(package_path)
        assert package_data is not None
        assert package_data['metadata']['task_id'] == task_id
        
        # 查询包内容
        zh_cn_text = packaging_service.query_package(package_path, "zh-CN")
        assert zh_cn_text is not None
        assert zh_cn_text['text'] == "你好世界"
        
        # 清理测试文件
        if os.path.exists(package_path):
            os.remove(package_path)
    
    def test_text_similarity_calculation(self, task_service):
        """测试文本相似度计算"""
        text1 = "Hello world"
        text2 = "Hello world"
        similarity = task_service._calculate_similarity(text1, text2)
        assert similarity == 1.0
        
        text3 = "Hello world!"
        similarity = task_service._calculate_similarity(text1, text3)
        assert similarity > 0.8
        
        text4 = "Goodbye world"
        similarity = task_service._calculate_similarity(text1, text4)
        assert similarity < 0.5
    
    def test_levenshtein_distance(self, task_service):
        """测试Levenshtein距离计算"""
        distance = task_service._levenshtein_distance("kitten", "sitting")
        assert distance == 3
        
        distance = task_service._levenshtein_distance("hello", "hello")
        assert distance == 0
        
        distance = task_service._levenshtein_distance("", "hello")
        assert distance == 5
    
    @patch('redis.from_url')
    def test_redis_health_check(self, mock_redis):
        """测试Redis健康检查"""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_redis.return_value = mock_client
        
        task_service = TaskService()
        is_healthy = task_service.check_redis_health()
        assert is_healthy == True
        
        # 测试连接失败
        mock_client.ping.side_effect = Exception("Connection failed")
        is_healthy = task_service.check_redis_health()
        assert is_healthy == False

def test_end_to_end_workflow():
    """端到端工作流测试"""
    # 这个测试需要实际的Redis和OpenAI API
    # 在实际环境中运行
    pass

if __name__ == '__main__':
    pytest.main([__file__, '-v']) 