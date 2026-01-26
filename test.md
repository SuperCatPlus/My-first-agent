```
My_agent_project/
├── config.py          # 存放配置（如模型名、API地址、系统提示词）
├── tools.py           # 存放所有工具函数
├── tool_registry.py   # 管理工具的定义和映射
├── agent_core.py      # Agent的核心逻辑（聊天循环、工具调用解析）
└── main.py            # 程序主入口，负责启动和组装
```

config.py - 集中管理配置

- `tools.py` - 纯粹的工具函数实现
这里只包含具体的工具函数，不涉及任何Agent逻辑。

- `tool_registry.py`工具的管理和描述
这是连接“工具函数”和“Agent逻辑”的桥梁。负责生成工具描述，并将工具名映射到实际的函数。

- `agent_core.py` Agent的大脑,包含与模型交互、解析响应、管理对话历史的核心逻辑。



# 第二版
```
My_agent_project/
├── tools/
│   ├── definitions/
│   │   ├── base_tools.json        # 基础工具定义
│   │   ├── web_tools.json         # 网络相关工具
│   │   └── math_tools.json        # 数学相关工具
│   └── implementations/
│       ├── __init__.py
│       ├── base_tools.py          # 基础工具实现
│       ├── web_tools.py           # 网络工具实现
│       └── math_tools.py          # 数学工具实现
├── prompts/
│   └── system_prompt.json
├── config.py
├── tool_registry.py    # 重构：负责加载定义和实现
├── agent_core.py
└── main.py

```
