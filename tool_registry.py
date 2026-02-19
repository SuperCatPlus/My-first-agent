import json
import yaml
import importlib.util
from pathlib import Path
from typing import Dict, List, Any, Callable
import sys
import time
import random

from colorama import init as colorama_init, Fore, Style
colorama_init(autoreset=True) # 字体

class ToolRegistry:
    """工具注册表，负责加载工具定义和实现"""
    
    def __init__(self, config):
        self.config = config
        self.tools = {}  # 工具定义
        self.implementations = {}  # 工具实现
        
    def load_tool_definitions(self) -> None:
        """加载所有工具定义"""
        definitions_dir = Path(self.config.TOOLS_DEFINITIONS_DIR)
        
        if not definitions_dir.exists():
            raise FileNotFoundError(f"工具定义目录不存在: {definitions_dir}")
        
        for json_file in definitions_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                if "tools" in data:
                    for tool_def in data["tools"]:
                        tool_name = tool_def.get("name")
                        if tool_name:
                            self.tools[tool_name] = tool_def
                            print(f"已加载工具定义: {tool_name}")
                            
                
            except Exception as e:
                print(f"加载工具定义文件失败 {json_file}: {e}")
        print(f"====--====")

    def load_tool_implementations(self) -> None:
        """加载所有工具实现"""
        import sys
        from pathlib import Path
        
        # 获取项目根目录
        project_root = Path(__file__).parent.parent
        
        # 将项目根目录添加到 sys.path
        sys.path.insert(0, str(project_root))
        
        try:
            # 导入 tools.implementations 包
            import tools.implementations as tools_impl
            
            # 从包中获取所有模块
            import pkgutil
            import inspect
            
            for _, module_name, is_pkg in pkgutil.iter_modules(tools_impl.__path__):
                if not is_pkg and module_name != "__pycache__":
                    try:
                        module = __import__(f"tools.implementations.{module_name}", fromlist=[""])
                        
                        # 查找并注册工具类
                        for name, obj in inspect.getmembers(module):
                            if inspect.isclass(obj):
                                # 检查是否为工具类
                                for method_name in dir(obj):
                                    if (not method_name.startswith('_') and 
                                        method_name in self.tools):
                                        method = getattr(obj, method_name)
                                        if callable(method):
                                            self.implementations[method_name] = method
                                            
                                            print(Fore.CYAN + f"已加载工具实现: {method_name}")
                                            # time.sleep(random.uniform(0.2, 1))
                                            
                    except Exception as e:
                        print(f"加载工具模块失败 {module_name}: {e}")
                        
        except Exception as e:
            print(f"导入工具包失败: {e}")
        finally:
            # 清理 sys.path
            if str(project_root) in sys.path:
                sys.path.remove(str(project_root))



    def get_tool(self, tool_name: str) -> Callable:
        """获取工具实现函数"""
        return self.implementations.get(tool_name)
    
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """获取所有工具定义"""
        return list(self.tools.values())
    
    def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """执行工具"""
        tool_func = self.get_tool(tool_name)
        if not tool_func:
            raise ValueError(f"工具未找到: {tool_name}")
        
        # 检查是否是异步函数
        import inspect
        import asyncio
        
        # 打印调试信息
        print(f"执行工具: {tool_name}")
        print(f"工具函数: {tool_func}")
        print(f"是否为协程函数: {inspect.iscoroutinefunction(tool_func)}")
        
        if inspect.iscoroutinefunction(tool_func):
            # 异步函数需要在事件循环中执行
            try:
                result = asyncio.run(tool_func(**kwargs))
                print(f"异步工具执行结果: {result}")
                return result
            except Exception as e:
                print(f"执行异步工具失败: {e}")
                raise
        else:
            # 同步函数直接执行
            try:
                result = tool_func(**kwargs)
                print(f"同步工具执行结果: {result}")
                return result
            except Exception as e:
                print(f"执行同步工具失败: {e}")
                raise
    
    def load_all(self) -> None:
        """加载所有工具"""
        self.load_tool_definitions()
        self.load_tool_implementations()

        print(f"共加载 {len(self.tools)} 个工具定义")
        print(Fore.YELLOW + f"共加载 {len(self.implementations)} 个工具实现")