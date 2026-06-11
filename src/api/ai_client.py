from __future__ import annotations

from pathlib import Path
import os

from .openai_client import OpenAIClient


ENV_PATH = Path(__file__).resolve().parent.parent.parent / "config" / ".env"


def _load_env() -> dict:
    """Load key/value pairs from ``config/.env`` and inject them into
    ``os.environ`` so libraries that read environment variables directly also
    pick them up. Returns the parsed dictionary (empty if the file is missing
    or unreadable).

    If ``python-dotenv`` is installed it is used for robust parsing; otherwise
    we fall back to a small manual parser so the project keeps working with
    only the standard library.
    """
    cfg: dict = {}
    if not ENV_PATH.exists():
        print(f"[警告] 未找到配置文件: {ENV_PATH}")
        return cfg

    # --- 1) Try python-dotenv first. Parameter names differ across versions.
    parsed_ok = False
    try:
        from dotenv import load_dotenv, dotenv_values  # type: ignore

        # Different python-dotenv versions accept different kwargs.
        tried = False
        for kwargs in (
            {"path": ENV_PATH, "override": True},
            {"dotenv_path": ENV_PATH, "override": True},
            {"path": ENV_PATH},
        ):
            try:
                load_dotenv(**kwargs)
                tried = True
                break
            except TypeError:
                continue
        if not tried:
            # Extremely old / odd version — try positional call.
            try:
                load_dotenv(ENV_PATH)  # type: ignore[call-arg]
            except Exception:
                pass

        # Mirror into the ``cfg`` dict AND explicitly write to os.environ
        # so downstream code such as ``os.getenv('OPENAI_API_KEY')
        # (e.g. OpenAIClient._load_config) sees the values even if ``load_dotenv``
        # returned False silently on some python-dotenv versions.
        try:
            raw = dotenv_values(ENV_PATH)
            for k, v in raw.items():
                if v is not None:
                    cfg[k] = str(v)
                    os.environ[k] = str(v)
            parsed_ok = len(cfg) > 0
        except Exception:
            pass

        print(f"[信息] 使用 python-dotenv 解析: 读取 {len(cfg)} 项")
    except Exception:
        parsed_ok = False

    # --- 2) Fallback: hand-rolled parser (no 3rd-party deps). Always override
    # os.environ so the shell cannot silently mask the project's configuration.
    if not parsed_ok:
        try:
            with open(ENV_PATH, 'r', encoding='utf-8') as f:
                for raw_line in f:
                    line = raw_line.strip()
                    if not line or line.startswith('#') or '=' not in line:
                        continue
                    key, _, value = line.partition('=')
                    key = key.strip()
                    value = value.strip()
                    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                        value = value[1:-1]
                    if not key:
                        continue
                    cfg[key] = value
                    # Always override — the .env file is the source of truth.
                    os.environ[key] = value
            print(f"[信息] 使用手动解析器: 读取 {len(cfg)} 项")
        except Exception as exc:
            print(f"[错误] 无法读取 {ENV_PATH}: {exc}")

    # --- 3) Echo the resolved values (safe, they are not secrets in a dev env
    # where the user needs to debug why the API isn't connecting).
    if cfg:
        print("[信息] 解析结果:")
        for k in ("OPENAI_API_URL", "OPENAI_MODEL", "OPENAI_API_KEY"):
            if k in cfg:
                val = cfg[k]
                # Mask the middle of the API key so it's still identifiable
                # as the right shape but not leaked to logs verbatim.
                if k == "OPENAI_API_KEY" and len(val) > 8:
                    shown = val[:4] + "****" + val[-4:]
                else:
                    shown = val
                print(f"       {k} = {shown}")
    else:
        print(f"[警告] 未能从 {ENV_PATH} 读取到任何配置项。")

    return cfg


def get_ai_client() -> OpenAIClient:
    """Return an :class:`OpenAIClient` configured from ``config/.env``.

    We no longer fall back to a MockClient. If the API key / URL is missing or
    the remote service is unreachable, the returned client will produce clear
    error text like ``[AI错误: ...]`` instead of silently emitting canned
    sample content.
    """
    cfg = _load_env()
    client = OpenAIClient(cfg=cfg)
    has_key = bool(os.getenv('OPENAI_API_KEY') or cfg.get('OPENAI_API_KEY'))
    if not has_key:
        print(
            "[警告] 未检测到 OPENAI_API_KEY。客户端仍会尝试连接配置的 API，"
            "但所有调用将返回连接错误信息。请编辑 config/.env 填入密钥。"
        )
    return client