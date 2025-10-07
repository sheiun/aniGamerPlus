"""M3U8 解析器模組。

負責處理動畫瘋的 M3U8 播放列表解析、廣告處理等功能。
"""

from __future__ import annotations

import random
import re
import sys
import time

from . import config
from .color_print import err_print
from .constants import AdConfig, AnimeUrl
from .http_client import HttpClient


class M3U8Parser:
    """M3U8 解析器。

    處理動畫瘋的影片解析流程，包含設備 ID 獲取、廣告處理、播放列表解析等。
    """

    def __init__(self, sn: int | str, http_client: HttpClient, cfg: config.Config) -> None:
        """初始化 M3U8 解析器。

        Args:
            sn: 影片序號
            http_client: HTTP 客戶端
            cfg: 配置物件
        """
        self._sn = str(sn)
        self._client = http_client
        self._cfg = cfg
        self._device_id = ""
        self._playlist: dict = {}
        self._m3u8_dict: dict[str, str] = {}

    def parse(self, title: str) -> dict[str, str]:
        """解析 M3U8 播放列表。

        Args:
            title: 影片標題

        Returns:
            M3U8 字典，格式為 {解析度: m3u8_url}
        """
        self._get_device_id()
        user_info = self._gain_access()

        # 處理錯誤反饋
        if "error" in user_info:
            self._handle_error(user_info, title)

        # 處理非 VIP 用戶廣告
        if not user_info.get("vip", False):
            self._handle_non_vip_ads(title)
        else:
            err_print(
                self._sn,
                "開始下載",
                f"《{title}》 識別到VIP賬戶, 立即下載",
            )

        # Web API 需要額外步驟
        if not self._cfg.use_mobile_api:
            self._unlock()
            self._check_lock()
            self._unlock()
            self._unlock()
            self._video_start()
            self._check_no_ad()

        self._get_playlist()
        self._parse_playlist()

        return self._m3u8_dict

    def _get_device_id(self) -> None:
        """獲取設備 ID。"""
        response = self._client.request_json(AnimeUrl.DEVICE_ID)
        self._device_id = response["deviceid"]

    def _gain_access(self) -> dict:
        """獲取訪問權限。

        Returns:
            用戶資訊字典
        """
        if self._cfg.use_mobile_api:
            url = (
                f"{AnimeUrl.MOBILE_API}/v3/token.php"
                f"?adID=0&sn={self._sn}&device={self._device_id}"
            )
        else:
            random_hash = self._generate_random_string(12)
            url = (
                f"{AnimeUrl.TOKEN}"
                f"?adID=0&sn={self._sn}&device={self._device_id}&hash={random_hash}"
            )

        return self._client.request_json(url)

    def _unlock(self) -> None:
        """解鎖影片。"""
        url = f"{AnimeUrl.UNLOCK}?sn={self._sn}&ttl=0"
        self._client.request(url)

    def _check_lock(self) -> None:
        """檢查鎖定狀態。"""
        url = f"{AnimeUrl.CHECK_LOCK}?device={self._device_id}&sn={self._sn}"
        self._client.request(url)

    def _start_ad(self) -> None:
        """開始廣告。"""
        if self._cfg.use_mobile_api:
            url = f"{AnimeUrl.MOBILE_API}/v1/stat_ad.php?schedule=-1&sn={self._sn}"
        else:
            url = f"{AnimeUrl.VIDEO_AD}?sn={self._sn}&s=194699"

        self._client.request(url)

    def _skip_ad(self) -> None:
        """跳過廣告。"""
        if self._cfg.use_mobile_api:
            url = f"{AnimeUrl.MOBILE_API}/v1/stat_ad.php?schedule=-1&ad=end&sn={self._sn}"
        else:
            url = f"{AnimeUrl.VIDEO_AD}?sn={self._sn}&s=194699&ad=end"

        self._client.request(url)

    def _video_start(self) -> None:
        """影片開始。"""
        url = f"{AnimeUrl.VIDEO_START}?sn={self._sn}"
        self._client.request(url)

    def _check_no_ad(self, retry_count: int = AdConfig.AD_CHECK_MAX_RETRY) -> None:
        """檢查廣告是否已去除。

        Args:
            retry_count: 剩餘重試次數
        """
        if retry_count == 0:
            err_print(self._sn, "廣告去除失敗! 請向開發者提交 issue!", status=1)
            sys.exit(1)

        random_hash = self._generate_random_string(12)
        url = f"{AnimeUrl.TOKEN}?sn={self._sn}&device={self._device_id}&hash={random_hash}"
        response = self._client.request_json(url)

        if "time" not in response:
            err_print(
                self._sn,
                "遭到動畫瘋地區限制, 你的IP可能不被動畫瘋認可!",
                status=1,
            )
            sys.exit(1)

        if response["time"] != 1:
            err_print(
                self._sn,
                f"廣告似乎還沒去除, 追加等待2秒, 剩餘重試次數 {retry_count}",
                status=1,
            )
            time.sleep(2)
            self._skip_ad()
            self._video_start()
            self._check_no_ad(retry_count - 1)
        elif retry_count != AdConfig.AD_CHECK_MAX_RETRY:
            # 通過廣告檢查，記錄實際廣告時間
            ad_time = self._get_current_ad_time()
            ads_time = (AdConfig.AD_CHECK_MAX_RETRY - retry_count) * 2 + ad_time + 2
            err_print(
                self._sn,
                f"通過廣告時間{ads_time}秒, 記錄到配置檔案",
                status=2,
            )
            self._save_ad_time(ads_time)

    def _get_playlist(self) -> None:
        """獲取播放列表。"""
        if self._cfg.use_mobile_api:
            url = (
                f"{AnimeUrl.M3U8_MOBILE}"
                f"?videoSn={self._sn}&device={self._device_id}"
            )
        else:
            url = f"{AnimeUrl.M3U8}?sn={self._sn}&device={self._device_id}"

        self._playlist = self._client.request_json(url)

    def _parse_playlist(self) -> None:
        """解析播放列表。"""
        # 獲取播放列表 URL
        if self._cfg.use_mobile_api:
            playlist_url = self._playlist["data"]["src"]
        else:
            playlist_url = self._playlist["src"]

        # 請求播放列表
        response = self._client.request(
            playlist_url,
            no_cookies=True,
            additional_headers={"origin": AnimeUrl.BASE},
        )

        # 解析 M3U8
        url_prefix = re.sub(r"playlist.+", "", playlist_url)
        m3u8_list = re.findall(r"=\d+x\d+\n.+", response.text)

        for item in m3u8_list:
            # 提取解析度
            resolution_match = re.findall(r"x\d+", item)
            if resolution_match:
                resolution = resolution_match[0][1:]  # 去掉 'x'
            else:
                continue

            # 提取 M3U8 URL
            m3u8_match = re.findall(r".*chunklist.+", item)
            if m3u8_match:
                m3u8_url = url_prefix + m3u8_match[0]
                self._m3u8_dict[resolution] = m3u8_url

    def _handle_error(self, user_info: dict, title: str) -> None:
        """處理錯誤訊息。

        Args:
            user_info: 用戶資訊
            title: 影片標題
        """
        error = user_info.get("error", {})
        msg = (
            f"《{title}》 "
            f"code={error.get('code', 'unknown')} "
            f"message: {error.get('message', 'unknown error')}"
        )
        err_print(self._sn, "收到錯誤", msg, status=1)
        sys.exit(1)

    def _handle_non_vip_ads(self, title: str) -> None:
        """處理非 VIP 用戶廣告。

        Args:
            title: 影片標題
        """
        if self._cfg.only_use_vip:
            err_print(
                self._sn,
                "非VIP",
                "因為已設定只使用VIP下載，故強制停止",
                status=1,
                no_sn=True,
            )
            sys.exit(1)

        ad_time = self._get_current_ad_time()

        err_print(
            self._sn,
            "正在等待",
            f"《{title}》 由於不是VIP賬戶, 正在等待{ad_time}s廣告時間",
        )

        self._start_ad()
        time.sleep(ad_time)
        self._skip_ad()

    def _get_current_ad_time(self) -> int:
        """獲取當前廣告時間。

        Returns:
            廣告時間（秒）
        """
        if self._cfg.use_mobile_api:
            return self._cfg.mobile_ads_time
        return self._cfg.ads_time

    def _save_ad_time(self, ads_time: int) -> None:
        """保存廣告時間到配置。

        Args:
            ads_time: 廣告時間（秒）
        """
        if self._cfg.use_mobile_api:
            self._cfg.mobile_ads_time = ads_time
        else:
            self._cfg.ads_time = ads_time
        config.save_config(self._cfg)

    @staticmethod
    def _generate_random_string(length: int) -> str:
        """生成隨機字串。

        Args:
            length: 字串長度

        Returns:
            隨機字串
        """
        chars = "abcdefghijklmnopqrstuvwxyz0123456789"
        random.seed(int(round(time.time() * 1000)))
        return "".join(random.choice(chars) for _ in range(length))
