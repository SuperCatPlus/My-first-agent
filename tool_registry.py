import json
import yaml
import importlib.util
from pathlib import Path
from typing import Dict, List, Any, Callable
import sys

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
    
    def load_tool_implementations(self) -> None:
        """加载所有工具实现"""
        implementations_dir = Path(self.config.TOOLS_IMPLEMENTATIONS_DIR)
        
        if not implementations_dir.exists():
            raise FileNotFoundError(f"工具实现目录不存在: {implementations_dir}")
        
        # 添加工具实现目录到Python路径
        sys.path.insert(0, str(implementations_dir.parent))
        
        try:
            # 动态导入工具实现模块
            for py_file in implementations_dir.glob("*.py"):
                if py_file.name == "__init__.py":
                    continue
                    
                module_name = py_file.stem
                try:
                    # 导入模块
                    spec = importlib.util.spec_from_file_location(
                        module_name, 
                        py_file
                    )
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # 查找并注册工具类
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if isinstance(attr, type) and hasattr(attr, '__module__'):
                            # 获取工具类的所有静态方法
                            for method_name in dir(attr):
                                method = getattr(attr, method_name)
                                if (callable(method) and 
                                    not method_name.startswith('_') and
                                    method_name in self.tools):
                                    
                                    self.implementations[method_name] = method
                                    print(f"已加载工具实现: {method_name}")
                                    
                except Exception as e:
                    print(f"加载工具实现模块失败 {module_name}: {e}")
                    
        finally:
            # 恢复Python路径
            if str(implementations_dir.parent) in sys.path:
                sys.path.remove(str(implementations_dir.parent))
    
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
        
        return tool_func(**kwargs)
    
    def load_all(self) -> None:
        """加载所有工具"""
        self.load_tool_definitions()
        self.load_tool_implementations()
        
        print(f"共加载 {len(self.tools)} 个工具定义")
        print(f"共加载 {len(self.implementations)} 个工具实现")
