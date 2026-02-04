import requests
import json
import yaml
from typing import Dict, List, Any, Optional
from tool_registry import ToolRegistry

class AgentCore:
    """智能体核心类"""
    
    def __init__(self, config, tool_registry: ToolRegistry):
        self.config = config
        self.tool_registry = tool_registry
        self.system_prompt = self._load_system_prompt()
        self.conversation_history = []
    
    def _load_system_prompt(self) -> str:
        """加载系统提示词"""
        try:
            with open(self.config.SYSTEM_PROMPT_FILE, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                system_prompt = data.get('system_prompt', '')
                # 替换后端API基础URL占位符
                system_prompt = system_prompt.replace('{backend_api_base}', self.config.BACKEND_API_BASE)
                return system_prompt
        except Exception as e:
            print(f"加载系统提示词失败: {e}")
            return "你是一个有用的助手。"
    
    def _call_ollama(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """调用Ollama API"""
        url = self.config.get_chat_endpoint()
        
        payload = {
            "model": self.config.MODEL_NAME,
            "messages": messages,
            "stream": False,
            **self.config.MODEL_PARAMS
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"调用Ollama API失败: {e}")
    
    def _extract_tool_call(self, response_text: str) -> Optional[Dict[str, Any]]:
        """从模型响应中提取工具调用（简化版本）"""
        # 在实际应用中，这里应该使用更复杂的解析逻辑
        # 这里简化处理，假设模型会以特定格式返回工具调用
        import re
        import json
        
        # 更强大的解析模式，支持JSON格式参数
        tool_patterns = [
            # 模式1: TOOL_CALL: tool_name {json} - 使用贪婪匹配并正确处理嵌套大括号
            r"TOOL_CALL:\s*(\w+)\s*\{((?:[^{}]|\{[^{}]*\})*)\}",
            # 模式2: 工具调用: tool_name(json)
            r"工具调用:\s*(\w+)\s*\(([^)]+)\)",
            # 模式3: 使用tool_name工具 {json} - 使用贪婪匹配并正确处理嵌套大括号
            r"使用(\w+)工具\s*\{((?:[^{}]|\{[^{}]*\})*)\}"
        ]
        
        for pattern in tool_patterns:
            match = re.search(pattern, response_text, re.IGNORECASE)
            if match:
                tool_name = match.group(1).strip()
                params_str = match.group(2).strip()
                
                try:
                    # 首先尝试解析为JSON
                    if params_str:
                        # 修复JSON解析：处理可能的格式问题
                        # 确保params_str是一个完整的JSON对象
                        # 1. 添加外层大括号
                        json_str = f"{{{params_str}}}"
                        # 2. 移除可能的尾随逗号
                        json_str = re.sub(r',\s*([}\]])', r' \1', json_str)
                        params = json.loads(json_str)
                    else:
                        params = {}
                    return {"name": tool_name, "parameters": params}
                except json.JSONDecodeError as e:
                    print(f"JSON解析错误: {e}")
                    print(f"原始参数字符串: {params_str}")
                    # 如果JSON解析失败，返回空参数
                    return {"name": tool_name, "parameters": {}}
        
        return None
    
    def process_message(self, user_message: str) -> str:
        """处理用户消息"""
        # 构建消息历史
        messages = [
            {"role": "system", "content": self.system_prompt},
            *self.conversation_history[-5:],  # 只保留最近5条历史
            {"role": "user", "content": user_message}
        ]
        
        # 获取模型响应
        response = self._call_ollama(messages)
        assistant_message = response.get("message", {}).get("content", "")
        
        # 检查是否需要工具调用
        tool_call = self._extract_tool_call(assistant_message)
        
        if tool_call:
            tool_name = tool_call["name"]
            tool_params = tool_call["parameters"]
            
            try:
                # 执行工具
                tool_result = self.tool_registry.execute_tool(tool_name, **tool_params)
                
                # 将工具结果作为系统消息添加到对话中
                result_message = {
                    "role": "system",
                    "content": f"工具 {tool_name} 执行结果: {json.dumps(tool_result, ensure_ascii=False)}"
                }
                
                # 再次调用模型，提供工具结果
                messages.append({"role": "assistant", "content": assistant_message})
                messages.append(result_message)
                
                final_response = self._call_ollama(messages)
                final_message = final_response.get("message", {}).get("content", "")
                
                # 更新对话历史
                self.conversation_history.append({"role": "user", "content": user_message})
                self.conversation_history.append({"role": "assistant", "content": final_message})
                
                # 自动语音播报：回复长度<=200字时发声，或用户输入包含"耄耋"时强制发声（工具调用后的回复）
                should_speak = len(final_message) <= 200 or "耄耋" in user_message
                if should_speak:
                    try:
                        # 自动调用语音工具朗读回复
                        self.tool_registry.execute_tool(
                            "balcon_tts",
                            text=final_message,
                            voice_name="Microsoft Xiaoxiao"
                        )
                    except Exception as e:
                        # 语音播报失败不影响回复
                        print(f"自动语音播报失败: {e}")
                
                return final_message
                
            except Exception as e:
                error_message = f"执行工具 {tool_name} 失败: {str(e)}"
                return error_message
        else:
            # 没有工具调用，检查回复长度并自动调用语音工具（短文本）
            self.conversation_history.append({"role": "user", "content": user_message})
            self.conversation_history.append({"role": "assistant", "content": assistant_message})
            
            # 自动语音播报：回复长度<=200字时发声，或用户输入包含"耄耋"时强制发声
            # 但不播报工具调用格式
            if not self._extract_tool_call(assistant_message):
                should_speak = len(assistant_message) <= 200 or "耄耋" in user_message
                if should_speak:
                    try:
                        # 自动调用语音工具朗读回复
                        self.tool_registry.execute_tool(
                            "balcon_tts",
                            text=assistant_message,
                            voice_name="Microsoft Xiaoxiao"
                        )
                    except Exception as e:
                        # 语音播报失败不影响回复
                        print(f"自动语音播报失败: {e}")
            
            return assistant_message
    
    def clear_history(self) -> None:
        """清除对话历史"""
        self.conversation_history = []