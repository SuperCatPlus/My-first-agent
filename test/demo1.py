# import json
import datetime
from typing import Dict, Any, Optional
# import requests


def get_current_time(timezone: Optional[str] = None, format: Optional[str] = None) -> str:
        """
        获取当前时间
        
        Args:
            timezone: 时区
            format: 时间格式
            
        Returns:
            格式化后的时间字符串
        """
        try:
            if timezone:
                import pytz
                tz = pytz.timezone(timezone)
                current_time = datetime.datetime.now(tz)
            else:
                current_time = datetime.datetime.now()
            
            if format:
                return current_time.strftime(format)
            else:
                return current_time.strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            return f"获取时间失败: {str(e)}"

print(get_current_time())