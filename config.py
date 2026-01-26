import os
import logging
from typing import Dict, Any


# 全局日志配置（只初始化一次）
logging.basicConfig(
    filename='API.log',  
    filemode='a',  
    level=logging.INFO,
    format='%(asctime)s - %(module)s - %(funcName)s - %(levelname)s: %(message)s',  
    datefmt='%Y-%m-%d %H:%M:%S',
    encoding='utf-8'
)


class Config:
    """配置类"""

    # Ollama API配置
    OLLAMA_API_BASE = "http://localhost:11434/api"
    MODEL_NAME = "qwen3:14b"  # 可根据实际情况修改为qwen、mistral等
    
    # 工具配置
    TOOLS_DEFINITIONS_DIR = "tools/definitions"
    TOOLS_IMPLEMENTATIONS_DIR = "tools/implementations"
    
    # 系统提示词文件
    SYSTEM_PROMPT_FILE = "prompts/system_prompt.yaml"
    
    # 模型参数
    MODEL_PARAMS = {
        "temperature": 0.7,
        "top_p": 0.9,
        "max_tokens": 1000,
        "stream": False
    }
    
    @classmethod
    def get_ollama_endpoint(cls) -> str:
        """获取Ollama API端点"""
        return f"{cls.OLLAMA_API_BASE}/generate"
    
    @classmethod
    def get_chat_endpoint(cls) -> str:
        """获取聊天API端点"""
        return f"{cls.OLLAMA_API_BASE}/chat"
    
    @classmethod
    def get_model_config(cls) -> Dict[str, Any]:
        """获取模型配置"""
        return {
            "model": cls.MODEL_NAME,
            **cls.MODEL_PARAMS
        }

# 单例配置实例
config = Config()
