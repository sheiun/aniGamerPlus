"""配置管理模組。

負責讀取和寫入 TOML 格式的配置文件。
"""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path

import tomli_w

from .schema import Config

# 工作目錄
if getattr(sys, "frozen", False):
    WORKING_DIR = Path(sys.executable).parent
else:
    # 從 src/backend 回到專案根目錄
    WORKING_DIR = Path(__file__).parent.parent.parent

CONFIG_PATH = WORKING_DIR / "config.toml"


def load_config() -> Config:
    """從 TOML 文件載入配置。

    Returns:
        Config: 配置對象
    """
    from .schema import CoolQSettings, DashboardConfig, FTPConfig

    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"配置文件不存在: {CONFIG_PATH}")

    with CONFIG_PATH.open("rb") as f:
        data = tomllib.load(f)

    # 處理嵌套的 dataclass
    if "dashboard" in data and isinstance(data["dashboard"], dict):
        data["dashboard"] = DashboardConfig(**data["dashboard"])

    if "ftp" in data and isinstance(data["ftp"], dict):
        data["ftp"] = FTPConfig(**data["ftp"])

    if "coolq" in data and isinstance(data["coolq"], dict):
        data["coolq"] = CoolQSettings(**data["coolq"])

    return Config(**data)


def save_config(config: Config) -> None:
    """將配置保存到 TOML 文件。

    Args:
        config: 配置對象
    """
    from dataclasses import asdict

    config_dict = asdict(config)

    with CONFIG_PATH.open("wb") as f:
        tomli_w.dump(config_dict, f)
