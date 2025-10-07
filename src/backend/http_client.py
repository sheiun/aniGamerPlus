"""HTTP 客戶端模組。

提供統一的 HTTP 請求處理，包含 cookie 管理和錯誤重試。
"""

from __future__ import annotations

import random
import time
from typing import Any

import httpx

from . import config
from .color_print import err_print
from .constants import AnimeUrl, HttpHeader, RetryConfig, Timeout
from .utils import RetryHandler


class TryTooManyTimeError(BaseException):
    """重試次數過多異常。"""


class CookieUpdateFailedError(Exception):
    """Cookie 更新失敗異常。

    當啟用 disable_guest_mode 且 cookie 更新失敗時拋出。
    """


class HttpClient:
    """HTTP 客戶端類別。

    封裝 httpx 客戶端，提供請求管理、cookie 處理和自動重試功能。
    """

    def __init__(self, sn: int | str, cfg: config.Config) -> None:
        """初始化 HTTP 客戶端。

        Args:
            sn: 影片序號
            cfg: 配置物件
        """
        self._sn = str(sn)
        self._cfg = cfg
        self._cookies: dict[str, str] = {}
        self._proxies: dict[str, str] = {}

        # 創建 httpx 客戶端
        self._httpx_client = httpx.Client(
            timeout=Timeout.HTTP_REQUEST,
            follow_redirects=True,
        )

        # 初始化 headers
        self._web_header: dict[str, str] = {}
        self._mobile_header: dict[str, str] = {}
        self._req_header: dict[str, str] = {}

    def init_headers(self, use_mobile: bool = False) -> None:
        """初始化 HTTP headers。

        Args:
            use_mobile: 是否使用手機 API header
        """
        host = "ani.gamer.com.tw"
        origin = f"https://{host}"
        ref = f"{origin}/animeVideo.php?sn={self._sn}"

        # Web header
        self._web_header = {
            "User-Agent": self._cfg.ua,
            "referer": ref,
            "Origin": origin,
            **HttpHeader.WEB_COMMON,
        }

        # Mobile header
        self._mobile_header = HttpHeader.MOBILE_API.copy()

        # 選擇使用的 header
        self._req_header = self._mobile_header if use_mobile else self._web_header

    def set_cookies(self, cookies: dict[str, str]) -> None:
        """設定 cookies。

        Args:
            cookies: cookie 字典
        """
        self._cookies = cookies

    def set_proxies(self, proxies: dict[str, str]) -> None:
        """設定代理。

        Args:
            proxies: 代理字典
        """
        self._proxies = proxies

    def request(
        self,
        url: str,
        *,
        no_cookies: bool = False,
        show_fail: bool = True,
        max_retry: int = RetryConfig.MAX_REQUEST_RETRY,
        additional_headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """發送 HTTP GET 請求。

        Args:
            url: 請求 URL
            no_cookies: 是否不使用 cookies
            show_fail: 是否顯示失敗訊息
            max_retry: 最大重試次數
            additional_headers: 額外的 headers

        Returns:
            HTTP 回應

        Raises:
            TryTooManyTimeError: 重試次數過多
        """
        # 準備 headers
        current_header = self._req_header.copy()
        if additional_headers:
            current_header.update(additional_headers)

        # 準備 cookies
        cookies = {} if no_cookies else self._cookies

        # 定義請求函數
        def do_request() -> httpx.Response:
            if self._proxies:
                proxy_url = self._proxies.get("http") or self._proxies.get("https")
                return self._httpx_client.get(
                    url,
                    headers=current_header,
                    cookies=cookies,
                    proxies=proxy_url,
                )
            return self._httpx_client.get(url, headers=current_header, cookies=cookies)

        # 定義錯誤處理
        def on_error(e: Exception, attempt: int) -> None:
            if show_fail:
                err_print(
                    self._sn,
                    "任務狀態",
                    f"請求失敗！{e}\n3s後重試（最多重試{max_retry}次）",
                )

        # 使用重試處理器
        retry_handler = RetryHandler(max_retries=max_retry, base_delay=3.0)

        try:
            response = retry_handler.execute(
                do_request,
                on_error=on_error,
                error_types=(httpx.HTTPError,),
            )
        except httpx.HTTPError:
            raise TryTooManyTimeError(
                f"任務狀態: sn={self._sn} 請求失敗次數過多！請求鏈接：\n{url}"
            )

        # 處理 cookie
        self._handle_cookie_response(response)

        return response

    def request_json(
        self,
        url: str,
        *,
        no_cookies: bool = False,
        show_fail: bool = True,
        max_retry: int = RetryConfig.MAX_REQUEST_RETRY,
        additional_headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """發送 HTTP GET 請求並返回 JSON。

        Args:
            url: 請求 URL
            no_cookies: 是否不使用 cookies
            show_fail: 是否顯示失敗訊息
            max_retry: 最大重試次數
            additional_headers: 額外的 headers

        Returns:
            JSON 回應資料
        """
        response = self.request(
            url,
            no_cookies=no_cookies,
            show_fail=show_fail,
            max_retry=max_retry,
            additional_headers=additional_headers,
        )
        return response.json()

    def _handle_cookie_response(self, response: httpx.Response) -> None:
        """處理回應中的 cookie 更新。

        Args:
            response: HTTP 回應
        """
        # 初始化 cookies
        if not self._cookies:
            self._cookies = dict(self._httpx_client.cookies)
            return

        # 處理遊客 cookie
        if (
            "nologinuser" not in self._cookies
            and "BAHAID" not in self._cookies
            and "nologinuser" in self._httpx_client.cookies
        ):
            self._cookies = dict(self._httpx_client.cookies)
            return

        # 處理 cookie 刷新
        if "set-cookie" not in response.headers:
            return

        set_cookie = response.headers.get("set-cookie", "")

        if "deleted" in set_cookie:
            self._handle_cookie_deleted()
        else:
            self._handle_cookie_refresh(set_cookie)

    def _handle_cookie_deleted(self) -> None:
        """處理 cookie 被刪除的情況。"""
        # 使用移動 API 無法刷新 cookie，切換回 Web header
        if (
            self._cfg.use_mobile_api
            and "X-Bahamut-App-Android" in self._req_header
        ):
            err_print(self._sn, "嘗試切換回 Web Header 刷新 Cookie", display=False)
            self._req_header = self._web_header
            self.request(AnimeUrl.BASE)
        else:
            err_print(self._sn, "收到cookie重置響應", display=False)
            self._wait_for_cookie_refresh()

    def _wait_for_cookie_refresh(self) -> None:
        """等待其他線程刷新 cookie。"""
        time.sleep(2)

        for attempt in range(3):
            old_cookie_value = self._cookies.get("BAHARUNE", "")
            self._cookies = config.read_cookie()

            err_print(
                self._sn,
                "讀取cookie",
                f"cookie.txt最後修改時間: {config.get_cookie_time()} 第{attempt}次嘗試",
                display=False,
            )

            if old_cookie_value != self._cookies.get("BAHARUNE", ""):
                err_print(self._sn, "讀取cookie", "新cookie讀取成功", display=False)
                return

            err_print(self._sn, "讀取cookie", "新cookie讀取失敗", display=False)
            time.sleep(random.uniform(2, 5))

        # 三次嘗試後仍失敗
        if self._cfg.disable_guest_mode:
            # 不使用遊客模式：拋出異常，保持 cookies 不變
            err_print(
                0,
                "用戶cookie更新失敗! 因設定不使用遊客帳號，暫停下載",
                status=1,
                no_sn=True,
            )
            config.invalid_cookie()
            raise CookieUpdateFailedError("Cookie 更新失敗，且已設定不使用遊客帳號")

        # 使用遊客模式：清空 cookies
        self._cookies = {}
        err_print(0, "用戶cookie更新失敗! 使用遊客身份訪問", status=1, no_sn=True)
        config.invalid_cookie()

        # 恢復 mobile header
        if self._cfg.use_mobile_api and "X-Bahamut-App-Android" not in self._req_header:
            self._req_header = self._mobile_header

    def _handle_cookie_refresh(self, set_cookie: str) -> None:
        """處理 cookie 刷新。

        Args:
            set_cookie: Set-Cookie header 內容
        """
        err_print(self._sn, "收到新cookie", display=False)

        self._cookies.update(dict(self._httpx_client.cookies))
        config.renew_cookies(self._cookies, log=False)

        key_list_str = ", ".join(self._httpx_client.cookies.keys())
        err_print(self._sn, f"用戶cookie刷新 {key_list_str}", display=False)

        self.request(AnimeUrl.BASE)

        # 檢查是否完整刷新
        if "BAHARUNE" in set_cookie:
            err_print(0, "用戶cookie已更新", status=2, no_sn=True)
            if self._cfg.use_mobile_api:
                self._req_header = self._mobile_header
                err_print(self._sn, "切換回 App Header 進行影片解析", display=False)

    def close(self) -> None:
        """關閉 HTTP 客戶端。"""
        self._httpx_client.close()
