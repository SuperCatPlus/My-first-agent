#!/usr/bin/env python3
"""
本地大模型智能体Web服务器
"""

from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
import os
import sys
import logging
from config import config
from tool_registry import ToolRegistry
from agent_core import AgentCore
import json
import requests

# 获取当前文件目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 使用 config.py 的全局日志配置
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 配置session
app.secret_key = 'your-secret-key-change-this-in-production'  # 生产环境应从环境变量读取
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# 配置静态文件路径
# app.static_folder = os.path.join(current_dir, 'static')
# app.static_url_path = '/static'

# 配置模板路径
# app.template_folder = os.path.join(current_dir, 'static', 'chat')

# 全局智能体实例
agent_instance = None

# 初始化智能体
def initialize_agent():
    """初始化智能体"""
    global agent_instance
    
    if agent_instance is None:
        try:
            # 检查依赖
            check_dependencies()
            
            # 检查Ollama服务
            check_ollama_service()
            
            # 初始化工具注册表
            tool_registry = ToolRegistry(config)
            tool_registry.load_all()
            
            # 初始化智能体核心
            agent_instance = AgentCore(config, tool_registry)
            print("✅ 智能体初始化完成!")
            print(f"📊 使用模型: {config.MODEL_NAME}")
            print(f"🛠️  可用工具: {', '.join(tool_registry.implementations.keys())}")
        except Exception as e:
            print(f"❌ 初始化智能体失败: {e}")
            raise

def check_dependencies():
    """检查依赖包"""
    try:
        import pytz
        import yaml
        import requests
    except ImportError as e:
        print(f"❌ 缺少依赖包: {e}")
        print("请运行: pip install requests pyyaml pytz")
        sys.exit(1)

def check_ollama_service():
    """检查Ollama服务"""
    try:
        response = requests.get(f"{config.OLLAMA_API_BASE}/tags", timeout=5)
        if response.status_code != 200:
            print("❌ Ollama服务可能未运行或无法访问")
            print("请确保已启动Ollama: ollama serve")
            sys.exit(1)
    except Exception:
        print("❌ 无法连接到Ollama服务")
        print(f"请检查Ollama是否运行在 {config.OLLAMA_API_BASE}")
        sys.exit(1)

# 首页路由
@app.route('/')
def index():
    """首页"""
    return render_template('index.html', model_name=config.MODEL_NAME)

# 聊天API路由
@app.route('/api/chat', methods=['POST'])
def chat():
    """聊天API"""
    try:
        # 记录请求信息
        data = request.get_json()
        logger.info(f"请求体 (JSON): {data}")
        logger.info(f"Cookie: {dict(request.cookies)}")
        
        user_message = data.get('message', '')
        
        if not user_message:
            logger.warning("用户消息为空")
            return jsonify({"error": "请输入消息"}), 400
        
        # 确保智能体已初始化
        initialize_agent()
        
        # 直接处理消息（AI会自动检查终端状态）
        result = agent_instance.process_message(user_message)
        
        # 记录处理结果
        logger.info(f"处理结果: {result}")
        
        # 返回响应和终端命令
        return jsonify(result)
    except Exception as e:
        logger.error(f"处理请求时发生错误: {str(e)}", exc_info=True)
        return jsonify({"error": str(e), "terminal_commands": []}), 500

# 工具列表API路由
@app.route('/api/tools', methods=['GET'])
def get_tools():
    """获取可用工具列表"""
    try:
        # 确保智能体已初始化
        initialize_agent()
        
        # 获取工具列表
        tools = []
        for tool_name, tool_def in agent_instance.tool_registry.tools.items():
            tools.append({
                "name": tool_name,
                "description": tool_def.get('description', '')
            })
        
        return jsonify({"tools": tools})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 健康检查路由
@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({"status": "healthy", "model": config.MODEL_NAME})

# 终端状态查询路由（使用Cookie）
@app.route('/api/terminal/status', methods=['GET'])
def terminal_status():
    """查询终端状态（使用Cookie）"""
    try:
        # 从Cookie获取终端连接状态
        terminal_connected = request.cookies.get('terminal_connected', 'false')
        
        if terminal_connected == 'true':
            return jsonify({
                "status": "success",
                "connected": True,
                "message": "终端已连接"
            })
        else:
            return jsonify({
                "status": "success",
                "connected": False,
                "message": "终端未连接"
            })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    # 初始化智能体
    initialize_agent()
    
    # 启动Web服务器
    print(f"🚀 Web服务器启动在 http://localhost:28080")
    print(f"📊 使用模型: {config.MODEL_NAME}")
    print(f"🛠️  可用工具: {', '.join(agent_instance.tool_registry.implementations.keys())}")
    
    app.run(host='0.0.0.0', port=28080, debug=False)
