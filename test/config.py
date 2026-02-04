# 配置文件：GeoServer日志分析器配置

# 需过滤的IP列表
# 支持两种格式：
# 1. 完整IP（如"127.0.0.1"）→ 精确匹配
# 2. IP段（如"172.16.37."）→ 模糊匹配（匹配该网段所有IP）
FILTER_IP = ["127.0.0.1", "172.16.37.0"]

# 日志文件路径
LOG_FILE_PATH = "geoserver.log.1"

# JSON输出路径
JSON_ALL_OUTPUT_PATH = "geoserver_audit_all.json"
JSON_THREAT_OUTPUT_PATH = "geoserver_audit_threats.json"
