"""Cookie 管理模組。

提供 Cookie 的讀取、刷新、驗證等功能。
"""

from __future__ import annotations

import re
import time
from pathlib import Path
from urllib.parse import quote

import httpx

from . import config
from .color_print import err_print
from .constants import AnimeUrl


class CookieManager:
    """Cookie 管理器。

    負責 Cookie 的讀取、刷新、驗證和持久化。
    """

    def __init__(self, cfg: config.Config) -> None:
        """初始化 Cookie 管理器。

        Args:
            cfg: 配置物件
        """
        self._cfg = cfg
        self._cookies: dict[str, str] = {}

    def load_cookies(self) -> dict[str, str]:
        """從配置載入 Cookie。

        Returns:
            Cookie 字典
        """
        if not self._cfg.cookie or not self._cfg.cookie.strip():
            return {}

        cookie_str = self._cfg.cookie.strip()
        cookies = self._parse_cookie_string(cookie_str)

        if cookies:
            self._cookies = cookies

        return self._cookies

    def save_cookies(self, cookies: dict[str, str]) -> bool:
        """保存 Cookie 到配置。

        Args:
            cookies: Cookie 字典

        Returns:
            是否保存成功
        """
        cookie_str = self._cookies_to_string(cookies)

        try:
            # 更新配置
            cfg = config.get_config()
            cfg.cookie = cookie_str
            config.save_config(cfg)

            # 更新內存
            self._cookies = cookies

            err_print(0, "Cookie 保存", "Cookie 已保存到配置", status=2, no_sn=True, display=False)
            return True

        except Exception as e:
            err_print(
                0,
                "Cookie 保存失敗",
                f"發生異常: {e}",
                status=1,
                no_sn=True,
            )
            return False

    def refresh_cookies(self, current_cookies: dict[str, str]) -> dict[str, str]:
        """刷新 Cookie（向動畫瘋發送請求獲取新 Cookie）。

        Args:
            current_cookies: 當前的 Cookie

        Returns:
            刷新後的 Cookie
        """
        err_print(0, "Cookie 刷新", "開始刷新 Cookie", no_sn=True, display=False)

        try:
            # 使用當前 cookie 向動畫瘋首頁發送請求
            headers = {
                "User-Agent": self._cfg.ua,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.6",
            }

            with httpx.Client(follow_redirects=True, timeout=10) as client:
                # 設置現有 cookies
                for key, value in current_cookies.items():
                    client.cookies.set(key, value)

                # 訪問首頁觸發 cookie 刷新
                response = client.get(AnimeUrl.BASE, headers=headers)

                # 檢查 Set-Cookie header
                if "set-cookie" in response.headers:
                    set_cookie = response.headers.get("set-cookie", "")

                    # 如果收到刪除 cookie 的指令
                    if "deleted" in set_cookie:
                        err_print(
                            0,
                            "Cookie 刷新",
                            "收到 Cookie 刪除指令，可能需要重新登入",
                            status=1,
                            no_sn=True,
                        )
                        return current_cookies

                    # 獲取刷新後的 cookies
                    new_cookies = dict(client.cookies)

                    # 移除不需要的 cookie
                    new_cookies.pop("ckBH_lastBoard", None)

                    # 檢查是否成功刷新（有新的 BAHARUNE）
                    if "BAHARUNE" in new_cookies and new_cookies.get("BAHARUNE") != current_cookies.get("BAHARUNE"):
                        err_print(
                            0,
                            "Cookie 刷新",
                            f"Cookie 刷新成功，新 Cookie keys: {', '.join(new_cookies.keys())}",
                            status=2,
                            no_sn=True,
                            display=False,
                        )
                        return new_cookies

                # 沒有收到 set-cookie，返回原 cookies
                err_print(
                    0,
                    "Cookie 刷新",
                    "未收到新 Cookie，使用原有 Cookie",
                    no_sn=True,
                    display=False,
                )
                return current_cookies

        except Exception as e:
            err_print(
                0,
                "Cookie 刷新失敗",
                f"發生異常: {e}",
                status=1,
                no_sn=True,
            )
            return current_cookies

    def validate_cookies(self, cookies: dict[str, str]) -> bool:
        """驗證 Cookie 是否有效。

        Args:
            cookies: Cookie 字典

        Returns:
            Cookie 是否有效
        """
        # 基本驗證：檢查必要的 cookie 欄位
        if not cookies:
            return False

        # 檢查是否有用戶 cookie 或遊客 cookie
        has_user_cookie = "BAHAID" in cookies
        has_guest_cookie = "nologinuser" in cookies

        if not (has_user_cookie or has_guest_cookie):
            err_print(
                0,
                "Cookie 驗證",
                "Cookie 缺少必要欄位（BAHAID 或 nologinuser）",
                status=1,
                no_sn=True,
                display=False,
            )
            return False

        return True

    def is_vip_cookie(self, cookies: dict[str, str]) -> bool:
        """檢查是否為 VIP Cookie。

        Args:
            cookies: Cookie 字典

        Returns:
            是否為 VIP
        """
        # 這裡可以根據實際情況判斷
        # 通常可以通過發送請求檢查用戶資訊
        return "BAHAID" in cookies

    @staticmethod
    def _parse_cookie_string(cookie_str: str) -> dict[str, str]:
        """解析 Cookie 字串。

        Args:
            cookie_str: Cookie 字串（格式：key1=value1; key2=value2）

        Returns:
            Cookie 字典
        """
        try:
            cookies = dict(
                [
                    list(
                        map(
                            lambda x: quote(x, safe="")
                            if re.match(r"[\u4e00-\u9fa5]", x)
                            else x,
                            line.split("=", 1),
                        )
                    )
                    for line in cookie_str.split("; ")
                    if "=" in line
                ]
            )
            cookies.pop("ckBH_lastBoard", None)
            return cookies
        except Exception as e:
            err_print(
                0,
                "Cookie 解析失敗",
                f"解析錯誤: {e}",
                status=1,
                no_sn=True,
            )
            return {}

    @staticmethod
    def _cookies_to_string(cookies: dict[str, str]) -> str:
        """將 Cookie 字典轉換為字串。

        Args:
            cookies: Cookie 字典

        Returns:
            Cookie 字串
        """
        return "; ".join(f"{key}={value}" for key, value in cookies.items())

    def get_cookie_info(self) -> str:
        """獲取 Cookie 資訊摘要。

        Returns:
            Cookie 資訊字串
        """
        if not self._cookies:
            return "未載入 Cookie"

        cookie_keys = list(self._cookies.keys())
        is_vip = self.is_vip_cookie(self._cookies)

        info = f"Cookie Keys: {', '.join(cookie_keys)}"
        if is_vip:
            info += " (VIP)"
        else:
            info += " (一般用戶/遊客)"

        return info


