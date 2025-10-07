"""檔案名稱建構模組。

提供統一的檔案名稱生成邏輯，支援 PLEX 命名、集數補零等功能。
"""

from __future__ import annotations

import re

from . import config
from .constants import ChineseNumberMap, SeasonPattern


class FilenameBuilder:
    """檔案名稱建構器。

    處理影片檔案名稱的生成，包含番劇名、集數、解析度等元素。
    """

    def __init__(self, cfg: config.Config) -> None:
        """初始化檔案名稱建構器。

        Args:
            cfg: 配置物件
        """
        self._cfg = cfg
        self._season_filter = re.compile(SeasonPattern.SEASON_TITLE)
        self._extra_filter = re.compile(SeasonPattern.EXTRA_TITLE)

    def build(
        self,
        bangumi_name: str,
        episode: str,
        resolution: str,
        bangumi_name_orig: str = "",
        include_suffix: bool = True,
    ) -> str:
        """建構檔案名稱。

        Args:
            bangumi_name: 番劇名稱
            episode: 集數
            resolution: 解析度
            bangumi_name_orig: 原始番劇名稱（用於 PLEX 命名）
            include_suffix: 是否包含副檔名

        Returns:
            完整檔案名稱
        """
        # 處理集數格式
        formatted_episode = self._format_episode(episode, bangumi_name_orig)

        # 建構基礎檔名
        if self._cfg.add_bangumi_name_to_video_filename:
            filename = (
                self._cfg.customized_video_filename_prefix
                + bangumi_name
                + self._cfg.customized_bangumi_name_suffix
                + formatted_episode
            )
        else:
            filename = self._cfg.customized_video_filename_prefix + formatted_episode

        # 添加解析度
        if self._cfg.add_resolution_to_video_filename:
            filename += f"[{resolution}P]"

        # 添加後綴和副檔名
        if include_suffix:
            filename += (
                self._cfg.customized_video_filename_suffix
                + "."
                + self._cfg.video_filename_extension
            )

        # 合法化檔案名稱
        return config.legalize_filename(filename)

    def build_temp(
        self, bangumi_name: str, episode: str, resolution: str, temp_suffix: str
    ) -> str:
        """建構臨時檔案名稱。

        Args:
            bangumi_name: 番劇名稱
            episode: 集數
            resolution: 解析度
            temp_suffix: 臨時檔案後綴（如 DOWNLOADING, MERGING）

        Returns:
            臨時檔案名稱
        """
        # 先建構不含副檔名的檔名
        base_filename = self.build(
            bangumi_name, episode, resolution, include_suffix=False
        )

        # 添加臨時後綴
        temp_filename = (
            base_filename
            + self._cfg.customized_video_filename_suffix
            + f".{temp_suffix}."
            + self._cfg.video_filename_extension
        )

        return config.legalize_filename(temp_filename)

    def _format_episode(self, episode: str, bangumi_name_orig: str = "") -> str:
        """格式化集數。

        Args:
            episode: 原始集數
            bangumi_name_orig: 原始番劇名稱（用於 PLEX 命名）

        Returns:
            格式化後的集數字串
        """
        # 處理數字補零
        formatted_ep = self._zerofill_episode(episode)

        # PLEX 命名格式
        if self._cfg.plex_naming and bangumi_name_orig:
            return self._format_plex_episode(formatted_ep, bangumi_name_orig)

        # 標準格式
        return f"[{formatted_ep}]"

    def _zerofill_episode(self, episode: str) -> str:
        """集數補零處理。

        Args:
            episode: 原始集數

        Returns:
            補零後的集數
        """
        if self._cfg.zerofill <= 1:
            return episode

        # 檢查是否為純數字或小數
        if not re.match(r"^[+-]?\d+(\.\d+)?$", episode):
            return episode

        # 處理小數
        if "." in episode:
            integer_part, decimal_part = episode.split(".", 1)
            return integer_part.zfill(self._cfg.zerofill) + "." + decimal_part

        # 處理整數
        return episode.zfill(self._cfg.zerofill)

    def _format_plex_episode(self, episode: str, bangumi_name_orig: str) -> str:
        """PLEX 命名格式處理。

        Args:
            episode: 集數
            bangumi_name_orig: 原始番劇名稱

        Returns:
            PLEX 格式的集數字串
        """
        # 檢查季度
        season_match = self._season_filter.findall(bangumi_name_orig)
        if season_match:
            season_num_str = season_match[0].replace("第", "").replace("季", "")
            season_num = self._parse_chinese_number(season_num_str)
            return f"[S{str(season_num).zfill(self._cfg.zerofill)}E{episode}]"

        # 檢查特別篇
        extra_match = self._extra_filter.findall(bangumi_name_orig)
        if extra_match:
            return f"[E{episode}]"

        # 檢查電影
        if episode == "電影":
            return "[電影]"

        # 預設為 S01
        return f"[S01E{episode}]"

    @staticmethod
    def _parse_chinese_number(zh_num: str) -> int:
        """解析中文數字。

        Args:
            zh_num: 中文數字字串

        Returns:
            對應的阿拉伯數字
        """
        mapping = ChineseNumberMap.MAPPING
        result = 0
        temp = 0

        for char in zh_num:
            num = mapping.get(char, 0)
            if num >= 10:
                temp = 1 if temp == 0 else temp
                result += num * temp
                temp = 0
            else:
                temp = temp * 10 + num

        return result + temp
