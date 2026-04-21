# config/xfyun_config.py
import os
from dotenv import load_dotenv
from pathlib import Path

# 加载 .env 文件
env_path = Path(__file__).parent.parent / "config" / ".env"
load_dotenv(dotenv_path=env_path)

# 讯飞 API 配置
XFYUN_CONFIG = {
    "app_id": os.getenv("XF_APP_ID", ""),
    "api_key": os.getenv("XF_API_KEY", ""),
    "api_secret": os.getenv("XF_API_SECRET", ""),
    "domain": os.getenv("XF_DOMAIN", "generalv2"),
    "multimodal_domain": os.getenv("XF_MULTIMODAL_DOMAIN", "multimodal-v1"),
}

# 内容安全配置
XF_SAFETY_CONFIG = {
    "check_url": "https://rest-api.xfyun.cn/v1/solution/v1/text_audit",
    "timeout": 10
}
