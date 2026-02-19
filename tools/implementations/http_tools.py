import requests
import json
from config import config
from .log_decorator import log_tool_call

class HttpTools:
    """HTTP请求工具类"""
    
    @staticmethod
    @log_tool_call
    def http_request(url, method="GET", headers=None, data=None, params=None, timeout=30):
        """
        发送HTTP请求到指定的API接口
        
        Args:
            url (str): 请求的URL地址
            method (str): HTTP请求方法，默认为GET
            headers (dict): 请求头信息
            data (dict): 请求体数据
            params (dict): URL查询参数
            timeout (int): 请求超时时间（秒），默认为30
        
        返回:
            dict: 请求结果，包含状态码、响应内容等信息
        """
        try:
            # 构建请求参数
            request_kwargs = {
                "timeout": timeout
            }
            
            # 添加请求头
            if headers:
                request_kwargs["headers"] = headers
            
            # 添加URL查询参数
            if params:
                request_kwargs["params"] = params
            
            # 添加请求体数据
            if data:
                # 如果Content-Type是application/json，则自动序列化
                if headers and headers.get("Content-Type") == "application/json":
                    request_kwargs["json"] = data
                else:
                    request_kwargs["data"] = data
            
            # 根据请求方法发送请求
            method = method.upper()
            if method == "GET":
                response = requests.get(url, **request_kwargs)
            elif method == "POST":
                response = requests.post(url, **request_kwargs)
            elif method == "PUT":
                response = requests.put(url, **request_kwargs)
            elif method == "DELETE":
                response = requests.delete(url, **request_kwargs)
            elif method == "PATCH":
                response = requests.patch(url, **request_kwargs)
            elif method == "HEAD":
                response = requests.head(url, **request_kwargs)
            elif method == "OPTIONS":
                response = requests.options(url, **request_kwargs)
            else:
                raise ValueError(f"不支持的HTTP方法: {method}")
            
            # 处理响应
            response_data = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "text": response.text
            }
            
            # 尝试解析JSON响应
            try:
                response_data["json"] = response.json()
            except json.JSONDecodeError:
                response_data["json"] = None
            
            return response_data
            
        except requests.exceptions.RequestException as e:
            return {
                "error": f"请求失败: {str(e)}",
                "status_code": None
            }
        except Exception as e:
            return {
                "error": f"未知错误: {str(e)}",
                "status_code": None
            }
    
    @staticmethod
    @log_tool_call
    def get_log_last_lines(lines_count=None):
        """
        调用/api/get-log-last-lines接口获取日志最后几行，用于查看是否有渗透痕迹
        
        Args:
            lines_count (int): 获取的日志行数，可不填，默认50行
        
        返回:
            dict: 请求结果，包含状态码、响应内容等信息
        """
        base_url = f"{config.BACKEND_API_BASE}/api/get-log-last-lines"
        params = {}
        
        if lines_count is not None:
            params["lines_count"] = lines_count
        
        return HttpTools.http_request(base_url, method="GET", params=params)
    
    @staticmethod
    @log_tool_call
    def analyze_log_for_intrusion(log_data):
        """
        分析日志数据，寻找渗透痕迹
        
        参数:
            log_data (str or dict): 日志数据，可以是字符串或包含text字段的字典
        
        返回:
            dict: 分析结果，包含是否检测到渗透痕迹以及具体的痕迹信息
        """
        # 提取日志文本
        if isinstance(log_data, dict):
            log_text = log_data.get("text", "")
        else:
            log_text = str(log_data)
        
        # 定义常见的渗透攻击模式
        intrusion_patterns = {
            "sql_injection": [
                "' OR '1'='1'",
                "UNION SELECT",
                "DROP TABLE",
                "INSERT INTO",
                "UPDATE.*SET",
                "DELETE FROM",
                "EXEC xp_",
                "1=1",
                "OR 1=1",
                "AND 1=0"
            ],
            "xss": [
                "<script>",
                "javascript:",
                "onerror=",
                "onload=",
                "onclick=",
                "<iframe>",
                "<img src=x onerror=",
                "alert("
            ],
            "sensitive_files": [
                "/etc/passwd",
                "/etc/shadow",
                ".env",
                "config.php",
                "web.config",
                "appsettings.json",
                "database.yml"
            ],
            "command_injection": [
                "; ls",
                "| cat",
                "&& echo",
                "; ping",
                "| ping",
                "&& ping",
                "`id`",
                "$(id)"
            ],
            "path_traversal": [
                "../",
                "..\\",
                "%2e%2e%2f",
                "%2e%2e%5c"
            ],
            "unusual_requests": [
                "404 Not Found",
                "500 Internal Server Error",
                "403 Forbidden",
                "401 Unauthorized"
            ]
        }
        
        # 检测渗透痕迹
        detected_intrusions = []
        
        for pattern_type, patterns in intrusion_patterns.items():
            for pattern in patterns:
                if pattern.lower() in log_text.lower():
                    detected_intrusions.append({
                        "type": pattern_type,
                        "pattern": pattern
                    })
        
        # 分析结果
        result = {
            "has_intrusion": len(detected_intrusions) > 0,
            "intrusions": detected_intrusions,
            "total_intrusions": len(detected_intrusions),
            "log_sample": log_text[:1000]  # 提供日志样本，最多1000字符
        }
        
        return result