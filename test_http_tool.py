#!/usr/bin/env python3
"""
测试HTTP请求工具
"""

from config import config
from tool_registry import ToolRegistry

def test_http_request():
    """测试HTTP请求工具"""
    print("测试HTTP请求工具...")
    
    try:
        # 初始化工具注册表
        tool_registry = ToolRegistry(config)
        tool_registry.load_all()
        
        print(f"可用工具: {list(tool_registry.implementations.keys())}")
        
        # 测试1: 发送GET请求到本地API
        print("\n测试1: 发送GET请求到本地API")
        try:
            result = tool_registry.execute_tool(
                "http_request",
                url="http://localhost:8000/api/Alarm",
                method="GET",
                timeout=10
            )
            print(f"请求结果: {result}")
        except Exception as e:
            print(f"测试1失败: {e}")
        
        # 测试2: 发送GET请求到一个公共API（如果本地API不可用）
        print("\n测试2: 发送GET请求到公共API")
        try:
            result = tool_registry.execute_tool(
                "http_request",
                url="https://api.github.com/users/octocat",
                method="GET",
                timeout=10
            )
            print(f"状态码: {result.get('status_code')}")
            print(f"响应内容长度: {len(result.get('text', ''))}")
            print("测试2成功!")
        except Exception as e:
            print(f"测试2失败: {e}")
        
    except Exception as e:
        print(f"初始化失败: {e}")

if __name__ == "__main__":
    test_http_request()
