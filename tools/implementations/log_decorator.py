import logging
from functools import wraps

# 获取全局logger（复用config.py的日志配置）
logger = logging.getLogger(__name__)

def log_tool_call(func):
    """
    装饰器：记录工具函数的调用信息（入参、出参、调用时间、异常）
    """
    @wraps(func)  # 保留原函数的元信息（如函数名、文档字符串）
    def wrapper(*args, **kwargs):
        # 记录函数开始调用
        logger.info(f"工具函数 {func.__name__} 开始调用 | 入参: args={args}, kwargs={kwargs}")
        try:
            # 执行原函数
            result = func(*args, **kwargs)
            # 记录函数调用成功
            logger.info(f"工具函数 {func.__name__} 调用成功 | 出参: {result}")
            return result
        except Exception as e:
            # 记录函数调用异常
            logger.error(f"工具函数 {func.__name__} 调用失败 | 异常信息: {str(e)}", exc_info=True)
            raise  # 抛出异常，不影响上层逻辑处理
    return wrapper