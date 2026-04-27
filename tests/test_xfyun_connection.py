"""简单配置检查：验证是否配置了本地 Ollama/AI API 入口（不会进行网络调用）。"""

from pathlib import Path


def load_env():
    env_path = Path(__file__).resolve().parent.parent / "config" / ".env"
    if not env_path.exists():
        return {}
    cfg = {}
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' not in line:
                continue
            k, v = line.split('=', 1)
            cfg[k] = v.strip().strip('"').strip("'")
    return cfg


def test_ollama_config_exists():
    cfg = load_env()
    # 只做静态检查：确保 XF_API_URL 在配置中存在
    assert 'XF_API_URL' in cfg and cfg['XF_API_URL'], "XF_API_URL 未在 config/.env 中配置"


if __name__ == '__main__':
    c = load_env()
    print('XF_API_URL=' + c.get('XF_API_URL', ''))
    try:
        test_ollama_config_exists()
        print('配置检查通过')
    except AssertionError as e:
        print('配置检查失败:', e)