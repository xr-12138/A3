# /home/hjj/桌面/A3-main/diagnose_api.py
"""
AI API 连接诊断工具
=====================

用途
----
快速确认 config/.env 中的 OPENAI_API_KEY / OPENAI_API_URL / OPENAI_MODEL
是否真的能连接到讯飞星火 OpenAI 兼容接口。

运行方式
--------
    cd /home/hjj/桌面/A3-main
    python diagnose_api.py

它会做三件事：
    1. 解析 config/.env，打印实际读到的配置
    2. 检查 DNS 与网络连通性
    3. 发起一次真实的 chat/completions 请求
    4. 根据服务端响应给出明确的诊断结论
"""

from __future__ import annotations

import json
import os
import socket
import sys
from pathlib import Path
from urllib.parse import urlparse

import requests


# 脚本位于项目根目录，config/.env 相对当前文件的父级同级
ENV_PATH = Path(__file__).resolve().parent / "config" / ".env"


def load_env(path: Path) -> dict:
    """读取 .env 并把读到的键值同时写入 os.environ 与返回 dict。"""
    cfg: dict = {}
    if not path.exists():
        print(f"[X] 找不到配置文件: {path}")
        return cfg

    # --- 优先使用 python-dotenv（更鲁棒）
    try:
        from dotenv import dotenv_values  # type: ignore
        raw = dotenv_values(str(path))
        for k, v in raw.items():
            if v is not None:
                cfg[k] = str(v)
                os.environ[k] = str(v)
        print(f"[OK] python-dotenv 解析到 {len(cfg)} 项配置")
        return cfg
    except Exception as exc:
        print(f"[!] python-dotenv 不可用 ({exc})，回退手动解析")

    # --- 手动解析（不依赖第三方库）
    with open(path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            # 剥去外层引号（支持 "..." 和 '...'）
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                value = value[1:-1]
            if not key:
                continue
            cfg[key] = value
            os.environ[key] = value
    print(f"[OK] 手动解析到 {len(cfg)} 项配置")
    return cfg


def check_network(api_url: str) -> int:
    """尝试建立一次 TCP 连接检查 DNS + 网络是否可达。返回 0=OK，非 0=失败。"""
    host = urlparse(api_url).netloc
    print(f"[1] 检查网络 -> {host}")
    try:
        # 只取主机部分（去掉可能存在的端口号），用 5 秒超时；
        # 注意：不用 socket.setdefaulttimeout，避免污染全局 socket 行为
        hostname = host.split(":", 1)[0]
        sock = socket.create_connection((hostname, 443), timeout=5)
        sock[0].close()
        print(f"    TCP 连接成功")
        return 0
    except socket.gaierror as exc:
        print(f"    [X] DNS 解析失败: {exc}")
        print("    提示: 检查是否能访问外网，或 OPENAI_API_URL 是否正确")
        return 2
    except (socket.timeout, OSError) as exc:
        print(f"    [X] 无法连接: {exc}")
        print("    提示: 防火墙阻断 / 服务器未开放 / 本地断网")
        return 3


def main() -> int:
    print("=" * 60)
    print("  AI API 连接诊断")
    print("=" * 60)

    cfg = load_env(ENV_PATH)
    api_key = cfg.get("OPENAI_API_KEY", "").strip()
    api_url = cfg.get("OPENAI_API_URL", "").strip()
    model = cfg.get("OPENAI_MODEL", "").strip()

    print()
    print(f"  API URL   : {api_url or '(空)'}")
    key_preview = (
        api_key[:6] + "****" + api_key[-6:]
        if len(api_key) > 12
        else "(空或太短)"
    )
    print(f"  API KEY   : {key_preview}")
    print(f"  MODEL     : {model or '(空)'}")
    print()

    if not api_key or not api_url or not model:
        print("[X] 有配置项为空，请检查 config/.env")
        return 1

    # Step 1: 网络连通性
    rc = check_network(api_url)
    if rc != 0:
        return rc

    # Step 2: 真实 chat/completions 请求
    print(f"[2] 发起一次真实的 chat/completions 请求 ...")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "你好，请用一句话回答。"}],
        "stream": False,
    }
    print(f"    发送: model={model!r}")

    try:
        resp = requests.post(api_url, json=payload, headers=headers, timeout=30)
    except requests.exceptions.ConnectionError as exc:
        print(f"    [X] HTTP 连接失败: {exc}")
        return 4
    except requests.exceptions.Timeout:
        print(f"    [X] 请求超时 (30s)")
        return 5
    except requests.exceptions.RequestException as exc:
        print(f"    [X] 请求异常: {exc}")
        return 6

    print(f"    HTTP 状态码: {resp.status_code} {resp.reason}")

    # Step 3: 根据状态码给结论
    if resp.status_code == 200:
        try:
            body = resp.json()
        except Exception:
            print(f"    [X] 响应体不是 JSON: {resp.text[:300]!r}")
            return 7

        choices = body.get("choices")
        if isinstance(choices, list) and choices:
            first = choices[0]
            if isinstance(first, dict):
                answer = first.get("message", {}).get("content", "")
            else:
                answer = str(first)
            print(f"    [OK] 成功！模型回答: {answer[:200]!r}")
            print()
            print("=" * 60)
            print("✅ API 完全正常，可以直接使用项目。")
            print("=" * 60)
            return 0
        print(
            f"    [!] 状态码 200 但没有 choices。"
            f"原始响应: {json.dumps(body, ensure_ascii=False, indent=2)[:500]}"
        )
        return 8

    # 非 200
    print()
    print("=" * 60)
    if resp.status_code in (401, 403):
        print("❌ 鉴权失败 (HTTP 401/403)。常见原因:")
        print("   - OPENAI_API_KEY 写错 / 已过期")
        print("   - API Key 没有开通当前模型（OPENAI_MODEL）的调用权限")
        print("   - 账号余额不足")
    elif resp.status_code == 400:
        print("❌ 请求参数错误 (HTTP 400)。常见原因:")
        print("   - OPENAI_MODEL 不是服务端认可的模型名")
        print("   - messages 格式不合法")
    elif resp.status_code >= 500:
        print("❌ 服务端内部错误，可能是讯飞侧故障，稍后重试")
    else:
        print(f"❌ 未处理的 HTTP {resp.status_code}")

    print()
    print("服务端返回的完整响应（用于诊断）:")
    try:
        print(json.dumps(resp.json(), ensure_ascii=False, indent=2))
    except Exception:
        print(resp.text[:800])

    return 9


if __name__ == "__main__":
    sys.exit(main())
