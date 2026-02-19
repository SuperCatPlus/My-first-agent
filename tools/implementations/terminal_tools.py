from typing import Dict, Any
from . import log_tool_call
import sys
import os
import requests
import logging

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 配置日志
logger = logging.getLogger(__name__)

class TerminalTools:
    """终端工具实现类，用于向WebSSH终端发送命令"""
    

    
    @staticmethod
    @log_tool_call
    def send_terminal_command(command: str, speed: int = 30, enter: bool = True) -> Dict[str, Any]:
        """
        向WebSSH终端发送命令并执行
        
        Args:
            command: 要执行的命令，例如：ls -la, cat file.txt
            speed: 打字速度（毫秒/字符），默认为30ms
            enter: 是否自动按回车键执行命令，默认为true
            
        Returns:
            包含执行结果的字典
        """
        return {
            "success": True,
            "message": f"命令已发送到终端: {command}",
            "command": command,
            "speed": speed,
            "enter": enter
        }
    
    @staticmethod
    @log_tool_call
    def send_terminal_key(key: str) -> Dict[str, Any]:
        """
        向WebSSH终端发送特殊按键
        
        Args:
            key: 按键名称，支持：Enter, Ctrl+C, Ctrl+D, Ctrl+Z
            
        Returns:
            包含执行结果的字典
        """
        return {
            "success": True,
            "message": f"按键已发送到终端: {key}",
            "key": key
        }