# config/xfyun_config.py
import os
from pathlib import Path

# 加载 .env 文件
env_path = Path(__file__).parent / ".env"

# 如果 .env 文件不存在，创建一个默认版本
if not env_path.exists():
    default_env_content = """XF_APP_ID=your_app_id
XF_API_KEY=your_api_key
XF_API_SECRET=your_api_secret
XF_DOMAIN=ultra
XF_MULTIMODAL_DOMAIN=multimodal-v1

ENV=development
WORK_DIR=/home/hjj/桌面/A3-main
DATABASE_URL=sqlite:////home/hjj/桌面/A3-main/data/db.sqlite3
CACHE_DIR=/home/hjj/桌面/A3-main/data/cache
MEDIA_DIR=/home/hjj/桌面/A3-main/data/media
LOG_LEVEL=DEBUG
"""
    with open(env_path, 'w', encoding='utf-8') as f:
        f.write(default_env_content)
    print(f"Created default .env file at {env_path}")

# 读取 .env 文件内容
env_vars = {}
with open(env_path, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        try:
            key, value = line.split('=', 1)
            env_vars[key] = value
        except ValueError:
            pass

# 讯飞 API 配置
XFYUN_CONFIG = {
    "app_id": env_vars.get("XF_APP_ID", ""),
    "api_key": env_vars.get("XF_API_KEY", ""),
    "api_secret": env_vars.get("XF_API_SECRET", ""),
    "domain": env_vars.get("XF_DOMAIN", "ultra"),
    "multimodal_domain": env_vars.get("XF_MULTIMODAL_DOMAIN", "multimodal-v1"),
}

# 内容安全配置
XF_SAFETY_CONFIG = {
    "check_url": "https://rest-api.xfyun.cn/v1/solution/v1/text_audit",
    "timeout": 10
}