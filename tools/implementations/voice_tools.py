import edge_tts
import os
import tempfile
import logging
from typing import Dict, Any, Optional
from .log_decorator import log_tool_call
# 配置日志：输出到文件，定义格式和级别


# 定义默认配置
DEFAULT_VOICE = "zh-CN-XiaoxiaoNeural"
DEFAULT_AUDIO_PATH = "edge_mixed_audio.mp3"

class VoiceTools:
    """基础工具实现类"""
    
    @staticmethod
    @log_tool_call
    async def text_to_speech_edge_mixed(
        text: str, 
        audio_path: Optional[str] = None, 
        voice: Optional[str] = None,
        keep_file: bool = False
    ) -> Dict[str, Any]:
        """
        edge-tts 实现中英混搭文字转语音（生成+自动播放）
        
        Args:
            text: 待转换的中英混搭文本
            audio_path: 音频保存路径(支持mp3/wav),默认使用临时文件
            voice: 语音音色（需支持中英双语），默认: zh-CN-XiaoxiaoNeural
            keep_file: 是否保留音频文件,默认:False(自动删除)
            
        Returns:
            包含语音合成结果的字典
        """
        # 导入播放库（放在内部避免初始化失败影响整体）
        try:
            from playsound import playsound
        except ImportError as e:
            return {
                "success": False,
                "message": "播放功能初始化失败",
                "error": f"缺少playsound库: {str(e)}，请执行 pip install playsound 安装",
                "audio_path": None,
                "voice": voice or DEFAULT_VOICE
            }
        
        # 设置默认值
        use_voice = voice or DEFAULT_VOICE
        use_audio_path = audio_path
        
        try:
            # 处理临时文件逻辑
            if use_audio_path is None or not keep_file:
                # 创建临时MP3文件
                with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
                    use_audio_path = tmp.name
            
            # 1. 初始化语音合成对象
            logging.info(f"开始生成语音，文本：{text[:20]}... 音色：{use_voice}")
            communicate = edge_tts.Communicate(
                text=text,
                voice=use_voice,
                rate="+0%"  # 语速调整（-50%到+50%，0%为默认）
            )
            
            # 2. 保存音频文件
            await communicate.save(use_audio_path)
            logging.info(f"音频文件保存成功：{use_audio_path}")
            
            # 3. 自动播放音频
            print(f"正在播放音频：{use_audio_path}")
            playsound(use_audio_path)
            
            # 4. 清理临时文件
            if not keep_file and os.path.exists(use_audio_path):
                os.remove(use_audio_path)
                logging.info(f"临时文件已清理：{use_audio_path}")
            
            # 返回成功结果
            return {
                "success": True,
                "message": "音频生成并播放完成！",
                "audio_path": use_audio_path if keep_file else "临时文件已删除",
                "voice": use_voice,
                "text_length": len(text),
                "keep_file": keep_file
            }
            
        except Exception as e:
            # 异常处理：清理文件并返回错误信息
            error_msg = f"TTS处理失败: {str(e)}"
            logging.error(error_msg)
            
            # 清理临时文件
            if use_audio_path and os.path.exists(use_audio_path) and not keep_file:
                try:
                    os.remove(use_audio_path)
                    logging.info(f"异常时清理临时文件：{use_audio_path}")
                except:
                    pass
            
            # 返回失败结果
            return {
                "success": False,
                "message": "语音合成失败",
                "error": error_msg,
                "audio_path": use_audio_path,
                "voice": use_voice,
                "text_length": len(text) if 'text' in locals() else 0,
                "keep_file": keep_file
            }

# 测试示例（可选）
# if __name__ == "__main__":
#     async def test_tts():
#         """测试语音合成功能"""
#         result = await BaseTools.text_to_speech_edge_mixed(
#             text="测试语音输入，Hello World！",
#             voice="zh-CN-XiaoxiaoNeural",
#             keep_file=True  # 保留文件便于验证
#         )
#         print(f"合成结果：{result}")
    
#     # 运行测试
#     asyncio.run(test_tts())