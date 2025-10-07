"""彩色終端輸出工具模組。

此模組提供彩色終端輸出和日誌記錄功能，支援 Windows 和 Unix-like 系統。

Functions:
    read_log_settings: 讀取日誌配置
    err_print: 列印彩色狀態訊息並記錄到日誌檔案

Classes:
    WindowsColorPrinter: Windows 主控台彩色輸出工具
"""

from __future__ import annotations

import ctypes
import platform
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from termcolor import cprint

from . import config

StatusType = Literal[0, 1, 2]


def read_log_settings() -> dict[str, Any]:
    """讀取日誌配置。

    從配置檔案讀取日誌相關設定，若讀取失敗則使用預設值。

    Returns:
        包含 save_logs 和 quantity_of_logs 的配置字典
    """
    settings: dict[str, Any] = {"save_logs": True, "quantity_of_logs": 7}

    try:
        # 使用新的 TOML 配置系統
        from .config_manager import load_config

        cfg = load_config()
        settings["save_logs"] = cfg.save_logs
        settings["quantity_of_logs"] = cfg.quantity_of_logs
    except Exception as e:
        # 若讀取失敗則靜默使用默認值（避免循環導入問題）
        pass

    return settings


log_settings = read_log_settings()


def err_print(
    sn: int | str,
    err_msg: str,
    detail: str = "",
    *,
    status: StatusType = 0,
    no_sn: bool = False,
    prefix: str = "",
    display: bool = True,
    display_time: bool = True,
) -> None:
    """列印彩色狀態訊息並記錄到日誌。

    Args:
        sn: 序號（SN碼）
        err_msg: 訊息類型/摘要（建議使用四個中文字）
        detail: 詳細描述
        status: 訊息狀態 (0=一般, 1=錯誤(紅色), 2=成功(綠色))
        no_sn: 是否列印 SN，預設會列印
        prefix: 訊息前綴
        display: 是否在主控台顯示（False 則僅記錄到日誌檔案）
        display_time: 是否顯示時間戳記

    Example:
        2019-01-30 17:22:30 更新狀態: sn=12345 檢查更新失敗, 跳過等待下次檢查
    """

    def succeed_or_failed_print(msg: str, green: bool) -> None:
        """Print colored text for success/failure."""
        check_tty = subprocess.Popen(
            "tty",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if not check_tty.stdout:
            return
        check_tty_return_str = check_tty.stdout.read().decode("utf-8").rstrip()

        if "Windows" in platform.system() and check_tty_return_str in (
            "/dev/cons0",
            "",
        ):
            color_printer = WindowsColorPrinter()
            if green:
                color_printer.print_green_text(msg)
            else:
                color_printer.print_red_text(msg)
        elif green:
            cprint(msg, "green", attrs=["bold"])
        else:
            cprint(msg, "red", attrs=["bold"])

    # Build message
    time_prefix = (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " " if display_time else ""
    )
    msg = f"{prefix}{time_prefix}"

    if no_sn:
        msg = f"{msg}{err_msg} {detail}"
    else:
        msg = f"{msg}{err_msg}: sn={sn}\t{detail}"

    # Display to console
    if display:
        if status == 0:
            print(msg)
        elif status == 1:
            succeed_or_failed_print(msg, green=False)
        else:  # status == 2
            succeed_or_failed_print(msg, green=True)

    # Write to log file
    if log_settings.get("save_logs", True):
        try:
            logs_dir = Path(config.get_working_dir()) / "logs"
            logs_dir.mkdir(parents=True, exist_ok=True)

            log_path = logs_dir / f"{datetime.now().strftime('%Y-%m-%d')}.log"
            # Use append mode to avoid reading existing content
            with log_path.open("a", encoding="utf-8", errors="replace") as f:
                f.write(msg + "\n")
        except Exception:
            # Silently ignore log writing errors to prevent cascading failures
            pass


class WindowsColorPrinter:
    """Windows 主控台彩色輸出工具。

    使用 Windows API 實現主控台文字的彩色輸出。

    基於：https://blog.csdn.net/five3/article/details/7630295
    參考：http://msdn.microsoft.com/library/default.asp?url=/library/en-us/winprog/winprog/windows_api_reference.asp
    """

    FOREGROUND_RED = 0x04
    FOREGROUND_GREEN = 0x02
    FOREGROUND_BLUE = 0x01
    FOREGROUND_INTENSITY = 0x08
    STD_OUTPUT_HANDLE = -11

    def __init__(self) -> None:
        """Initialize Windows color printer."""
        self.handle = ctypes.windll.kernel32.GetStdHandle(self.STD_OUTPUT_HANDLE)  # type: ignore[attr-defined]

    def set_cmd_color(self, color: int) -> bool:
        """Set console text color.

        Example: set_cmd_color(FOREGROUND_RED | FOREGROUND_GREEN | FOREGROUND_BLUE | FOREGROUND_INTENSITY)
        """
        return bool(ctypes.windll.kernel32.SetConsoleTextAttribute(self.handle, color))  # type: ignore[attr-defined]

    def reset_color(self) -> None:
        """Reset console color to default."""
        self.set_cmd_color(
            self.FOREGROUND_RED | self.FOREGROUND_GREEN | self.FOREGROUND_BLUE
        )

    def print_red_text(self, text: str) -> None:
        """Print text in red."""
        self.set_cmd_color(self.FOREGROUND_RED | self.FOREGROUND_INTENSITY)
        print(text)
        self.reset_color()

    def print_green_text(self, text: str) -> None:
        """Print text in green."""
        self.set_cmd_color(self.FOREGROUND_GREEN | self.FOREGROUND_INTENSITY)
        print(text)
        self.reset_color()
