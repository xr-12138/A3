from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

import requests

from .base import BaseAIClient


class OllamaClient(BaseAIClient):
    """简单的 Ollama 本地部署客户端封装，兼容项目中 `BaseAIClient` 接口。

    该实现使用 `config/.env` 中的 `XF_API_URL` 和 `XF_MODEL` 配置，
    以便最小改动将现有 OpenAI-兼容请求指向本地 Ollama 服务。
    """

    def __init__(self):
        self._load_config()

    def _load_config(self):
        env_path = Path(__file__).resolve().parent.parent / "config" / ".env"
        self.api_url = "http://127.0.0.1:11434/v1/chat/completions"
        self.api_key = ""
        self.model = "ollama"
        try:
            if env_path.exists():
                with open(env_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith('#'):
                            continue
                        if '=' not in line:
                            continue
                        k, v = line.split('=', 1)
                        v = v.strip().strip('"').strip("'")
                        if k == 'XF_API_URL':
                            self.api_url = v
                        elif k == 'XF_API_KEY':
                            self.api_key = v
                        elif k == 'XF_MODEL':
                            self.model = v
        except Exception:
            # 保持默认配置，确保不会阻塞页面
            pass

    def _post(self, payload: Dict[str, Any], timeout: int = 120) -> Optional[Dict[str, Any]]:
        headers = {'Content-Type': 'application/json'}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        try:
            resp = requests.post(self.api_url, json=payload, headers=headers, timeout=timeout)
            if resp.status_code != 200:
                return {"error": f"HTTP {resp.status_code}: {resp.text}"}
            try:
                return resp.json()
            except Exception:
                return {"error": "无法解析返回 JSON"}
        except Exception as e:
            return {"error": str(e)}

    def generate_text(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }
        result = self._post(payload)
        if not result:
            return "错误: 无响应"
        if 'error' in result:
            return f"错误: {result['error']}"

        # 兼容多种返回格式
        # 优先查找 choices -> message/content
        try:
            choices = result.get('choices') if isinstance(result, dict) else None
            if choices:
                first = choices[0]
                if 'message' in first and isinstance(first['message'], dict):
                    return first['message'].get('content', '')
                if 'text' in first:
                    return first.get('text', '')

            # 某些 Ollama/OpenAI 兼容实现返回 { 'text': '...' }
            if 'text' in result:
                return result.get('text', '')

            # 回退到直接字符串化
            return json.dumps(result, ensure_ascii=False)
        except Exception as e:
            return f"错误: 解析响应时异常: {str(e)}"

    def generate_mindmap(self, topic: str) -> Dict:
        prompt = f"请为'{topic}'生成一个思维导图，返回JSON格式，包含title和children字段。"
        text = self.generate_text(prompt)
        try:
            return json.loads(text)
        except Exception:
            # 返回简单默认结构
            return {"title": topic, "children": [{"title": "基础概念"}, {"title": "应用场景"}]}

    def generate_code(self, topic: str, language: str = "python") -> str:
        prompt = f"请生成关于'{topic}'的{language}代码示例，代码要完整可运行，包含必要的注释和说明。"
        return self.generate_text(prompt)

    def generate_questions(self, topic: str, num: int = 5) -> List:
        prompt = f"请为'{topic}'生成{num}个练习题，返回JSON格式，包含q（问题）和a（答案）字段的列表。"
        text = self.generate_text(prompt)
        try:
            return json.loads(text)
        except Exception:
            questions = []
            for i in range(num):
                questions.append({"q": f"{topic} 的第 {i+1} 个问题？", "a": f"示例答案 {i+1}"})
            return questions

    # 兼容旧接口
    def generate(self, prompt: str, **kwargs) -> str:
        return self.generate_text(prompt)

