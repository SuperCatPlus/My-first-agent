#!/usr/bin/env python3
"""
测试HTTP工具的日志记录功能
"""

from config import config
from tool_registry import ToolRegistry

def test_http_logging():
    """测试HTTP工具的日志记录"""
    print("测试HTTP工具的日志记录功能...")
    
    try:
        # 初始化工具注册表
        tool_registry = ToolRegistry(config)
        tool_registry.load_all()
        
        print("\n执行http_request工具...")
        # 执行http_request工具
        result = tool_registry.execute_tool(
            "http_request",
            url="http://localhost:8000/api/Alarm",
            method="GET"
        )
        print(f"执行结果: {result}")
        
        print("\n执行get_log_last_lines工具...")
        # 执行get_log_last_lines工具
        result = tool_registry.execute_tool(
            "get_log_last_lines",
            lines_count=10
        )
        print(f"执行结果: {result}")
        
        print("\n测试完成！请查看Function.log文件确认日志记录是否成功。")
        
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    test_http_logging()
