# 本地大模型智能体

基于 Ollama 部署的本地大模型智能体，支持灵活的工具调用能力，可扩展、易配置，适配多种本地大模型。

## 🌟 核心特性
- 🤖 适配 Ollama 生态：支持 qwen、mistral、llama 等主流本地大模型
- 🔧 可扩展工具系统：工具定义与实现分离，轻松新增自定义工具
- 💬 交互式对话：支持多轮对话、历史记录管理
- ⚡ 高效工具调用：自动解析模型响应并执行对应工具，返回结构化结果
- 📝 可配置化：通过配置文件灵活调整模型参数、工具路径等
- 🎤 智能语音播报：短文本自动发声，长文本不发声，提升用户体验
- 🌐 HTTP请求工具：支持发送GET、POST等HTTP请求到指定API接口
- 📋 API列表管理：限制模型只能使用预定义的API列表，确保安全可控
- 🔍 日志分析功能：调用/api/get-log-last-lines接口查看日志，检测渗透痕迹

## 📋 目录结构
```
My_agent_project/
├── tools/                      # 工具模块
│   ├── definitions/            # 工具定义（JSON格式，描述工具元信息）
│   │   ├── base_tools.json     # 基础工具（时间、网络）
│   │   ├── test_tools.json     # 测试工具
│   │   ├── math_tools.json     # 数学工具
│   │   ├── voice_tools.json    # 语音工具
│   │   └── http_tools.json     # HTTP请求工具
│   │
│   └── implementations/        # 工具实现（Python类，对应具体逻辑）
│       ├── __init__.py
│       ├── base_tools.py       # 基础工具实现（获取时间、网络搜索）
│       ├── math_tools.py       # 数学工具实现（计算、问候）
│       ├── voice_tools.py      # 语音工具实现（文字转语音）
│       └── http_tools.py       # HTTP请求工具实现（发送HTTP请求）
│
├── api_config.json              # API列表配置（限制模型可使用的API）
│ 
├── prompts/                    # 提示词目录
│   └── system_prompt.yaml      # 系统提示词（定义工具调用规则）
│
├── utils_bin/                  # 工具二进制文件
│   └── balcon/                 # Balcon TTS工具（离线语音播放）
│       ├── balcon.exe          # Balcon主程序
│       ├── SoundTouch.dll      # 依赖库
│       ├── chsdet.dll          # 依赖库
│       ├── lame.exe            # 依赖库
│       ├── lame_enc.dll        # 依赖库
│       └── libsamplerate.dll   # 依赖库
│
├── abandon/                    # 以被弃用的程序(不参与程序)
│   └── voice_tools.py          # 旧版语音工具实现
│
├── config.py                   # 核心配置（模型、API、工具路径）
├── tool_registry.py            # 工具注册表（加载/管理工具定义与实现）
├── agent_core.py               # 智能体核心（对话、工具调用、模型交互）
├── main.py                     # 程序入口（交互/单次查询模式）
├── requirements.txt            # 依赖清单
└── README.md                   # 项目说明
```

