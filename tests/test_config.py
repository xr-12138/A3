# tests/test_config.py
import sys
from pathlib import Path

# 修复 ModuleNotFoundError（关键代码）
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

# 现在可以正常导入了
from config import xfyun_config

def test_xfyun_config():
    """测试讯飞配置是否正确加载"""
    config = xfyun_config.XFYUN_CONFIG
    
    # 打印配置（调试用）
    print("讯飞配置加载成功：")
    print(f"APP_ID: {config['app_id']}")
    print(f"API_KEY: {config['api_key'][:5]}...")
    
    # 断言配置不为空
    assert config["app_id"] != ""
    assert config["api_key"] != ""
    assert config["api_secret"] != ""
    print("✅ 配置测试通过！")

if __name__ == "__main__":
    test_xfyun_config()
