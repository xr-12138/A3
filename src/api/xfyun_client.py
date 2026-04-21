# src/api/xfyun_client.py
import sys
from pathlib import Path
root_path = Path(__file__).parent.parent.parent
sys.path.append(str(root_path))

import asyncio
import websockets
import json
import hashlib
import hmac
import base64
from datetime import datetime
from urllib.parse import urlencode
from config.xfyun_config import XFYUN_CONFIG

class XFYunClient:
    def __init__(self):
        self.app_id = XFYUN_CONFIG["app_id"]
        self.api_key = XFYUN_CONFIG["api_key"]
        self.api_secret = XFYUN_CONFIG["api_secret"]
        self.host = "spark-api.xf-yun.com"
        self.path = "/v2.1/chat"
        self.domain = "generalv2"

    def _generate_auth_url(self):
        date = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
        signature_origin = f"host: {self.host}\ndate: {date}\nGET {self.path} HTTP/1.1"
        sha = hmac.new(self.api_secret.encode(), signature_origin.encode(), hashlib.sha256)
        digest = base64.b64encode(sha.digest()).decode()
        authorization = f'api_key="{self.api_key}", algorithm="hmac-sha256", headers="host date request-line", signature="{digest}"'
        
        params = {
            "host": self.host,
            "date": date,
            "authorization": authorization
        }
        return f"wss://{self.host}{self.path}?{urlencode(params)}"

    def generate(self, prompt):
        async def _run():
            url = self._generate_auth_url()
            async with websockets.connect(url) as ws:
                data = {
                    "header": {"app_id": self.app_id},
                    "parameter": {"chat": {"domain": self.domain, "temperature": 0.7, "max_tokens": 2048}},
                    "payload": {"message": {"text": [{"role": "user", "content": prompt}]}}
                }
                await ws.send(json.dumps(data))
                
                full_result = ""
                while True:
                    resp = await ws.recv()
                    res = json.loads(resp)
                    if res["header"]["code"] != 0:
                        return f"错误：{res['header']['message']}"
                    
                    full_result += res["payload"]["choices"]["text"][0]["content"]
                    if res["header"]["status"] == 2:
                        return full_result
        
        try:
            return asyncio.run(_run())
        except Exception as e:
            return f"异常：{str(e)}"

xfyun_client = XFYunClient()

