"""Compatibility shim: re-export API client implementations.

旧代码从 `src.frontend.clients` 导入 `MockClient` / `BaseAIClient`，
现在统一维护在 `src.api` 包中，这里做一层简单重导出以免破坏导入链。
"""

from src.api.mock_client import MockClient  # type: ignore
from src.api.base import BaseAIClient  # type: ignore

__all__ = ["MockClient", "BaseAIClient"]
