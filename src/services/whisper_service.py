"""
Whisper语音识别服务
"""

import os
import whisper
from typing import Dict, Any, Optional
from src.core.config import Config
from src.core.logger import get_logger

logger = get_logger("whisper_service")

class WhisperService:
    """Whisper语音识别服务"""
    
    def __init__(self):
        """初始化Whisper服务"""
        self.model = None
        self.model_name = Config.WHISPER_MODEL
        self.device = Config.WHISPER_DEVICE
        
        # 设置FFmpeg路径
        ffmpeg_path = os.path.join(os.path.expanduser("~"), "AppData", "Local", "Microsoft", "WinGet", "Packages", 
                                   "Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe", "ffmpeg-7.1.1-full_build", "bin", "ffmpeg.exe")
        if os.path.exists(ffmpeg_path):
            os.environ["PATH"] = os.path.dirname(ffmpeg_path) + os.pathsep + os.environ.get("PATH", "")
            logger.info(f"FFmpeg path set: {ffmpeg_path}")
        else:
            logger.warning(f"FFmpeg not found at: {ffmpeg_path}")
        
    def _load_model(self):
        """加载Whisper模型"""
        if self.model is None:
            try:
                logger.info(f"Loading Whisper model: {self.model_name}")
                self.model = whisper.load_model(self.model_name, device=self.device)
                logger.info("Whisper model loaded successfully")
            except Exception as e:
                logger.error(f"Error loading Whisper model: {str(e)}")
                raise
    
    def transcribe_audio(self, audio_file: str) -> Optional[Dict[str, Any]]:
        """转录音频文件"""
        try:
            # 检查文件是否存在
            if not os.path.exists(audio_file):
                logger.error(f"Audio file not found: {audio_file}")
                return None
            
            # 加载模型
            self._load_model()
            
            # 执行转录
            logger.info(f"Transcribing audio file: {audio_file}")
            result = self.model.transcribe(audio_file)
            
            # 处理结果
            transcription = {
                'text': result.get('text', '').strip(),
                'language': result.get('language', 'unknown'),
                'segments': result.get('segments', []),
                'confidence': self._calculate_confidence(result)
            }
            
            logger.info(f"Transcription completed: {len(transcription['text'])} characters")
            return transcription
            
        except Exception as e:
            logger.error(f"Error transcribing audio {audio_file}: {str(e)}")
            return None
    
    def _calculate_confidence(self, result: Dict[str, Any]) -> float:
        """计算转录置信度"""
        try:
            segments = result.get('segments', [])
            if not segments:
                return 0.0
            
            # 计算平均置信度
            total_confidence = 0.0
            total_segments = 0
            
            for segment in segments:
                if 'avg_logprob' in segment:
                    # 将log概率转换为置信度
                    confidence = max(0.0, min(1.0, (segment['avg_logprob'] + 1.0) / 2.0))
                    total_confidence += confidence
                    total_segments += 1
            
            if total_segments > 0:
                return total_confidence / total_segments
            else:
                return 0.0
                
        except Exception as e:
            logger.error(f"Error calculating confidence: {str(e)}")
            return 0.0
    
    def detect_language(self, audio_file: str) -> Optional[str]:
        """检测音频语言"""
        try:
            if not os.path.exists(audio_file):
                logger.error(f"Audio file not found: {audio_file}")
                return None
            
            self._load_model()
            
            logger.info(f"Detecting language for: {audio_file}")
            result = self.model.transcribe(audio_file, task="language_detection")
            
            language = result.get('language', 'unknown')
            logger.info(f"Detected language: {language}")
            
            return language
            
        except Exception as e:
            logger.error(f"Error detecting language for {audio_file}: {str(e)}")
            return None
    
    def get_available_models(self) -> list:
        """获取可用的模型列表"""
        return whisper.available_models()
    
    def validate_audio_file(self, audio_file: str) -> bool:
        """验证音频文件"""
        try:
            if not os.path.exists(audio_file):
                return False
            
            # 检查文件扩展名
            supported_extensions = ['.mp3', '.wav', '.m4a', '.flac', '.ogg']
            file_ext = os.path.splitext(audio_file)[1].lower()
            
            if file_ext not in supported_extensions:
                logger.warning(f"Unsupported audio format: {file_ext}")
                return False
            
            # 检查文件大小
            file_size = os.path.getsize(audio_file)
            max_size = 100 * 1024 * 1024  # 100MB
            
            if file_size > max_size:
                logger.warning(f"Audio file too large: {file_size} bytes")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating audio file {audio_file}: {str(e)}")
            return False 