"""共用工具模組。

提供重試處理、進度追蹤、驗證等共用功能。
"""

from __future__ import annotations

import random
import time
from typing import Any, Callable, TypeVar

from .color_print import err_print

T = TypeVar("T")


class RetryHandler:
    """重試處理器。

    提供統一的重試邏輯，支援指數退避和自訂錯誤處理。
    """

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 2.0,
        max_delay: float = 10.0,
        exponential_backoff: bool = True,
    ) -> None:
        """初始化重試處理器。

        Args:
            max_retries: 最大重試次數
            base_delay: 基礎延遲時間（秒）
            max_delay: 最大延遲時間（秒）
            exponential_backoff: 是否使用指數退避
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_backoff = exponential_backoff

    def execute(
        self,
        func: Callable[[], T],
        on_error: Callable[[Exception, int], None] | None = None,
        error_types: tuple[type[Exception], ...] = (Exception,),
    ) -> T:
        """執行函數並在失敗時重試。

        Args:
            func: 要執行的函數
            on_error: 錯誤回調函數，接收異常和重試次數
            error_types: 要捕獲的異常類型

        Returns:
            函數執行結果

        Raises:
            最後一次執行時的異常
        """
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                return func()
            except error_types as e:
                last_exception = e
                if attempt >= self.max_retries:
                    raise

                if on_error:
                    on_error(e, attempt)

                delay = self._calculate_delay(attempt)
                time.sleep(delay)

        # 這行理論上不會執行，但為了類型檢查
        raise last_exception  # type: ignore

    def _calculate_delay(self, attempt: int) -> float:
        """計算延遲時間。

        Args:
            attempt: 當前重試次數

        Returns:
            延遲時間（秒）
        """
        if self.exponential_backoff:
            delay = self.base_delay * (2**attempt)
        else:
            delay = self.base_delay

        # 添加隨機抖動
        jitter = random.uniform(0, delay * 0.1)
        delay = min(delay + jitter, self.max_delay)

        return delay


class ProgressTracker:
    """進度追蹤器。

    用於追蹤和報告任務進度。
    """

    def __init__(self, sn: int | str, total: int = 100) -> None:
        """初始化進度追蹤器。

        Args:
            sn: 任務序號
            total: 總進度值（預設 100 表示百分比）
        """
        self.sn = sn
        self.total = total
        self.current = 0

    def update(self, value: int, status: str = "") -> None:
        """更新進度。

        Args:
            value: 當前進度值
            status: 狀態描述
        """
        self.current = value
        # 更新全域進度追蹤
        import config

        if int(self.sn) in config.tasks_progress_rate:
            config.tasks_progress_rate[int(self.sn)]["rate"] = (
                self.current / self.total * 100
            )
            if status:
                config.tasks_progress_rate[int(self.sn)]["status"] = status

    def increment(self, step: int = 1) -> None:
        """增加進度。

        Args:
            step: 增加量
        """
        self.current = min(self.current + step, self.total)
        self.update(self.current)

    def get_percentage(self) -> float:
        """獲取進度百分比。

        Returns:
            進度百分比（0-100）
        """
        return (self.current / self.total) * 100


class ValidationHelper:
    """驗證輔助工具。

    提供各種參數驗證和防呆處理功能。
    """

    @staticmethod
    def ensure_positive_int(value: Any, default: int = 1, field_name: str = "") -> int:
        """確保值為正整數。

        Args:
            value: 輸入值
            default: 預設值
            field_name: 欄位名稱（用於錯誤訊息）

        Returns:
            驗證後的正整數
        """
        try:
            result = int(value)
            if result <= 0:
                if field_name:
                    err_print(
                        0,
                        f"參數驗證",
                        f"{field_name} 必須為正整數，使用預設值 {default}",
                        status=1,
                        no_sn=True,
                    )
                return default
            return result
        except (ValueError, TypeError):
            if field_name:
                err_print(
                    0,
                    f"參數驗證",
                    f"{field_name} 格式錯誤，使用預設值 {default}",
                    status=1,
                    no_sn=True,
                )
            return default

    @staticmethod
    def ensure_non_empty_string(value: Any, default: str = "", field_name: str = "") -> str:
        """確保值為非空字串。

        Args:
            value: 輸入值
            default: 預設值
            field_name: 欄位名稱

        Returns:
            驗證後的字串
        """
        if not value or not str(value).strip():
            if field_name and default:
                err_print(
                    0,
                    f"參數驗證",
                    f"{field_name} 不能為空，使用預設值",
                    status=1,
                    no_sn=True,
                )
            return default
        return str(value).strip()

    @staticmethod
    def validate_resolution(resolution: str | int) -> str:
        """驗證影片解析度。

        Args:
            resolution: 解析度值

        Returns:
            驗證後的解析度字串
        """
        valid_resolutions = ["360", "480", "540", "576", "720", "1080"]
        resolution_str = str(resolution)

        if resolution_str not in valid_resolutions:
            err_print(
                0,
                "參數驗證",
                f"解析度 {resolution} 無效，使用預設值 1080",
                status=1,
                no_sn=True,
            )
            return "1080"

        return resolution_str

    @staticmethod
    def validate_download_mode(mode: str) -> str:
        """驗證下載模式。

        Args:
            mode: 下載模式

        Returns:
            驗證後的下載模式
        """
        valid_modes = ["all", "latest", "largest-sn", "single"]

        if mode not in valid_modes:
            err_print(
                0,
                "參數驗證",
                f"下載模式 {mode} 無效，使用預設值 latest",
                status=1,
                no_sn=True,
            )
            return "latest"

        return mode
