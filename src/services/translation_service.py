"""
翻译服务模块
"""

import openai
from typing import Dict, Any, Optional
from src.core.config import Config
from src.core.logger import get_logger

logger = get_logger("translation_service")

class TranslationService:
    """翻译服务类"""
    
    def __init__(self):
        """初始化翻译服务"""
        self.api_key = Config.OPENAI_API_KEY
        self.model = Config.OPENAI_MODEL
        
        if self.api_key:
            openai.api_key = self.api_key
        else:
            logger.warning("OpenAI API key not configured")
    
    def translate_text(self, text: str, target_language: str, source_language: str = 'auto') -> Optional[str]:
        """翻译文本"""
        try:
            if not self.api_key:
                logger.error("OpenAI API key not configured")
                return None
            
            if not text.strip():
                logger.warning("Empty text provided for translation")
                return text
            
            # 构建翻译提示
            language_names = {
                'zh-CN': '简体中文',
                'zh-TW': '繁體中文',
                'ja': '日本語',
                'en': 'English'
            }
            
            target_lang_name = language_names.get(target_language, target_language)
            
            prompt = f"""
请将以下文本翻译成{target_lang_name}。请保持原文的意思和风格，确保翻译准确自然。

原文：
{text}

翻译：
"""
            
            # 调用OpenAI API
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的翻译助手，擅长多语言翻译。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.3
            )
            
            translation = response.choices[0].message.content.strip()
            logger.info(f"Translation completed: {len(text)} -> {len(translation)} characters")
            
            return translation
            
        except Exception as e:
            logger.error(f"Error translating text: {str(e)}")
            return None
    
    def translate_batch(self, texts: list, target_language: str, source_language: str = 'auto') -> list:
        """批量翻译文本"""
        try:
            translations = []
            
            for i, text in enumerate(texts):
                logger.info(f"Translating text {i+1}/{len(texts)}")
                translation = self.translate_text(text, target_language, source_language)
                translations.append(translation if translation else text)
            
            return translations
            
        except Exception as e:
            logger.error(f"Error in batch translation: {str(e)}")
            return texts
    
    def validate_translation(self, original: str, translation: str, target_language: str) -> Dict[str, Any]:
        """验证翻译质量"""
        try:
            if not self.api_key:
                return {'quality': 0.0, 'issues': ['API key not configured']}
            
            prompt = f"""
请评估以下翻译的质量，给出0-100的分数，并指出主要问题：

原文：{original}
翻译：{translation}
目标语言：{target_language}

请以JSON格式回复：
{{
    "score": 分数,
    "issues": ["问题1", "问题2"],
    "suggestions": ["建议1", "建议2"]
}}
"""
            
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个翻译质量评估专家。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.1
            )
            
            # 解析响应
            result_text = response.choices[0].message.content.strip()
            
            # 简单的JSON解析
            try:
                import json
                result = json.loads(result_text)
                return result
            except:
                # 如果JSON解析失败，返回默认结果
                return {
                    'score': 70,
                    'issues': ['Unable to parse evaluation result'],
                    'suggestions': ['Check translation manually']
                }
                
        except Exception as e:
            logger.error(f"Error validating translation: {str(e)}")
            return {
                'score': 0,
                'issues': [f'Validation error: {str(e)}'],
                'suggestions': ['Check translation manually']
            }
    
    def get_supported_languages(self) -> Dict[str, str]:
        """获取支持的语言"""
        return {
            'zh-CN': '简体中文',
            'zh-TW': '繁體中文',
            'ja': '日本語',
            'en': 'English'
        }
    
    def is_language_supported(self, language: str) -> bool:
        """检查语言是否支持"""
        supported = self.get_supported_languages()
        return language in supported
    
    def get_language_name(self, language_code: str) -> str:
        """获取语言名称"""
        supported = self.get_supported_languages()
        return supported.get(language_code, language_code) 