"""
API测试模块
"""

import pytest
import json
import os
from unittest.mock import Mock, patch
from src.core.config import Config
from src.services.task_service import TaskService

class TestAPI:
    """API测试类"""
    
    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        from app import create_app
        app = create_app()
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    @pytest.fixture
    def sample_task_data(self):
        """示例任务数据"""
        return {
            "audio_file": "tests/test_data/sample_audio.mp3",
            "text_file": "tests/test_data/sample_text.json",
            "target_languages": ["zh-CN", "zh-TW", "ja"]
        }
    
    def test_health_check(self, client):
        """测试健康检查端点"""
        response = client.get('/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'status' in data
        assert 'service' in data
    
    def test_create_task_success(self, client, sample_task_data):
        """测试创建任务成功"""
        with patch('src.services.task_service.TaskService.create_task') as mock_create:
            mock_create.return_value = True
            
            response = client.post('/api/v1/tasks',
                                data=json.dumps(sample_task_data),
                                content_type='application/json')
            
            assert response.status_code == 201
            data = json.loads(response.data)
            assert 'task_id' in data
            assert data['status'] == 'pending'
    
    def test_create_task_missing_fields(self, client):
        """测试创建任务缺少必需字段"""
        response = client.post('/api/v1/tasks',
                             data=json.dumps({"audio_file": "test.mp3"}),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_create_task_unsupported_language(self, client, sample_task_data):
        """测试创建任务不支持的语言"""
        sample_task_data['target_languages'] = ['invalid-lang']
        
        response = client.post('/api/v1/tasks',
                             data=json.dumps(sample_task_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_get_task_success(self, client):
        """测试获取任务成功"""
        task_id = "test-task-id"
        mock_task = {
            "task_id": task_id,
            "status": "completed",
            "progress": 100,
            "target_languages": ["zh-CN", "zh-TW"]
        }
        
        with patch('src.services.task_service.TaskService.get_task') as mock_get:
            mock_get.return_value = mock_task
            
            response = client.get(f'/api/v1/tasks/{task_id}')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['task_id'] == task_id
            assert data['status'] == 'completed'
    
    def test_get_task_not_found(self, client):
        """测试获取不存在的任务"""
        task_id = "non-existent-task"
        
        with patch('src.services.task_service.TaskService.get_task') as mock_get:
            mock_get.return_value = None
            
            response = client.get(f'/api/v1/tasks/{task_id}')
            
            assert response.status_code == 404
            data = json.loads(response.data)
            assert 'error' in data
    
    def test_get_supported_languages(self, client):
        """测试获取支持的语言列表"""
        response = client.get('/api/v1/languages')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'languages' in data
        assert 'default_targets' in data
        assert len(data['languages']) > 0
    
    def test_cancel_task_success(self, client):
        """测试取消任务成功"""
        task_id = "test-task-id"
        
        with patch('src.services.task_service.TaskService.cancel_task') as mock_cancel:
            mock_cancel.return_value = True
            
            response = client.delete(f'/api/v1/tasks/{task_id}')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['status'] == 'cancelled'
    
    def test_cancel_task_not_found(self, client):
        """测试取消不存在的任务"""
        task_id = "non-existent-task"
        
        with patch('src.services.task_service.TaskService.cancel_task') as mock_cancel:
            mock_cancel.return_value = False
            
            response = client.delete(f'/api/v1/tasks/{task_id}')
            
            assert response.status_code == 404
            data = json.loads(response.data)
            assert 'error' in data
    
    def test_list_tasks(self, client):
        """测试列出任务"""
        mock_tasks = {
            'items': [
                {'task_id': 'task1', 'status': 'completed'},
                {'task_id': 'task2', 'status': 'pending'}
            ],
            'total': 2,
            'page': 1,
            'per_page': 10,
            'pages': 1
        }
        
        with patch('src.services.task_service.TaskService.list_tasks') as mock_list:
            mock_list.return_value = mock_tasks
            
            response = client.get('/api/v1/tasks')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'tasks' in data
            assert 'total' in data
            assert len(data['tasks']) == 2

if __name__ == '__main__':
    pytest.main([__file__]) 