class AutoCookieRefresher:
    """自動 Cookie 刷新器。

    定期檢查並刷新 Cookie，確保 Cookie 持續有效。
    """

    def __init__(
        self,
        cookie_manager: CookieManager,
        refresh_interval: int = 3600,  # 預設每小時刷新
    ) -> None:
        """初始化自動刷新器。

        Args:
            cookie_manager: Cookie 管理器
            refresh_interval: 刷新間隔（秒）
        """
        self._manager = cookie_manager
        self._refresh_interval = refresh_interval
        self._last_refresh = 0

    def should_refresh(self) -> bool:
        """檢查是否需要刷新。

        Returns:
            是否需要刷新
        """
        current_time = time.time()
        return (current_time - self._last_refresh) >= self._refresh_interval

    def refresh_if_needed(self, current_cookies: dict[str, str]) -> dict[str, str]:
        """如果需要則刷新 Cookie。

        Args:
            current_cookies: 當前 Cookie

        Returns:
            刷新後的 Cookie
        """
        if not self.should_refresh():
            return current_cookies

        new_cookies = self._manager.refresh_cookies(current_cookies)

        # 如果刷新成功，保存並更新時間戳
        if new_cookies != current_cookies:
            self._manager.save_cookies(new_cookies)

        self._last_refresh = time.time()
        return new_cookies
