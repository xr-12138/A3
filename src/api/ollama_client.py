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
        self.model = "qwen3.5:2b"  # 默认使用qwen3.5:2b模型
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
            print(f"[信息] OllamaClient配置: URL={self.api_url}, Model={self.model}")
        except Exception as e:
            print(f"[错误] 加载配置时发生错误: {str(e)}")
            # 保持默认配置，确保不会阻塞页面
            pass

    def _post(self, payload: Dict[str, Any], timeout: int = 120) -> Optional[Dict[str, Any]]:
        headers = {'Content-Type': 'application/json'}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        try:
            resp = requests.post(self.api_url, json=payload, headers=headers, timeout=timeout)
            if resp.status_code != 200:
                # 尝试解析服务器返回的 JSON 错误信息
                try:
                    err = resp.json()
                    msg = ''
                    # 常见 Ollama 返回示例中会包含 model not found 的提示
                    if isinstance(err, dict):
                        # 支持多种错误字段路径
                        if 'error' in err and isinstance(err['error'], dict):
                            msg = err['error'].get('message', '') or str(err['error'])
                        else:
                            msg = err.get('message', '') or str(err)
                    if msg and 'not found' in msg and 'model' in msg:
                        return {"error": f"模型未找到: {msg}. 请运行 'ollama list' 查看本地已安装模型，并在 config/.env 中设置 XF_MODEL 为可用模型名。"}
                    return {"error": f"HTTP {resp.status_code}: {resp.text}"}
                except Exception:
                    return {"error": f"HTTP {resp.status_code}: {resp.text}"}
            try:
                return resp.json()
            except Exception:
                return {"error": "无法解析返回 JSON"}
        except Exception as e:
            return {"error": str(e)}

    def generate_text(self, prompt: str) -> str:
        # 强制模型以中文输出，并提供 system 指令以保证输出格式规范
        system_msg = "你是一个专业的中文学习助手，始终用中文回答。严格按照用户要求的格式输出，仅返回所需内容，不要添加额外解释。对于学习画像，确保所有字段和内容都是中文。"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": prompt}
            ],
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
        # 更详细且健壮的提示，要求严格 JSON 输出，包含多层次信息：title, note, children
        prompt = (
            f"请为高校课程的知识主题'{topic}'生成一个结构化的思维导图，返回严格的 JSON。"
            "格式示例：{\n  \"title\": \"根节点\",\n  \"note\": \"一句话概述\",\n  \"children\": [ {\"title\":\"节点名\", \"note\":\"简短说明\", \"children\": [...] }, ... ]\n}\n"
            "每个节点应尽量包含：1) title（字符串），2) note（不超过60字的简短描述，可选），3) children（同结构的数组，可选）。"
            "请至少输出 3 个二级节点，每个二级节点下尽量包含 2 个三级子节点（如适用）。不要包含非 JSON 文本或额外说明。"
        )

        text = self.generate_text(prompt)

        # 尝试从返回中提取 JSON 块（兼容模型返回多余文本的情况）
        def _extract_json(s: str) -> Optional[str]:
            try:
                json.loads(s)
                return s
            except Exception:
                pass
            m = re.search(r"(\{.*\})", s, flags=re.S)
            if m:
                return m.group(1)
            return None

        try:
            js = _extract_json(text)
            if js:
                return json.loads(js)
        except Exception:
            pass

        # 回退：如果解析失败，构造一个较为完整的占位结构，包含描述（note）以便前端展示
        return {
            "title": topic,
            "note": f"{topic} 概览：核心概念与应用场景",
            "children": [
                {"title": "基础概念", "note": f"{topic} 的基础概念、定义与关键术语"},
                {"title": "核心原理", "note": f"{topic} 的主要原理与常见算法/方法"},
                {"title": "实践应用", "note": f"{topic} 的典型应用场景与实战案例"}
            ]
        }

    def generate_code(self, topic: str, language: str = "python") -> str:
        prompt = f"请生成关于'{topic}'的{language}代码示例，代码要完整可运行，包含必要的注释和说明。"
        return self.generate_text(prompt)

    def generate_questions(self, topic: str, num: int = 5) -> List:
        # 请求模型返回结构化题库：每题包含 q（问题）、a（答案）和 explanation（详解）
        prompt = (
            f"请为'{topic}'生成{num}个练习题，返回严格的 JSON 列表，每个元素包含字段："
            "q（问题，中文）、a（标准答案，中文）、explanation（详细解析，中文，步骤清晰，便于学生学习）。"
            " 示例输出：[{\"q\": \"问题1\", \"a\": \"答案1\", \"explanation\": \"详解1\"}, ...]。"
        )
        text = self.generate_text(prompt)
        try:
            return json.loads(text)
        except Exception:
            questions = []
            for i in range(num):
                questions.append({
                    "q": f"{topic} 的第 {i+1} 个问题？",
                    "a": f"示例答案 {i+1}",
                    "explanation": f"示例解析 {i+1}: 这是对答案的详细分步说明，帮助学习者理解解题思路。"
                })
            return questions

    # 兼容旧接口
    def generate(self, prompt: str, **kwargs) -> str:
        return self.generate_text(prompt)