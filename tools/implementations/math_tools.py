import math
from typing import Dict, Any
from .log_decorator import log_tool_call

class MathTools:
    """数学工具实现类"""
    
    @staticmethod
    @log_tool_call
    def calculate(expression: str) -> Dict[str, Any]:
        """
        计算数学表达式
        
        Args:
            expression: 数学表达式
            
        Returns:
            计算结果
        """
        try:
            # 安全地计算表达式
            allowed_names = {
                k: v for k, v in math.__dict__.items() 
                if not k.startswith("__")
            }
            
            # 自定义的安全eval函数
            def safe_eval(expr, namespace):
                code = compile(expr, "<string>", "eval")
                for name in code.co_names:
                    if name not in namespace:
                        raise NameError(f"使用未授权的名称: {name}")
                return eval(code, {"__builtins__": {}}, namespace)
            
            result = safe_eval(expression, allowed_names)
            
            return {
                "expression": expression,
                "result": result,
                "type": type(result).__name__,
                "success": True
            }
        except Exception as e:
            return {
                "expression": expression,
                "error": str(e),
                "success": False
            }
    
    @staticmethod
    def greet_user(name: str) -> Dict[str, str]:
        """
        问候用户
        
        Args:
            name: 用户姓名
            
        Returns:
            问候语
        """
        import datetime
        hour = datetime.datetime.now().hour
        
        if 5 <= hour < 12:
            greeting = "早上好"
        elif 12 <= hour < 14:
            greeting = "中午好"
        elif 14 <= hour < 18:
            greeting = "下午好"
        elif 18 <= hour < 22:
            greeting = "晚上好"
        else:
            greeting = "夜深了"
        
        return {
            "greeting": f"{greeting}，{name}！",
            "timestamp": datetime.datetime.now().isoformat()
        }
