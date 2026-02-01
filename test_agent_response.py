#!/usr/bin/env python3
"""
测试智能体的完整响应，包括工具调用部分
"""

from config import config
from agent_core import AgentCore
from tool_registry import ToolRegistry

def test_agent_response():
    """测试智能体的完整响应"""
    print("测试智能体的完整响应...")
    
    try:
        # 初始化智能体
        tool_registry = ToolRegistry(config)
        tool_registry.load_all()
        
        agent = AgentCore(config, tool_registry)
        
        # 测试查询
        user_input = "更新报警值为20"
        print(f"用户输入: {user_input}")
        
        # 构建消息历史
        messages = [
            {"role": "system", "content": agent.system_prompt},
            {"role": "user", "content": user_input}
        ]
        
        # 调用Ollama API获取原始响应
        response = agent._call_ollama(messages)
        assistant_message = response.get("message", {}).get("content", "")
        
        print(f"\n智能体原始响应:")
        print(assistant_message)
        
        # 提取工具调用
        tool_call = agent._extract_tool_call(assistant_message)
        print(f"\n提取的工具调用:")
        print(tool_call)
        
        if tool_call:
            print(f"\n工具名称: {tool_call.get('name')}")
            print(f"工具参数: {tool_call.get('parameters')}")
        
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    test_agent_response()
