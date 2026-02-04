import subprocess 
import os 
import sys 

from typing import Dict, Any, Optional
# 配置日志：输出到文件，定义格式和级别
from . import log_tool_call

class VoiceTools:
    """基础工具实现类"""
    
    @staticmethod
    @log_tool_call
    def balcon_tts(text, save_to_file=None, voice_name=None, speed=90): 
        """ 
        调用Balcon实现文本转语音 
        :param text: 要合成语音的文本（必填） 
        :param save_to_file: 保存语音文件的路径（如"output.wav"，可选，不填则直接播放） 
        :param voice_name: 语音库名称（可选，不填则用默认语音） 
        :param speed: 语速（1-200，默认100） 
        :return: 成功返回True，失败返回False 
        """ 
        # 1. 确定Balcon的路径 
        balcon_path = os.path.join(os.getcwd(), "utils_bin", "balcon", "balcon.exe") 
        if not os.path.exists(balcon_path): 
            print(f"错误：找不到Balcon程序，路径：{balcon_path}") 
            return False 

        # 2. 构造Balcon的命令行参数 
        cmd = [balcon_path] 
        # 文本预处理：过滤掉不需要的内容
        if text:
            # 过滤掉换行符和反斜杠
            filtered_text = text.replace('\n', ' ').replace('\r', ' ').replace('\\', '')
            # 过滤掉emoji表情和其他特殊字符
            import re
            # 使用更全面的正则表达式过滤掉emoji和其他可能导致问题的字符
            # 保留ASCII字符、中文字符和中文标点符号
            # 中文标点符号范围：\u3000-\u303F（全角标点）、\uFF00-\uFFEF（半角标点）
            filtered_text = re.sub('[^\x00-\x7F\u4E00-\u9FFF\u3000-\u303F\uFF00-\uFFEF]', '', filtered_text)
            # 解决Balcon可能吞掉前几个字的问题：
            # 1. 在文本前添加多个中文空格，确保Balcon正确处理文本的开头部分
            # 2. 中文空格在语音播放时不会被明显察觉
            # 3. 使用多个空格增加保险系数，确保Balcon不会丢失开头的文字
            adjusted_text = "　　　" + filtered_text
        else:
            adjusted_text = text
        cmd.extend(["-t", adjusted_text]) 
        cmd.extend(["-s", str(speed)]) 
        if voice_name: 
            cmd.extend(["-n", voice_name]) 
        if save_to_file: 
            cmd.extend(["-w", save_to_file]) 

        # 3. 执行命令（增加调试信息） 
        try: 
            print(f"执行命令：{' '.join(cmd)}")  # 打印完整命令，方便调试 
            
            # 使用Popen在后台执行，避免阻塞主线程
            # 这样用户可以在语音播放的同时输入内容
            process = subprocess.Popen( 
                cmd, 
                encoding="gbk", 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE 
            ) 
            
            # 对于保存文件的情况，我们需要等待执行完成
            # 对于直接播放的情况，我们可以立即返回
            if save_to_file: 
                stdout, stderr = process.communicate() 
                if process.returncode == 0: 
                    print(f"成功！语音已保存至：{os.path.abspath(save_to_file)}") 
                else: 
                    print(f"执行失败！返回码：{process.returncode}") 
                    print(f"标准输出：{stdout}") 
                    print(f"标准错误：{stderr}") 
                    return False 
            else: 
                # 直接播放时，立即返回True，不等待执行完成
                print(f"开始播放语音：{text}") 
            
            return True 
        except Exception as e: 
            print(f"未知错误：{str(e)}") 
            return False 

    @staticmethod
    @log_tool_call
    def list_balcon_voices(): 
        """ 
        调用Balcon列出所有可用的语音库（去重+过滤无效行） 
        :return: 去重后的语音库列表 
        """ 
        balcon_path = os.path.join(os.getcwd(), "utils_bin", "balcon", "balcon.exe") 
        if not os.path.exists(balcon_path): 
            print(f"错误：找不到Balcon程序，路径：{balcon_path}") 
            return [] 

        try: 
            result = subprocess.run( 
                [balcon_path, "-l"], 
                encoding="gbk", 
                capture_output=True, 
                check=True 
            ) 
            # 解析输出：过滤无效行+去重 
            voices = [] 
            seen = set()  # 用于去重 
            for line in result.stdout.splitlines(): 
                line = line.strip() 
                # 过滤空行、SAPI 5:、重复行 
                if line and not line.startswith("Balabolka") and not line == "SAPI 5:": 
                    if line not in seen: 
                        seen.add(line) 
                        voices.append(line) 
            # 打印整理后的语音库 
            print("=== 系统可用语音库（去重后）===") 
            for i, voice in enumerate(voices): 
                print(f"{i+1}. {voice}") 
            return voices 
        except Exception as e: 
            print(f"获取语音库失败：{str(e)}") 
            return [] 

# ==================== 专用：使用Microsoft Xiaoxiao语音库 ==================== 
if __name__ == "__main__": 
    # 第一步：列出去重后的语音库（确认Microsoft Xiaoxiao存在） 
    voices = VoiceTools.list_balcon_voices() 

    # 第二步：用Microsoft Xiaoxiao播放语音 
    VoiceTools.balcon_tts( 
        text="你好！我是微软晓晓的语音，很高兴为你服务", 
        voice_name="Microsoft Xiaoxiao",  # 固定使用该语音库 
        # speed=110  # 可根据需求调整语速 
    ) 

    # 第三步：用Microsoft Xiaoxiao保存语音文件 
    # VoiceTools.balcon_tts( 
    #     text="这是使用微软晓晓语音保存的WAV音频文件", 
    #     save_to_file="xiaoxiao_output.wav",  # 自定义保存文件名 
    #     voice_name="Microsoft Xiaoxiao", 
    #     speed=110 
    # )