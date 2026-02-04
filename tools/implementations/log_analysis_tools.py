import re
from datetime import datetime
from typing import Dict, List, Optional
from .log_decorator import log_tool_call

# 全局正则表达式：适配GeoServer日志格式（syslog封装+中文月份）
PATTERN_GEOSERVER_CORE = re.compile(
    r"""
    (?P<day>\d{2})\s+
    (?P<mon_cn>\w+)\s+
    (?P<time>\d{2}:\d{2}:\d{2})\s+
    (?P<log_level>\w+)\s+
    \[(?P<module>[^\]]+)\]\s+-\s+
    (?P<client_ip>\d+\.\d+\.\d+\.\d+)\s+
    "?(?P<http_method>\w+)\s+(?P<request_uri>[^"\s]+)"?\s+
    (?:"(?P<user_agent>[^"]*)")?\s+
    (?:"(?P<referer>[^"]*)")?
    """,
    re.VERBOSE | re.IGNORECASE
)

# 安全特征库
THREAT_SIGNATURES = {
    "RCE_KEYWORDS": re.compile(r"(java\.lang\.Runtime|ProcessBuilder|getRuntime|exec|eval)", re.I),
    "SHELL_COMMANDS": re.compile(r"(wget|curl|chmod|chown|bash|sh\s+-c|python|perl|nc\s+|netcat)", re.I),
    "ENCODING_PATTERNS": re.compile(r"(base64|%[0-9a-f]{2})", re.I),
    "TRAVERSAL_PATTERNS": re.compile(r"(\.\./|\.\.\\)", re.I),
}

# 匹配耗时日志行：took Xms
PATTERN_RESPONSE_TIME = re.compile(r"took\s+(?P<response_time>\d+)ms")

# 匹配WFS业务详情：Request: getFeature/typeName等
PATTERN_WFS_BIZ = re.compile(
    r"Request:\s+(?P<geo_action>\w+)|typeName\[0\]\s+=\s+(?P<geo_layer>[^\n]+)|version\s+=\s+(?P<geo_version>[^\n]+)",
    re.IGNORECASE
)

# 需过滤的冗余日志关键词
FILTER_KEYWORDS = [
    "Headers:", "Accept: ", "Priority: ", "User-Agent: ", "Referer: ",
    "Connection: ", "Host: ", "Accept-Language: ", "Accept-Encoding: ",
    "Cookie: ", "about to encode JSON", "Request: getServiceInfo"
]

# IP过滤列表
FILTER_IP = ["127.0.0.1", "172.16.37.0"]

class SecurityEngine:
    @staticmethod
    def analyze(log_entry: dict) -> dict:
        """
        分析结构化日志，识别潜在威胁
        """
        threats = []
        payload = (log_entry.get("query_string") or "") + (log_entry.get("raw_log") or "")
        
        # 1. 检测 Java 注入特征
        if THREAT_SIGNATURES["RCE_KEYWORDS"].search(payload):
            threats.append("Critical: Java RCE Keyword Detected")
            
        # 2. 检测 危险系统命令
        if THREAT_SIGNATURES["SHELL_COMMANDS"].search(payload):
            threats.append("High: Shell Command Injection Attempt")
            
        # 3. 检测 目录穿越
        if THREAT_SIGNATURES["TRAVERSAL_PATTERNS"].search(payload):
            threats.append("Medium: Path Traversal Attempt")

        return {
            "is_threat": len(threats) > 0,
            "threat_level": "High" if len(threats) > 1 else ("Medium" if threats else "Low"),
            "threat_details": threats
        }

