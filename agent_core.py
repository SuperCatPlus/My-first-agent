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
                return data.get('system_prompt', '')
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
            # 模式1: TOOL_CALL: tool_name {json}
            r"TOOL_CALL:\s*(\w+)\s*\{([\s\S]*?)\}",
            # 模式2: 工具调用: tool_name(json)
            r"工具调用:\s*(\w+)\s*\(([^)]+)\)",
            # 模式3: 使用tool_name工具 {json}
            r"使用(\w+)工具\s*\{([\s\S]*?)\}"
        ]
        
        for pattern in tool_patterns:
            match = re.search(pattern, response_text, re.IGNORECASE)
            if match:
                tool_name = match.group(1).strip()
                params_str = match.group(2).strip()
                
                try:
                    # 首先尝试解析为JSON
                    if params_str:
                        params = json.loads(params_str)
                    else:
                        params = {}
                    return {"name": tool_name, "parameters": params}
                except json.JSONDecodeError:
                    # 如果JSON解析失败，尝试解析简单键值对
                    params = {}
                    lines = params_str.split('\n')
                    for line in lines:
                        line = line.strip()
                        if ':' in line:
                            key, value = line.split(':', 1)
                            key = key.strip().strip('"\'')
                            value = value.strip().strip('",\'')
                            if value.lower() in ['true', 'false']:
                                params[key] = value.lower() == 'true'
                            elif value.isdigit():
                                params[key] = int(value)
                            else:
                                params[key] = value
                    
                    return {"name": tool_name, "parameters": params}
        
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
                
                # 自动语音播报：回复长度<=50字时发声，或用户输入包含"耄耋"时强制发声（工具调用后的回复）
                should_speak = len(final_message) <= 50 or "耄耋" in user_message
                if should_speak:
                    try:
                        # 自动调用语音工具朗读回复
                        # 当用户输入包含"耄耋"时，设置max_length为较大值以强制发声
                        max_length = 1000 if "耄耋" in user_message else 50
                        self.tool_registry.execute_tool(
                            "text_to_speech_edge_mixed",
                            text=final_message,
                            max_length=max_length
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
            
            # 自动语音播报：回复长度<=50字时发声，或用户输入包含"耄耋"时强制发声
            should_speak = len(assistant_message) <= 50 or "耄耋" in user_message
            if should_speak:
                try:
                    # 自动调用语音工具朗读回复
                    # 当用户输入包含"耄耋"时，设置max_length为较大值以强制发声
                    max_length = 1000 if "耄耋" in user_message else 50
                    self.tool_registry.execute_tool(
                        "text_to_speech_edge_mixed",
                        text=assistant_message,
                        max_length=max_length
                    )
                except Exception as e:
                    # 语音播报失败不影响回复
                    print(f"自动语音播报失败: {e}")
            
            return assistant_message
    
    def clear_history(self) -> None:
        """清除对话历史"""
        self.conversation_history = []