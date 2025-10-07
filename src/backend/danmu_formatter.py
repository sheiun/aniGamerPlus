"""彈幕格式化工具模組。

提供彈幕格式轉換和 ASS 字幕生成功能。
"""

from __future__ import annotations

import random
from typing import Literal

DanmuPosition = Literal[0, 1, 2]  # 0=滾動, 1=頂部, 2=底部


class DanmuFormatter:
    """彈幕格式化工具。

    處理彈幕資料的格式轉換，生成 ASS 字幕格式。
    """

    @staticmethod
    def rgb_to_bgr(rgb_color: str) -> str:
        """將 RGB 顏色轉換為 BGR 格式。

        Args:
            rgb_color: RGB 顏色字串（如 "FF0000"）

        Returns:
            BGR 顏色字串（如 "0000FF"）
        """
        if len(rgb_color) < 6:
            return "FFFFFF"  # 預設白色

        r, g, b = rgb_color[0:2], rgb_color[2:4], rgb_color[4:6]
        return f"{b}{g}{r}"

    @staticmethod
    def format_time(seconds: int, hundred_ms: int) -> str:
        """格式化時間為 ASS 字幕格式。

        Args:
            seconds: 秒數
            hundred_ms: 百毫秒數（0-9）

        Returns:
            格式化的時間字串（如 "0:01:23.40"）
        """
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        return f"{h:d}:{m:02d}:{s:02d}.{hundred_ms:d}0"

    @staticmethod
    def create_roll_danmu(
        text: str,
        bgr_color: str,
        start_time_str: str,
        end_time_str: str,
        height: int,
    ) -> str:
        """創建滾動彈幕。

        Args:
            text: 彈幕文字
            bgr_color: BGR 顏色
            start_time_str: 開始時間
            end_time_str: 結束時間
            height: 垂直位置

        Returns:
            ASS 字幕行
        """
        return (
            f"Dialogue: 0,{start_time_str},{end_time_str},Roll,,0,0,0,,"
            f"{{\\move(1920,{height},-1000,{height})\\1c&H4C{bgr_color}}}{text}\n"
        )

    @staticmethod
    def create_top_danmu(
        text: str,
        bgr_color: str,
        start_time_str: str,
        end_time_str: str,
    ) -> str:
        """創建頂部彈幕。

        Args:
            text: 彈幕文字
            bgr_color: BGR 顏色
            start_time_str: 開始時間
            end_time_str: 結束時間

        Returns:
            ASS 字幕行
        """
        return (
            f"Dialogue: 0,{start_time_str},{end_time_str},Top,,0,0,0,,"
            f"{{\\1c&H4C{bgr_color}}}{text}\n"
        )

    @staticmethod
    def create_bottom_danmu(
        text: str,
        bgr_color: str,
        start_time_str: str,
        end_time_str: str,
    ) -> str:
        """創建底部彈幕。

        Args:
            text: 彈幕文字
            bgr_color: BGR 顏色
            start_time_str: 開始時間
            end_time_str: 結束時間

        Returns:
            ASS 字幕行
        """
        return (
            f"Dialogue: 0,{start_time_str},{end_time_str},Bottom,,0,0,0,,"
            f"{{\\1c&H4C{bgr_color}}}{text}\n"
        )


class RollChannelManager:
    """滾動彈幕軌道管理器。

    管理滾動彈幕的多個軌道，避免重疊。
    """

    def __init__(self) -> None:
        """初始化軌道管理器。"""
        self._channels: list[int] = []  # 每個軌道的結束時間
        self._roll_times: list[int] = []  # 每個軌道的滾動時間

    def allocate_channel(
        self, danmu_time: int, text_length: int
    ) -> tuple[int, int, int]:
        """分配軌道。

        Args:
            danmu_time: 彈幕時間（十分之一秒）
            text_length: 文字長度

        Returns:
            (軌道高度, 結束時間, 滾動時間)
        """
        # 查找可用軌道
        for i, channel_end_time in enumerate(self._channels):
            if channel_end_time <= danmu_time:
                height = i * 54 + 27
                roll_time = self._roll_times[i]
                self._channels[i] = danmu_time + (text_length * roll_time) // 8 + 1
                return height, roll_time, roll_time

        # 創建新軌道
        new_roll_time = random.randint(10, 14)
        self._channels.append(danmu_time + (text_length * new_roll_time) // 8 + 1)
        self._roll_times.append(new_roll_time)
        height = len(self._channels) * 54 - 27

        return height, new_roll_time, new_roll_time