class GeoServerLogParser:
    def __init__(self):
        self.request_cache: Dict[str, Dict] = {}  # 请求缓存：聚合同一请求的发起/耗时日志
        self.parsed_results: List[Dict] = []      # 最终结构化结果

    def _filter_redundant(self, log_line: str) -> bool:
        """过滤冗余日志行，返回True=保留，False=丢弃"""
        log_line_strip = log_line.strip()
        if not log_line_strip:
            return False
        for keyword in FILTER_KEYWORDS:
            if log_line_strip.startswith(keyword):
                return False
        return True

    def _filter_ip(self, client_ip: str) -> bool:
        """
        过滤指定IP，返回True=保留（非过滤IP），False=丢弃（命中过滤IP）
        :param client_ip: 解析出的客户端IP
        """
        for ip_pattern in FILTER_IP:
            # 精确匹配（完整IP）或模糊匹配（IP段）
            if client_ip == ip_pattern or client_ip.startswith(ip_pattern):
                return False
        return True

    def _get_request_key(self, client_ip: str, request_uri: str) -> str:
        """生成请求唯一标识：用于聚合同一请求的发起/耗时日志"""
        return f"{client_ip}_{request_uri.split('?')[0]}_{request_uri[-20:]}"

    def _parse_wfs_biz(self, log_lines: List[str]) -> Dict:
        """从日志行中提取WFS业务核心字段"""
        wfs_biz = {"geo_service": "WFS", "geo_action": "", "geo_layer": "", "geo_version": "1.0.0"}
        for line in log_lines:
            match = PATTERN_WFS_BIZ.search(line)
            if match:
                if match.group("geo_action"):
                    wfs_biz["geo_action"] = match.group("geo_action").strip()
                if match.group("geo_layer"):
                    # 清洗图层名：{http://grain.safe}warehouse_live -> GrainSafe:warehouse_live
                    layer = match.group("geo_layer").strip().replace("{http://grain.safe}", "GrainSafe:")
                    wfs_biz["geo_layer"] = layer.replace("}", "")
                if match.group("geo_version"):
                    wfs_biz["geo_version"] = match.group("geo_version").strip()
        return wfs_biz

    def _judge_request_type(self, request_uri: str) -> str:
        """判断请求类型：WFS/STATIC/OTHER"""
        if "/wfs" in request_uri:
            return "WFS"
        elif any(s in request_uri for s in ["/tiles/", ".png", ".html", ".js", ".css"]):
            return "STATIC"
        else:
            return "OTHER"

    def parse_single_line(self, log_line: str, raw_log: Optional[str] = None) -> Optional[Dict]:
        """
        解析单条GeoServer日志行
        :param log_line: 清洗后的日志行
        :param raw_log: 原始日志行（可选，用于留存）
        :return: 结构化字典/None（未匹配）
        """
        match = PATTERN_GEOSERVER_CORE.search(log_line)
        if not match:
            return None

        # 提取客户端IP并校验
        client_ip = match.group("client_ip").strip()
        if not self._filter_ip(client_ip):
            # 命中过滤IP → 直接返回None，不解析后续内容
            return None

        # 基础字段提取
        month_map = {
            "1月": "01", "2月": "02", "3月": "03", "4月": "04",
            "5月": "05", "6月": "06", "7月": "07", "8月": "08",
            "9月": "09", "10月": "10", "11月": "11", "12月": "12"
        }

        day_str = match.group('day')
        mon_cn = match.group('mon_cn')
        time_str = match.group('time')

        # 组合正确的日期字符串
        current_year = "2026"
        month_str = month_map.get(mon_cn, "01") # 默认1月防止报错

        try:
            # 构造格式：2026-02-03 10:44:25
            formatted_date = f"{current_year}-{month_str}-{day_str} {time_str}"
            log_time = datetime.strptime(formatted_date, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            # 如果解析失败，回退到原始字符串
            log_time = f"{current_year}-{mon_cn}-{day_str} {time_str}"

        http_method = match.group("http_method").strip()
        request_uri = match.group("request_uri").strip()
        request_path = request_uri.split('?')[0] if '?' in request_uri else request_uri
        query_string = request_uri.split('?')[1] if '?' in request_uri else ""

        # 提取响应时间
        response_time_ms = 0
        rt_match = PATTERN_RESPONSE_TIME.search(log_line)
        if rt_match:
            response_time_ms = int(rt_match.group("response_time"))

        # 生成请求唯一标识
        request_key = self._get_request_key(client_ip, request_uri)

        # 基础结构化字典（轻量化安全审计字段）
        structured = {
            "timestamp": log_time,          # 标准化时间戳
            "client_ip": client_ip,         # 客户端IP
            "http_method": http_method,     # 请求方法
            "request_path": request_path,   # 请求路径
            "query_string": query_string,   # 查询参数
            "request_type": self._judge_request_type(request_uri),  # 请求类型
            "user_agent": match.group("user_agent").strip() if match.group("user_agent") else "",
            "referer": match.group("referer").strip() if match.group("referer") else "",
            "log_level": match.group("log_level").strip(),
            "log_module": match.group("module").strip(),
            "response_time_ms": response_time_ms,  # 响应时间
            "geo_service": "",              # GIS服务类型
            "geo_action": "",               # GIS操作
            "geo_layer": "",                # GIS图层名
            "geo_version": "",              # GIS版本
            "raw_log": raw_log or log_line  # 原始日志
        }

        # --- 集成安全分析引擎 ---
        security_report = SecurityEngine.analyze(structured)
        structured.update(security_report) # 将安全检查结果合并到日志中

        # 补充WFS业务字段
        if structured["request_type"] == "WFS":
            wfs_biz = self._parse_wfs_biz([log_line])
            structured.update(wfs_biz)
        # 静态资源补充字段
        elif structured["request_type"] == "STATIC":
            structured["geo_service"] = "STATIC"
            structured["geo_action"] = "STATIC_RESOURCE"

        # 聚合请求：缓存无响应时间的请求，补全后加入最终结果
        if response_time_ms == 0:
            self.request_cache[request_key] = structured
        else:
            if request_key in self.request_cache:
                # 补全缓存请求的响应时间，加入最终结果
                cached = self.request_cache.pop(request_key)
                cached["response_time_ms"] = response_time_ms
                self.parsed_results.append(cached)
            else:
                self.parsed_results.append(structured)

        return structured

    def parse_logs(self, log_content: str) -> List[Dict]:
        """
        解析批量日志内容（文件/流读取的字符串）
        :param log_content: 原始日志内容（按行分隔）
        :return: 最终结构化日志列表
        """
        self.request_cache.clear()
        self.parsed_results.clear()

        # 按行解析
        for line in log_content.splitlines():
            line_strip = line.strip()
            # 第一步：过滤冗余日志
            if not self._filter_redundant(line_strip):
                continue
            # 第二步：解析核心日志行（IP过滤在parse_single_line内完成）
            self.parse_single_line(line_strip, raw_log=line)

        # 缓存中剩余的无耗时日志，加入最终结果（兜底）
        self.parsed_results.extend(self.request_cache.values())
        self.request_cache.clear()

        return self.parsed_results


class LogAnalysisTools:
    """日志分析工具类"""
    
    @staticmethod
    @log_tool_call
    def analyze_geoserver_log(log_file_path=None):
        """
        分析GeoServer日志文件，识别潜在威胁
        
        参数:
            log_file_path (str): 日志文件路径，默认使用geoserver.log.1
        
        返回:
            dict: 分析结果，包含威胁统计和详细信息
        """
        try:
            # 使用默认日志文件路径
            if log_file_path is None:
                log_file_path = "geoserver.log.1"
            
            # 初始化解析器
            parser = GeoServerLogParser()
            
            # 读取文件内容
            with open(log_file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 执行解析
            results = parser.parse_logs(content)

            # 筛选出所有威胁请求，并整理成易读的结构
            threat_count = 0
            threat_entries = []  # 存储所有威胁请求的结构化数据
            for entry in results:
                if entry.get("is_threat"):
                    threat_count += 1
                    # 整理字段为JSON友好的结构
                    threat_item = {
                        "threat_level": entry["threat_level"],
                        "timestamp": entry["timestamp"],
                        "client_ip": entry["client_ip"],
                        "threat_details": entry["threat_details"],
                        "raw_payload": entry["raw_log"].strip()[:100],  # 截取前100字符
                        "full_raw_log": entry["raw_log"],  # 保留完整原始日志
                        "http_method": entry["http_method"],
                        "request_path": entry["request_path"],
                        "query_string": entry["query_string"]
                    }
                    threat_entries.append(threat_item)

            # 封装成更易读的结构，包含统计信息 + 威胁列表
            threat_report = {
                "audit_summary": {
                    "total_processed_lines": len(content.splitlines()),
                    "total_valid_requests": len(results),
                    "total_threat_requests": threat_count
                },
                "threat_details": threat_entries
            }
            
            return threat_report
            
        except FileNotFoundError:
            return {
                "error": f"日志文件不存在: {log_file_path}",
                "audit_summary": {
                    "total_processed_lines": 0,
                    "total_valid_requests": 0,
                    "total_threat_requests": 0
                },
                "threat_details": []
            }
        except Exception as e:
            return {
                "error": f"分析失败: {str(e)}",
                "audit_summary": {
                    "total_processed_lines": 0,
                    "total_valid_requests": 0,
                    "total_threat_requests": 0
                },
                "threat_details": []
            }
    
    @staticmethod
    @log_tool_call
    def analyze_geoserver_log_summarize(log_file_path=None):
        """
        分析GeoServer日志文件，返回威胁摘要
        
        参数:
            log_file_path (str): 日志文件路径，默认使用geoserver.log.1
        
        返回:
            dict: 分析摘要，包含威胁统计和关键信息
        """
        try:
            # 调用完整分析方法
            full_report = LogAnalysisTools.analyze_geoserver_log(log_file_path)
            
            # 如果有错误，直接返回
            if "error" in full_report:
                return full_report
            
            # 生成摘要
            summary = {
                "audit_summary": full_report.get("audit_summary", {}),
                "top_threats": [],
                "threat_summary": ""
            }
            
            # 提取前5个威胁作为摘要
            threat_details = full_report.get("threat_details", [])
            top_threats = threat_details[:5]
            summary["top_threats"] = top_threats
            
            # 生成威胁摘要文本
            threat_count = summary["audit_summary"].get("total_threat_requests", 0)
            if threat_count > 0:
                summary["threat_summary"] = f"共检测到 {threat_count} 个潜在威胁。"
                if top_threats:
                    summary["threat_summary"] += " 前5个威胁如下："
            else:
                summary["threat_summary"] = "未检测到潜在威胁。"
            
            return summary
            
        except Exception as e:
            return {
                "error": f"分析失败: {str(e)}",
                "audit_summary": {
                    "total_processed_lines": 0,
                    "total_valid_requests": 0,
                    "total_threat_requests": 0
                },
                "top_threats": [],
                "threat_summary": ""
            }
