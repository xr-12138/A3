from __future__ import annotations

import os
import json
import time
import requests
from typing import Dict, List, Any, Optional
from pathlib import Path

from .base import BaseAIClient


class XFYunClient(BaseAIClient):
    """讯飞星火大模型客户端实现（HTTP服务接口版本）"""

    def __init__(self):
        # 加载配置
        try:
            self._load_config()
        except Exception as e:
            print(f"[ERROR] 初始化XFYunClient失败: {str(e)}")
            # 不抛出异常，确保页面能正常访问
            self.api_key = ""
            self.api_url = "https://spark-api-open.xf-yun.com/v1/chat/completions"

    def _load_config(self):
        """从.env文件加载配置"""
        try:
            env_path = Path(__file__).resolve().parent.parent.parent / "config" / ".env"
            print(f"[INFO] 加载配置文件: {env_path}")
            if not env_path.exists():
                error_msg = f"配置文件不存在: {env_path}"
                print(f"[ERROR] {error_msg}")
                # 不抛出异常，使用默认值
                self.api_key = "ollama"
                self.api_url = "http://127.0.0.1:11434/v1/chat/completions"
                self.model = "qwen3.5:2b"
                return

            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    key, value = line.split('=', 1)
                    # 去除可能的引号和空格
                    value = value.strip().strip('"').strip("'")
                    if key == 'XF_API_KEY':
                        self.api_key = value
                        print(f"[INFO] 加载到API_KEY: {self.api_key[:4]}****")
                    elif key == 'XF_API_URL':
                        self.api_url = value
                        print(f"[INFO] 加载到API_URL: {self.api_url}")
                    elif key == 'XF_MODEL':
                        self.model = value
                        print(f"[INFO] 加载到MODEL: {self.model}")

            # 设置默认值
            if not hasattr(self, 'api_key'):
                self.api_key = "ollama"
            if not hasattr(self, 'api_url'):
                self.api_url = "http://127.0.0.1:11434/v1/chat/completions"
            if not hasattr(self, 'model'):
                self.model = "qwen3.5:2b"
            
            print(f"[INFO] API地址: {self.api_url}")
            print(f"[INFO] 模型: {self.model}")
        except Exception as e:
            print(f"[ERROR] 加载配置时发生错误: {str(e)}")
            # 不抛出异常，使用默认值
            self.api_key = "ollama"
            self.api_url = "http://127.0.0.1:11434/v1/chat/completions"
            self.model = "qwen3.5:2b"














    def _chat(self, prompt, max_tokens=2048, temperature=0.7, timeout=300):
        """与OpenAI兼容API进行对话"""
        try:
            # 检查API密钥是否为空
            if not self.api_key:
                error_msg = "API密钥未配置"
                print(f"[ERROR] {error_msg}")
                return f"错误: {error_msg}"

            # 构建请求头 - 使用Bearer Token认证
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'content-type': "application/json"
            }
            print(f"[INFO] 请求头: {json.dumps(headers, indent=2)}")
            
            # 构建请求数据 - 与http_demo.py保持一致
            request_data = {
                "model": self.model,
                "user": "user_id",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "stream": True,
                "tools": [
                    {
                        "type": "web_search",
                        "web_search": {
                            "enable": True,
                            "search_mode": "deep"
                        }
                    }
                ]
            }
            print(f"[INFO] 请求数据: {json.dumps(request_data, indent=2)}")
            
            # 发送请求
            print("[INFO] 发送请求到API...")
            response = requests.post(
                self.api_url,
                json=request_data,
                headers=headers,
                timeout=timeout,
                stream=True
            )
            print(f"[INFO] 请求完成，状态码: {response.status_code}")
            print(f"[INFO] 响应头部: {dict(response.headers)}")
            
            # 检查响应状态
            if response.status_code != 200:
                error_msg = f"HTTP错误: {response.status_code} - {response.text}"
                print(f"[ERROR] {error_msg}")
                return f"错误: {error_msg}"
            
            # 处理流式响应 - 与http_demo.py保持一致
            full_response = ""
            is_first_content = True
            
            for chunks in response.iter_lines():
                print(f"[DEBUG] 收到 chunk: {chunks}")
                if chunks and '[DONE]' not in str(chunks):
                    try:
                        # 尝试处理不同格式的chunk
                        if chunks.startswith(b'data: '):
                            data_org = chunks[6:]
                            if data_org:
                                chunk = json.loads(data_org)
                                print(f"[DEBUG] 解析后的数据: {json.dumps(chunk, indent=2)}")
                                
                                # 检查API错误
                                if 'error' in chunk:
                                    error_msg = f"API错误: {chunk['error']['message']}"
                                    print(f"[ERROR] {error_msg}")
                                    return f"错误: {error_msg}"
                                
                                # 提取内容
                                choices = chunk.get('choices', [])
                                if choices:
                                    text = choices[0].get('delta', {})
                                    if 'content' in text and text['content']:
                                        content = text["content"]
                                        if is_first_content:
                                            is_first_content = False
                                        print(f"[DEBUG] 收到内容: {content[:100]}...")
                                        full_response += content
                        else:
                            # 尝试直接解析
                            chunk = json.loads(chunks)
                            print(f"[DEBUG] 直接解析后的数据: {json.dumps(chunk, indent=2)}")
                            
                            # 检查API错误
                            if 'error' in chunk:
                                error_msg = f"API错误: {chunk['error']['message']}"
                                print(f"[ERROR] {error_msg}")
                                return f"错误: {error_msg}"
                            
                            # 提取内容
                            choices = chunk.get('choices', [])
                            if choices:
                                for choice in choices:
                                    if 'message' in choice and 'content' in choice['message']:
                                        content = choice['message']['content']
                                        print(f"[DEBUG] 收到内容: {content[:100]}...")
                                        full_response += content
                                    elif 'delta' in choice and 'content' in choice['delta']:
                                        content = choice['delta']['content']
                                        print(f"[DEBUG] 收到内容: {content[:100]}...")
                                        full_response += content
                    except json.JSONDecodeError as e:
                        error_msg = f"JSON解析错误: {str(e)}"
                        print(f"[ERROR] {error_msg}")
                        print(f"[DEBUG] 原始chunk: {chunks}")
                        continue
            
            # 检查结果
            if not full_response:
                error_msg = "未收到API响应内容"
                print(f"[ERROR] {error_msg}")
                return f"错误: {error_msg}"
            
            print("[INFO] API响应成功接收")
            return full_response
            
        except Exception as e:
            print(f"[ERROR] 与API通信时发生异常: {str(e)}")
            import traceback
            traceback.print_exc()
            # 不抛出异常，返回错误信息，确保页面能正常访问
            return f"错误: {str(e)}"





    def generate_text(self, prompt: str) -> str:
        """生成文本响应"""
        # 重试机制
        retries = 3
        for i in range(retries):
            try:
                print(f"[INFO] 尝试第 {i+1}/{retries} 次生成文本")
                result = self._chat(prompt)
                # 检查是否是错误信息
                if result.startswith("错误:"):
                    if i == retries - 1:
                        print("[ERROR] 所有重试均失败")
                        return result
                    print(f"[WARNING] 第 {i+1} 次尝试失败: {result}")
                    print(f"[INFO] 等待1秒后重试...")
                    time.sleep(1)
                    continue
                return result
            except Exception as e:
                print(f"[WARNING] 第 {i+1} 次尝试失败: {str(e)}")
                if i == retries - 1:
                    print("[ERROR] 所有重试均失败")
                    return f"错误: {str(e)}"
                print(f"[INFO] 等待1秒后重试...")
                time.sleep(1)


    def generate_mindmap(self, topic: str) -> Dict:
        """生成思维导图的结构化表示"""
        prompt = f"请为'{topic}'生成一个思维导图，返回JSON格式，包含title和children字段，children中的每个节点也包含title和可选的children字段。示例格式：{{\"title\": \"主题\", \"children\": [{{\"title\": \"子主题1\", \"children\": [{{\"title\": \"子子主题1\"}}]}}, {{\"title\": \"子主题2\"}}]}}"
        
        # 重试机制
        retries = 3
        for i in range(retries):
            try:
                response = self._chat(prompt)
                # 尝试解析JSON
                try:
                    return json.loads(response)
                except json.JSONDecodeError:
                    # 如果返回的不是JSON，生成一个默认的思维导图
                    return {
                        "title": topic,
                        "children": [
                            {"title": "基础概念", "children": [{"title": f"{topic}的定义"}, {"title": f"{topic}的特点"}]},
                            {"title": "核心原理", "children": [{"title": f"{topic}的工作原理"}, {"title": f"{topic}的数学基础"}]},
                            {"title": "应用场景", "children": [{"title": f"{topic}的实际应用"}, {"title": f"{topic}的案例分析"}]},
                            {"title": "学习资源", "children": [{"title": f"{topic}的推荐书籍"}, {"title": f"{topic}的在线课程"}]},
                        ]
                    }
            except Exception as e:
                if i == retries - 1:
                    # 如果最后一次重试失败，返回默认思维导图
                    return {
                        "title": topic,
                        "children": [
                            {"title": "基础概念", "children": [{"title": f"{topic}的定义"}, {"title": f"{topic}的特点"}]},
                            {"title": "应用场景", "children": [{"title": f"{topic}的实际应用"}, {"title": f"{topic}的案例分析"}]},
                        ]
                    }
                time.sleep(1)

    def generate_code(self, topic: str, language: str = "python") -> str:
        """生成代码示例文本"""
        prompt = f"请生成关于'{topic}'的{language}代码示例，代码要完整可运行，包含必要的注释和说明。"
        
        # 重试机制
        retries = 3
        for i in range(retries):
            try:
                return self._chat(prompt)
            except Exception as e:
                if i == retries - 1:
                    # 如果最后一次重试失败，返回默认代码
                    if language.lower() == "python":
                        return f"# {topic} 示例代码\ndef {topic.replace(' ', '_').lower()}_example():\n    \"\"\"{topic}的示例实现\"\"\"\n    # 核心逻辑\n    result = f'Implementing {topic}'\n    return result\n\nif __name__ == '__main__':\n    print({topic.replace(' ', '_').lower()}_example())\n"
                    else:
                        return f"// {topic} 示例代码 ({language})\nfunction {topic.replace(' ', '').toLowerCase()}Example() {{\n    // 核心逻辑\n    return `Implementing {topic}`;\n}}\n\nconsole.log({topic.replace(' ', '').toLowerCase()}Example());\n"
                time.sleep(1)

    def generate_questions(self, topic: str, num: int = 5) -> List:
        """生成题目列表"""
        prompt = f"请为'{topic}'生成{num}个练习题，返回JSON格式，包含q（问题）和a（答案）字段的列表。示例格式：[{{\"q\": \"问题1\", \"a\": \"答案1\"}}, {{\"q\": \"问题2\", \"a\": \"答案2\"}}]"
        
        # 重试机制
        retries = 3
        for i in range(retries):
            try:
                response = self._chat(prompt)
                # 尝试解析JSON
                try:
                    return json.loads(response)
                except json.JSONDecodeError:
                    # 如果返回的不是JSON，生成默认问题
                    questions = []
                    for i in range(num):
                        questions.append({"q": f"{topic}的第{i+1}个问题？", "a": f"关于{topic}的详细回答..."})
                    return questions
            except Exception as e:
                if i == retries - 1:
                    # 如果最后一次重试失败，返回默认问题
                    questions = []
                    for i in range(num):
                        questions.append({"q": f"{topic}的第{i+1}个问题？", "a": f"关于{topic}的详细回答..."})
                    return questions
                time.sleep(1)

    # 兼容旧接口
    def generate(self, prompt: str, **kwargs) -> str:
        """兼容旧接口"""
        return self.generate_text(prompt)

    async def async_generate(self, prompt: str, timeout: Optional[int] = None) -> str:
        """异步生成文本"""
        return self.generate_text(prompt)