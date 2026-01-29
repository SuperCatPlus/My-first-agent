# 本地大模型智能体

基于 Ollama 部署的本地大模型智能体，支持灵活的工具调用能力，可扩展、易配置，适配多种本地大模型。

## 🌟 核心特性
- 🤖 适配 Ollama 生态：支持 qwen、mistral、llama 等主流本地大模型
- 🔧 可扩展工具系统：工具定义与实现分离，轻松新增自定义工具
- 💬 交互式对话：支持多轮对话、历史记录管理
- ⚡ 高效工具调用：自动解析模型响应并执行对应工具，返回结构化结果
- 📝 可配置化：通过配置文件灵活调整模型参数、工具路径等
- 🎤 智能语音播报：短文本自动发声，长文本不发声，提升用户体验

## 📋 目录结构
```
My_agent_project/
├── tools/                      # 工具模块
│   ├── definitions/            # 工具定义（JSON格式，描述工具元信息）
│   │   ├── base_tools.json     # 基础工具（时间、网络）
│   │   ├── test_tools.json     # 测试工具
│   │   ├── math_tools.json     # 数学工具
│   │   └── voice_tools.json    # 语音工具
│   └── implementations/        # 工具实现（Python类，对应具体逻辑）
│       ├── __init__.py
│       ├── base_tools.py       # 基础工具实现（获取时间、网络搜索）
│       ├── math_tools.py       # 数学工具实现（计算、问候）
│       └── voice_tools.py      # 语音工具实现（文字转语音）
├── prompts/                    # 提示词目录
│   └── system_prompt.yaml      # 系统提示词（定义工具调用规则）
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
- 语音播报依赖：edge-tts、playsound（用于文字转语音和播放）

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
git clone <你的仓库地址>
cd My_agent_project
```

### 5. 安装 Python 依赖
```bash
pip install -r requirements.txt
# 或手动安装核心依赖
pip install requests pyyaml pytz edge-tts playsound
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
- **自动播报**：当回复文本长度≤50字时，自动触发语音播报
- **手动调用**：可通过工具调用格式手动触发语音播报

```bash
# 示例：手动触发语音播报
python main.py --query "请将'你好，欢迎使用本地大模型智能体！'转换为语音"
```

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
在 `prompts/system_prompt.yaml` 中补充工具说明，确保模型能识别新工具。

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
- 检查是否安装了语音依赖：`pip install edge-tts playsound`
- 确认网络连接正常（edge-tts 需要联网）
- 查看控制台输出，确认语音工具是否成功加载
- 检查回复文本长度是否≤50字（默认设置）

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