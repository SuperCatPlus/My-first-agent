import json
import datetime
import pytz
from typing import Dict, Any, Optional
import requests

from . import log_tool_call

class BaseTools:
    """基础工具实现类"""
    
    @staticmethod
    @log_tool_call
    def get_current_time(timezone: Optional[str] = None, format: Optional[str] = None) -> Dict[str, Any]:
        """
        获取当前时间
        
        Args:
            timezone: 时区，例如：Asia/Shanghai
            format: 时间格式，例如：%Y-%m-%d %H:%M:%S
            
        Returns:
            包含时间信息的字典
        """
        try:
            now = datetime.datetime.now()
            
            # 应用时区
            if timezone:
                try:
                    target_tz = pytz.timezone(timezone)
                    now_utc = pytz.utc.localize(now)  # 将当前时间视为UTC
                    now = now_utc.astimezone(target_tz)
                except Exception as tz_error:
                    return {
                        "error": f"时区错误: {str(tz_error)}",
                        "current_time_utc": now.strftime("%Y-%m-%d %H:%M:%S"),
                        "timezone": "UTC"
                    }
            
            # 应用格式
            if format:
                formatted_time = now.strftime(format)
            else:
                formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")
            
            return {
                "current_time": formatted_time,
                "timestamp": now.isoformat(),
                "timezone": timezone if timezone else "local",
                "year": now.year,
                "month": now.month,
                "day": now.day,
                "hour": now.hour,
                "minute": now.minute,
                "second": now.second,
                "weekday": now.strftime("%A"),
                "success": True
            }
            
        except Exception as e:
            # 如果格式错误，返回简单时间
            current_time = datetime.datetime.now()
            return {
                "current_time": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                "error": f"格式化错误: {str(e)}",
                "success": False
            }
    
    # search_internet 方法保持不变...
