#!/usr/bin/env python3
"""
读取output目录中的文件内容
"""

import os
import json
import base64
import gzip
import glob

def read_gcp_file(file_path):
    """读取.gcp文件内容"""
    print(f"=== 读取文件: {os.path.basename(file_path)} ===")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if len(lines) >= 2:
            header = lines[0].strip()
            content = lines[1].strip()
            
            print(f"文件头: {header}")
            print(f"内容长度: {len(content)} 字符")
            
            # 尝试解码Base64内容
            try:
                decoded_bytes = base64.b64decode(content)
                print(f"解码后长度: {len(decoded_bytes)} 字节")
                
                # 尝试解压gzip
                try:
                    decompressed = gzip.decompress(decoded_bytes)
                    print(f"解压后长度: {len(decompressed)} 字节")
                    
                    # 尝试解析为JSON
                    try:
                        data = json.loads(decompressed.decode('utf-8'))
                        print("✅ 成功解析为JSON:")
                        print(json.dumps(data, indent=2, ensure_ascii=False))
                        return data
                    except json.JSONDecodeError:
                        print("⚠️ 解压后内容不是JSON格式")
                        print("原始内容:")
                        print(decompressed.decode('utf-8', errors='ignore'))
                        return None
                        
                except Exception as e:
                    print(f"❌ 解压失败: {e}")
                    print("原始Base64内容:")
                    print(content[:100] + "..." if len(content) > 100 else content)
                    return None
                    
            except Exception as e:
                print(f"❌ Base64解码失败: {e}")
                return None
        else:
            print("❌ 文件格式不正确")
            return None
            
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        return None

def list_output_files():
    """列出output目录中的所有文件"""
    output_dir = "data/output"
    
    if not os.path.exists(output_dir):
        print(f"❌ 输出目录不存在: {output_dir}")
        return []
    
    # 查找所有.gcp文件
    gcp_files = glob.glob(os.path.join(output_dir, "*.gcp"))
    
    print(f"=== 输出目录: {output_dir} ===")
    print(f"找到 {len(gcp_files)} 个.gcp文件:")
    
    for i, file_path in enumerate(gcp_files, 1):
        file_size = os.path.getsize(file_path)
        file_name = os.path.basename(file_path)
        print(f"  {i}. {file_name} ({file_size} bytes)")
    
    return gcp_files

def main():
    """主函数"""
    print("📁 读取output目录中的文件")
    print("=" * 50)
    
    # 列出所有文件
    gcp_files = list_output_files()
    
    if not gcp_files:
        print("❌ 没有找到.gcp文件")
        return
    
    # 读取每个文件
    for file_path in gcp_files:
        data = read_gcp_file(file_path)
        
        if data:
            print(f"\n✅ 文件 {os.path.basename(file_path)} 解析成功")
            
            # 提取翻译内容
            if 'translations' in data:
                print("\n📋 翻译内容:")
                translations = data['translations']
                for lang, text in translations.items():
                    print(f"  {lang}: {text}")
            
            if 'audio_transcription' in data:
                print("\n🎤 音频转录:")
                transcription = data['audio_transcription']
                print(f"  文本: {transcription.get('text', 'N/A')}")
                print(f"  语言: {transcription.get('language', 'N/A')}")
                print(f"  置信度: {transcription.get('confidence', 'N/A')}")
        
        print("\n" + "-" * 50)

if __name__ == '__main__':
    main() 