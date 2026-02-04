#!/usr/bin/env python3
"""
本地大模型智能体主程序
"""

import sys
import argparse
from config import config
from tool_registry import ToolRegistry
from agent_core import AgentCore

import base_init
from colorama import init as colorama_init, Fore, Style
colorama_init(autoreset=True)   #字体

def initialize_agent(check_ollama=True) -> AgentCore:
    """初始化智能体"""
    print(Fore.BLUE + "正在初始化智能体...")
    
    # 检查依赖
    try:
        import pytz
        import yaml
        import requests
    except ImportError as e:
        print(f"❌ 缺少依赖包: {e}")
        print("请运行: pip install requests pyyaml pytz")
        sys.exit(1)
    
    # 检查Ollama服务
    if check_ollama:
        try:
            response = requests.get(f"{config.OLLAMA_API_BASE}/tags", timeout=5)
            if response.status_code != 200:
                print("❌ Ollama服务可能未运行或无法访问")
                print("请确保已启动Ollama: ollama serve")
                sys.exit(1)
        except:
            print("❌ 无法连接到Ollama服务")
            print("请检查Ollama是否运行在 http://localhost:11434")
            sys.exit(1)
    
    # 初始化工具注册表
    try:
        tool_registry = ToolRegistry(config)
        tool_registry.load_all()
    except Exception as e:
        print(f"❌ 初始化工具注册表失败: {e}")
        sys.exit(1)
    
    # 初始化智能体核心
    try:
        agent = AgentCore(config, tool_registry)
    except Exception as e:
        print(f"❌ 初始化智能体核心失败: {e}")
        sys.exit(1)
    
    print("✅ 智能体初始化完成!")
    print(f"📊 使用模型: {config.MODEL_NAME}")
    print(f"🛠️  可用工具: {', '.join(tool_registry.implementations.keys())}")
    
    return agent

def interactive_mode(agent: AgentCore):
    """交互模式"""
    print("\n" + "="*50)
    print(Fore.GREEN + "智能体已就绪！")
    print(f"模型: {config.MODEL_NAME}")
    print("输入 '退出' 或 'quit' 结束对话")
    print("输入 '清除' 或 'clear' 清除对话历史")
    print("="*50 + "\n")
    
    while True:
        try:
            user_input = input("\n👤 用户: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['退出', 'quit', 'exit']:
                print("\n🤖 助手: 再见！")
                break
            
            if user_input.lower() in ['清除', 'clear']:
                agent.clear_history()
                print("🗑️ 对话历史已清除")
                continue
            
            # 处理用户消息
            print("\n🤖 助手:", end="", flush=True)
            response = agent.process_message(user_input)
            
            # 美化输出
            print(f" {response}")
            print("-"*50)
            
        except KeyboardInterrupt:
            print("\n\n⚠️  程序被用户中断")
            break
        except Exception as e:
            print(f"\n❌ 错误: {e}")

def single_query_mode(agent: AgentCore, query: str):
    """单次查询模式"""
    try:
        response = agent.process_message(query)
        print(f"📝 查询: {query}")
        print(f"🤖 回答: {response}")
    except Exception as e:
        print(f"❌ 处理查询时出错: {e}")

def main():
    parser = argparse.ArgumentParser(description="本地大模型智能体")
    parser.add_argument("--query", "-q", help="单次查询模式，直接输入问题")
    parser.add_argument("--model", "-m", help="指定模型名称，覆盖配置文件")
    parser.add_argument("--list-tools", "-l", action="store_true", 
                        help="列出可用工具")
    parser.add_argument("--test-tools", "-t", action="store_true", 
                        help="测试工具加载（不连接Ollama服务）")
    
    args = parser.parse_args()
    
    # 如果指定了模型，更新配置
    if args.model:
        config.MODEL_NAME = args.model
    
    try:
        # 测试工具模式不检查Ollama服务
        if args.test_tools:
            agent = initialize_agent(check_ollama=False)
            print("\n🛠️  可用工具列表:")
            for i, (tool_name, tool_func) in enumerate(agent.tool_registry.implementations.items(), 1):
                tool_def = agent.tool_registry.tools.get(tool_name, {})
                description = tool_def.get('description', '无描述')
                print(f"  {i}. {tool_name}: {description}")
            return
        
        agent = initialize_agent()
        
        # 如果指定了列出工具，显示后退出
        if args.list_tools:
            print("\n🛠️  可用工具列表:")
            for i, (tool_name, tool_func) in enumerate(agent.tool_registry.implementations.items(), 1):
                tool_def = agent.tool_registry.tools.get(tool_name, {})
                description = tool_def.get('description', '无描述')
                print(f"  {i}. {tool_name}: {description}")
            return
        
        if args.query:
            single_query_mode(agent, args.query)
        else:
            interactive_mode(agent)
            
    except Exception as e:
        print(f"❌ 启动智能体失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()