"""彈幕下載模組。

此模組負責下載動畫瘋的彈幕並轉換為 ASS 字幕格式。

Classes:
    Danmu: 彈幕下載和處理類別
"""

from __future__ import annotations

import random
import re
from pathlib import Path

import httpx

from . import config
from .color_print import err_print
from .danmu_formatter import DanmuFormatter, RollChannelManager


class Danmu:
    """彈幕下載和處理類別。

    負責下載動畫瘋的彈幕資料並轉換為 ASS 字幕格式，
    支援過濾敏感詞和自訂關鍵字。
    """

    _BASE_URL = "https://ani.gamer.com.tw"
    _USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36"
    )

    def __init__(
        self, sn: int | str, full_filename: str, cookies: dict[str, str]
    ) -> None:
        """初始化彈幕下載器。

        Args:
            sn: 影片序號（SN碼）
            full_filename: 輸出 .ass 檔案的完整路徑
            cookies: 認證 Cookie
        """
        self._sn = str(sn)
        self._full_filename = Path(full_filename)
        self._cookies = cookies

    @staticmethod
    def _rgb_to_bgr(rgb_color: str) -> str:
        """Convert RGB color format to BGR format (使用 DanmuFormatter)."""
        return DanmuFormatter.rgb_to_bgr(rgb_color)

    @staticmethod
    def _find_ban_word(text: str, ban_word_pattern: re.Pattern) -> str | None:
        """Check if text contains banned words.

        Args:
            text: Text to check
            ban_word_pattern: Compiled regex pattern for banned words

        Returns:
            Matched banned word or None
        """
        result = ban_word_pattern.search(text)
        return result.group(0) if result and result.group(0) else None

    def _fetch_danmu_data(self) -> dict | None:
        """Fetch danmu data from server.

        Returns:
            Danmu data as dict or None if failed
        """
        headers = {
            "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",
            "origin": self._BASE_URL,
            "authority": "ani.gamer.com.tw",
            "user-agent": self._USER_AGENT,
        }
        data = {"sn": self._sn}

        try:
            response = httpx.post(
                f"{self._BASE_URL}/ajax/danmuGet.php",
                data=data,
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            err_print(
                self._sn,
                "彈幕下載失敗",
                f"Error: {e}",
                status=1,
            )
            return None

    def _fetch_online_ban_words(self) -> list[str]:
        """Fetch online banned words list.

        Returns:
            List of banned words
        """
        headers = {
            "accept": "application/json",
            "origin": self._BASE_URL,
            "authority": "ani.gamer.com.tw",
            "user-agent": self._USER_AGENT,
        }

        try:
            response = httpx.get(
                f"{self._BASE_URL}/ajax/keywordGet.php",
                headers=headers,
                cookies=self._cookies,
                timeout=30,
            )
            response.raise_for_status()

            online_ban_words = response.json()
            ban_words = [word["keyword"] for word in online_ban_words]

            for ban_word in ban_words:
                err_print(
                    self._sn,
                    "取得線上過濾彈幕",
                    detail=ban_word,
                    status=0,
                    display=False,
                )

            return ban_words
        except httpx.HTTPError as e:
            err_print(
                self._sn,
                "取得線上過濾彈幕失敗",
                f"Error: {e}",
                status=1,
            )
            return []

    def _format_time(self, time_value: int, hundred_ms: int) -> str:
        """Format time value to ASS subtitle format (使用 DanmuFormatter)."""
        return DanmuFormatter.format_time(time_value, hundred_ms)

    def _process_roll_danmu(
        self,
        danmu: dict,
        text: str,
        bgr_color: str,
        start_time: int,
        hundred_ms: int,
        roll_channel: list[int],
        roll_time: list[int],
    ) -> str:
        """Process rolling danmu.

        Args:
            danmu: Danmu data
            text: Danmu text
            bgr_color: BGR color code
            start_time: Start time in seconds
            hundred_ms: Hundreds of milliseconds
            roll_channel: List of roll channel states
            roll_time: List of roll durations

        Returns:
            Formatted ASS subtitle line
        """
        height = 0
        end_time = 0

        # Find available channel
        for i, channel_time in enumerate(roll_channel):
            if channel_time <= danmu["time"]:
                height = i * 54 + 27
                roll_channel[i] = danmu["time"] + (len(text) * roll_time[i]) / 8 + 1
                end_time = start_time + roll_time[i]
                break

        # Create new channel if none available
        if height == 0:
            new_roll_time = random.randint(10, 14)
            roll_channel.append(danmu["time"] + (len(text) * new_roll_time) / 8 + 1)
            roll_time.append(new_roll_time)
            height = len(roll_channel) * 54 - 27
            end_time = start_time + roll_time[-1]

        m, s = divmod(end_time, 60)
        h, m = divmod(m, 60)
        end_time_str = f"{h:d}:{m:02d}:{s:02d}.{hundred_ms:d}0"

        return (
            f"Dialogue: 0,{self._format_time(start_time, hundred_ms)},{end_time_str},"
            f"Roll,,0,0,0,,{{\\move(1920,{height},-1000,{height})"
            f"\\1c&H4C{bgr_color}}}{text}\n"
        )

    def download(self, ban_words: list[str]) -> None:
        """Download and convert danmu to ASS subtitle format.

        Args:
            ban_words: List of words to filter out
        """
        # Fetch danmu data
        danmu_data = self._fetch_danmu_data()
        if not danmu_data:
            return

        # Fetch online ban words
        online_ban_words = self._fetch_online_ban_words()
        all_ban_words = ban_words + online_ban_words

        # Prepare output file
        template_path = Path(config.get_working_dir()) / "DanmuTemplate.ass"
        template_content = template_path.read_text(encoding="utf-8")

        # Initialize state
        roll_channel: list[int] = []
        roll_time: list[int] = []
        ban_word_pattern = re.compile("|".join(all_ban_words), re.IGNORECASE)

        # Process each danmu
        output_lines = [template_content]

        for danmu in danmu_data:
            text = danmu["text"]

            # Skip if contains banned word
            if self._find_ban_word(text, ban_word_pattern):
                err_print(
                    self._sn,
                    f"跳過彈幕 [{text}]",
                    str(self._full_filename),
                    display=False,
                )
                continue

            # Calculate time
            start_time = int(danmu["time"] / 10)
            hundred_ms = danmu["time"] % 10
            start_time_str = self._format_time(start_time, hundred_ms)

            # Get color
            bgr_color = self._rgb_to_bgr(danmu["color"][1:])

            position = danmu["position"]
            if position == 0:  # Rolling danmu
                line = self._process_roll_danmu(
                    danmu,
                    text,
                    bgr_color,
                    start_time,
                    hundred_ms,
                    roll_channel,
                    roll_time,
                )
            elif position == 1:  # Top danmu
                end_time = start_time + 5
                end_time_str = self._format_time(end_time, hundred_ms)
                line = f"Dialogue: 0,{start_time_str},{end_time_str},Top,,0,0,0,,{{\\1c&H4C{bgr_color}}}{text}\n"
            else:  # Bottom danmu
                end_time = start_time + 5
                end_time_str = self._format_time(end_time, hundred_ms)
                line = f"Dialogue: 0,{start_time_str},{end_time_str},Bottom,,0,0,0,,{{\\1c&H4C{bgr_color}}}{text}\n"

            output_lines.append(line)

        # Write output file
        self._full_filename.write_text("".join(output_lines), encoding="utf-8")
        err_print(self._sn, "彈幕下載完成", str(self._full_filename), status=2)


if __name__ == "__main__":
    pass
