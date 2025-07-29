#!/usr/bin/env python3
"""
完整测试脚本
"""

import subprocess
import time
import requests
import json
import os
import sys

def start_services():
    """启动服务"""
    print("=== 启动服务 ===")
    
    # 检查API是否已经在运行
    try:
        response = requests.get("http://localhost:5000/api/v1/health", timeout=2)
        if response.status_code == 200:
            print("API服务已在运行")
            return True
    except:
        pass
    
    print("启动API服务...")
    # 启动API服务
    api_process = subprocess.Popen([
        sys.executable, "app.py"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # 等待API启动
    time.sleep(3)
    
    # 检查API是否启动成功
    try:
        response = requests.get("http://localhost:5000/api/v1/health", timeout=5)
        if response.status_code == 200:
            print("API服务启动成功")
        else:
            print(f"API服务启动失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"API服务启动失败: {e}")
        return False
    
    print("启动Worker服务...")
    # 启动Worker服务
    worker_process = subprocess.Popen([
        sys.executable, "worker.py"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    time.sleep(2)
    print("服务启动完成")
    return True

def test_translation():
    """测试翻译功能"""
    print("\n=== 测试翻译功能 ===")
    
    # 创建翻译任务
    task_data = {
        "audio_file": "data/audio/1.mp3",
        "text_file": "data/text/text.json",
        "target_languages": ["zh-CN", "zh-TW", "ja"]
    }
    
    try:
        print("创建翻译任务...")
        response = requests.post("http://localhost:5000/api/v1/tasks", json=task_data)
        
        if response.status_code == 201:
            result = response.json()
            task_id = result.get('task_id')
            print(f"任务创建成功，ID: {task_id}")
            
            # 监控任务状态
            print("监控任务进度...")
            for i in range(30):  # 最多等待30秒
                time.sleep(2)
                
                status_response = requests.get(f"http://localhost:5000/api/v1/tasks/{task_id}")
                if status_response.status_code == 200:
                    task_status = status_response.json()
                    status = task_status.get('status')
                    progress = task_status.get('progress', 0)
                    
                    print(f"状态: {status}, 进度: {progress}%")
                    
                    if status == 'completed':
                        print("任务完成！")
                        
                        # 获取结果
                        result_response = requests.get(f"http://localhost:5000/api/v1/tasks/{task_id}/result")
                        if result_response.status_code == 200:
                            result_data = result_response.json()
                            print("翻译结果:")
                            print(json.dumps(result_data, indent=2, ensure_ascii=False))
                        break
                    elif status == 'failed':
                        print("任务失败！")
                        error = task_status.get('error')
                        if error:
                            print(f"错误: {error}")
                        break
                else:
                    print(f"获取状态失败: {status_response.status_code}")
            
        else:
            print(f"任务创建失败: {response.status_code}")
            print(f"响应: {response.text}")
            
    except Exception as e:
        print(f"翻译测试失败: {e}")

def main():
    """主函数"""
    print("开始完整测试...")
    
    # 启动服务
    if not start_services():
        print("服务启动失败")
        return
    
    # 测试翻译
    test_translation()
    
    print("\n=== 测试完成 ===")

if __name__ == '__main__':
    main() 