## 🛠️ 环境要求
- Python 3.8+
- Ollama（已安装并运行，参考 [Ollama 官网](https://ollama.com/)）
- 本地模型（如 qwen3:14b、mistral:7b 等，需提前通过 `ollama pull` 下载）
- 语音播报依赖：Balcon TTS（已包含在 utils_bin/balcon/ 目录中，用于离线语音播放）

## 🚀 安装步骤

### 1. 安装 Ollama
```bash
# 方式1：官网脚本（推荐）
curl -fsSL https://ollama.com/install.sh | sh

# 方式2：手动下载（根据系统选择，参考官网）
# https://ollama.com/download
```

### 2. 启动 Ollama 服务
```bash
ollama serve  # 后台运行
# 或直接启动（前台）：ollama run qwen3:14b
```

### 3. 下载本地模型
```bash
ollama pull qwen3:14b
```

### 4. 克隆/下载项目代码
```bash
git clone https://github.com/SuperCatPlus/My-first-agent.git
cd My-first-agent
```

### 5. 安装 Python 依赖
```bash
pip install -r requirements.txt
# 或手动安装核心依赖
pip install requests pyyaml pytz
```

## 📖 使用指南

### 1. 基础使用（交互模式）
```bash
# 启动交互式对话（默认使用 config.py 中配置的模型）
python main.py

# 指定模型启动
python main.py --model qwen3:14b
```

交互指令：
- 输入问题直接对话（如「现在几点了？」「计算 2+3*4」）
- 输入 `清除`/`clear`：清空对话历史
- 输入 `退出`/`quit`：退出程序

### 2. 单次查询模式
```bash
# 直接执行单次查询
python main.py --query "现在的北京时间是多少？"

# 指定模型+单次查询
python main.py --model qwen3:14b --query "计算 100*2 + 50/2"
```

### 3. 查看可用工具
```bash
python main.py --list-tools
```

### 4. 语音播报功能
智能体具有智能语音播报功能：
- **自动播报**：当回复文本长度≤200字时，自动触发语音播报
- **手动调用**：可通过工具调用格式手动触发语音播报
- **离线播放**：使用Balcon TTS实现离线语音播放，无需网络连接
- **异步执行**：语音播放在后台执行，不会阻塞用户输入，用户可在语音播放时继续与智能体对话

```bash
# 示例：手动触发语音播报
python main.py --query "请将'你好，欢迎使用本地大模型智能体！'转换为语音"
```

### 5. HTTP请求工具使用
智能体支持发送HTTP请求到指定的API接口：

**调用格式**：
```
TOOL_CALL: http_request {
  "url": "http://localhost:8000/api/Alarm",
  "method": "GET",
  "timeout": 10
}
```

**示例**：
- 获取报警信息：`python main.py --query "获取报警信息"`
- 更新报警值：`python main.py --query "更新报警值为20"`

### 6. 日志分析功能使用
智能体支持调用`/api/get-log-last-lines`接口查看日志，检测渗透痕迹：

**调用格式**：
```
TOOL_CALL: get_log_last_lines {
  "lines_count": 100
}
```

**参数说明**：
- `lines_count` (可选)：获取的日志行数，默认50行

**示例**：
- 查看默认50行日志：`python main.py --query "查看系统日志，检查是否有渗透痕迹"`
- 查看100行日志：`python main.py --query "查看系统日志100行，检查是否有渗透痕迹"`

**日志分析功能**：
系统会自动分析日志中的渗透痕迹，包括：
- SQL注入攻击
- XSS攻击
- 敏感文件访问
- 命令注入
- 路径遍历
- 异常请求

### 7. API列表管理
智能体只能使用预定义的API列表，确保安全可控：

**配置文件**：`api_config.json`
- 存储允许使用的API列表
- 包含API的URL、方法、描述和参数信息

**使用限制**：
- 模型只能使用`api_config.json`中定义的API
- 严格按照配置的参数格式调用API
- 支持GET和POST等多种HTTP方法

## ⚙️ 配置说明
核心配置文件：`config.py`

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `OLLAMA_API_BASE` | Ollama API 地址 | `http://localhost:11434/api` |
| `MODEL_NAME` | 默认使用的模型 | `qwen3:14b` |
| `TOOLS_DEFINITIONS_DIR` | 工具定义目录 | `tools/definitions` |
| `TOOLS_IMPLEMENTATIONS_DIR` | 工具实现目录 | `tools/implementations` |
| `SYSTEM_PROMPT_FILE` | 系统提示词文件 | `prompts/system_prompt.yaml` |
| `MODEL_PARAMS` | 模型参数（温度、最大令牌等） | `temperature:0.7, top_p:0.9, max_tokens:1000` |

## 🔌 扩展自定义工具
### 步骤1：定义工具（JSON）
在 `tools/definitions/` 下新建 `custom_tools.json`：
```json
{
    "tools": [
        {
            "name": "get_weather",
            "description": "获取指定城市的天气",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称，如北京、上海"
                    }
                },
                "required": ["city"]
            }
        }
    ]
}
```

### 步骤2：实现工具（Python）
在 `tools/implementations/` 下新建 `custom_tools.py`：
```python
from typing import Dict, Any
import requests

class CustomTools:
    """自定义工具实现类"""
    
    @staticmethod
    def get_weather(city: str) -> Dict[str, Any]:
        """获取指定城市天气"""
        try:
            # 示例：调用天气API（需替换为真实接口）
            url = f"https://api.example.com/weather?city={city}"
            response = requests.get(url, timeout=5)
            data = response.json()
            
            return {
                "city": city,
                "weather": data.get("weather"),
                "temperature": data.get("temp"),
                "success": True
            }
        except Exception as e:
            return {
                "city": city,
                "error": f"获取天气失败: {str(e)}",
                "success": False
            }
```

### 步骤3：注册工具
修改 `tools/implementations/__init__.py`，添加自定义工具类：
```python
from .base_tools import BaseTools
from .math_tools import MathTools
from .custom_tools import CustomTools  # 新增
__all__ = ['BaseTools', 'MathTools', 'CustomTools']
```

### 步骤4：更新系统提示词
在 `prompts/system_prompt.yaml` 中添加新工具和API的说明，确保模型能识别并正确使用。

### 步骤5：扩展API列表（可选）
如果需要限制模型只能使用特定的API，可在 `api_config.json` 中添加：
```json
{
    "allowed_apis": [
        {
            "name": "Weather",
            "url": "https://api.example.com/weather",
            "method": "GET",
            "description": "获取天气信息",
            "params": {
                "city": {
                    "type": "string",
                    "required": true,
                    "description": "城市名称"
                }
            }
        }
    ]
}
```

## 📝 常见问题
### Q1: 连接 Ollama 失败？
- 检查 Ollama 服务是否启动：`ollama serve`
- 确认 API 地址正确：默认 `http://localhost:11434`
- 防火墙/代理是否拦截本地请求

### Q2: 工具调用无响应？
- 检查工具名称是否与定义/实现一致（大小写敏感）
- 查看控制台输出，确认工具是否成功加载
- 检查系统提示词中工具调用格式是否正确

### Q3: 模型响应慢？
- 降低模型规模（如从 14B 换为 7B）
- 调整 `MODEL_PARAMS` 中的 `max_tokens` 减小响应长度
- 确保本地硬件满足模型运行要求（如足够的内存/显存）

### Q4: 语音播报不工作？
- 检查 `utils_bin/balcon/` 目录是否存在，以及 `balcon.exe` 文件是否完整
- 查看控制台输出，确认语音工具是否成功加载
- 检查回复文本长度是否≤200字（默认设置）
- 确认系统已安装语音库，如 Microsoft Xiaoxiao

## 📄 许可证
（可选）补充你的开源许可证，如 MIT、Apache 2.0 等。

## 📧 反馈与贡献
欢迎提交 Issue/PR 改进项目，如有问题可通过项目仓库反馈。


### 优化说明
1. **结构完善**：补充了特性、配置说明、扩展工具、常见问题等核心板块，符合开源项目 README 规范；
2. **实用性增强**：增加了详细的安装步骤、使用示例、自定义工具教程，降低使用门槛；
3. **可读性提升**：使用表格、代码块、emoji 区分不同模块，重点内容突出；
4. **兼容性**：保留原有项目结构，所有示例与现有代码逻辑对齐（如工具定义/实现方式）；
5. **扩展性**：预留许可证、贡献指南等板块，便于后续维护。

可根据实际需求调整：
- 补充真实的许可证信息；
- 替换天气 API 等示例为实际可用的接口；
- 新增更多工具示例（如文件操作、数据解析等）；
- 补充性能优化、部署（如 Docker）等进阶内容。