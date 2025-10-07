"""下載器模組。

提供影片下載功能，支援分段下載和 FFmpeg 下載兩種模式。
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import threading
import time
from abc import ABC, abstractmethod
from pathlib import Path

from . import config
from .color_print import err_print
from .constants import DownloadStatus, RetryConfig, Timeout
from .http_client import HttpClient, TryTooManyTimeError
from .utils import ProgressTracker


class BaseDownloader(ABC):
    """下載器基礎類別。

    定義下載器的共用介面和功能。
    """

    def __init__(
        self,
        sn: int | str,
        http_client: HttpClient,
        cfg: config.Config,
        m3u8_url: str,
        output_path: str,
        temp_path: str,
        filename: str,
    ) -> None:
        """初始化下載器。

        Args:
            sn: 影片序號
            http_client: HTTP 客戶端
            cfg: 配置物件
            m3u8_url: M3U8 播放列表 URL
            output_path: 輸出檔案路徑
            temp_path: 臨時檔案路徑
            filename: 檔案名稱
        """
        self._sn = str(sn)
        self._client = http_client
        self._cfg = cfg
        self._m3u8_url = m3u8_url
        self._output_path = Path(output_path)
        self._temp_path = Path(temp_path)
        self._filename = filename
        self._ffmpeg_path = ""
        self._title = ""
        self.video_size = 0
        self.realtime_show = False

    def set_title(self, title: str) -> None:
        """設定影片標題。"""
        self._title = title

    def set_ffmpeg_path(self, path: str) -> None:
        """設定 FFmpeg 路徑。"""
        self._ffmpeg_path = path

    @abstractmethod
    def download(self) -> bool:
        """執行下載。

        Returns:
            是否下載成功
        """
        pass

    def _move_to_output(self, source: Path) -> None:
        """移動檔案到輸出目錄。

        Args:
            source: 來源檔案路徑
        """
        # 記錄檔案大小
        self.video_size = int(source.stat().st_size / (1024 * 1024))

        err_print(
            self._sn,
            "下載狀態",
            f"{self._filename} 解密合并完成, 本集 {self.video_size}MB, 正在移至番劇目錄……",
        )

        # 刪除已存在的檔案
        if self._output_path.exists():
            self._output_path.unlink()

        # 移動檔案
        if self._cfg.use_copyfile_method:
            shutil.copyfile(source, self._output_path)
            source.unlink()
        else:
            shutil.move(str(source), str(self._output_path))

        err_print(self._sn, "下載完成", self._filename, status=2)

    def _build_ffmpeg_cmd(self, input_file: str, output_file: str) -> list[str]:
        """建構 FFmpeg 命令。

        Args:
            input_file: 輸入檔案
            output_file: 輸出檔案

        Returns:
            FFmpeg 命令列表
        """
        cmd = [
            self._ffmpeg_path,
            "-allowed_extensions",
            "ALL",
            "-i",
            input_file,
            "-c",
            "copy",
            output_file,
            "-y",
        ]

        # Faststart movflags
        if self._cfg.faststart_movflags:
            cmd[7:7] = ["-movflags", "faststart"]

        # Audio language metadata
        if self._cfg.audio_language:
            language = "chi" if "中文" in self._title else "jpn"
            cmd[7:7] = ["-metadata:s:a:0", f"language={language}"]

        return cmd


class SegmentDownloader(BaseDownloader):
    """分段下載器。

    使用多線程下載影片片段並合併。
    """

    def download(self) -> bool:
        """執行分段下載。

        Returns:
            是否下載成功
        """
        # 創建臨時目錄
        temp_dir = self._temp_path.parent / f"{self._sn}-downloading-by-aniGamerPlus"
        temp_dir.mkdir(parents=True, exist_ok=True)

        try:
            # 下載並解析 M3U8
            m3u8_content = self._download_m3u8(temp_dir)
            key_path = self._download_key(m3u8_content, temp_dir)
            chunk_list = re.findall(r"media_b.+ts.*", m3u8_content)

            # 下載所有片段
            if not self._download_chunks(chunk_list, temp_dir):
                return False

            # 本地化 M3U8
            localized_m3u8 = self._localize_m3u8(
                m3u8_content, key_path, chunk_list, temp_dir
            )
            m3u8_path = temp_dir / f"{self._sn}.m3u8"
            m3u8_path.write_text(localized_m3u8, encoding="utf-8")

            # 使用 FFmpeg 合併
            self._merge_segments(m3u8_path)

            # 移動到輸出目錄
            self._move_to_output(self._temp_path)

            return True

        finally:
            # 清理臨時目錄
            shutil.rmtree(temp_dir, ignore_errors=True)

    def _download_m3u8(self, temp_dir: Path) -> str:
        """下載 M3U8 檔案。

        Args:
            temp_dir: 臨時目錄

        Returns:
            M3U8 內容
        """
        response = self._client.request(self._m3u8_url, no_cookies=True)
        return response.text

    def _download_key(self, m3u8_content: str, temp_dir: Path) -> Path:
        """下載加密金鑰。

        Args:
            m3u8_content: M3U8 內容
            temp_dir: 臨時目錄

        Returns:
            金鑰檔案路徑
        """
        key_match = re.search(r'(?<=AES-128,URI=")(.*)(?=")', m3u8_content)
        if not key_match:
            raise ValueError(f"無法從 M3U8 文件中提取 key URI: {m3u8_content[:200]}")

        key_uri = key_match.group()
        url_path = os.path.dirname(self._m3u8_url)

        # 處理相對路徑
        if not re.match(r"http.+", key_uri):
            key_uri = f"{url_path}/{key_uri}"

        # 下載金鑰
        key_path = temp_dir / "key.m3u8key"
        response = self._client.request(key_uri, no_cookies=True)
        key_path.write_bytes(response.content)

        return key_path

    def _download_chunks(self, chunk_list: list[str], temp_dir: Path) -> bool:
        """下載所有片段。

        Args:
            chunk_list: 片段列表
            temp_dir: 臨時目錄

        Returns:
            是否下載成功
        """
        url_path = os.path.dirname(self._m3u8_url)
        limiter = threading.Semaphore(self._cfg.multi_downloading_segment)
        total_chunks = len(chunk_list)
        finished_counter = 0
        failed_flag = False

        # 進度追蹤
        progress = ProgressTracker(self._sn, total_chunks)

        def download_chunk(chunk_name: str) -> None:
            nonlocal finished_counter, failed_flag

            chunk_path = temp_dir / chunk_name
            chunk_url = f"{url_path}/{chunk_name}"

            try:
                response = self._client.request(
                    chunk_url,
                    no_cookies=True,
                    show_fail=False,
                    max_retry=self._cfg.segment_max_retry,
                )
                chunk_path.write_bytes(response.content)
            except TryTooManyTimeError:
                failed_flag = True
                err_print(self._sn, "下載狀態", f"Bad segment={chunk_name}", status=1)
                limiter.release()
                return
            except Exception as e:
                failed_flag = True
                err_print(
                    self._sn,
                    "下載狀態",
                    f"Bad segment={chunk_name} 發生未知錯誤: {e}",
                    status=1,
                )
                limiter.release()
                return

            # 更新進度
            finished_counter += 1
            progress.update(finished_counter, DownloadStatus.DOWNLOADING)

            if self.realtime_show:
                progress_rate = round(finished_counter / total_chunks * 100, 2)
                sys.stdout.write(
                    f"\r正在下載: sn={self._sn} {self._filename} {progress_rate}%  "
                )
                sys.stdout.flush()

            limiter.release()

        # 顯示開始訊息
        if self.realtime_show:
            sys.stdout.write(f"正在下載: sn={self._sn} {self._filename}")
            sys.stdout.flush()
        else:
            err_print(self._sn, "正在下載", f"{self._filename} title={self._title}")

        # 建立下載任務
        tasks = []
        for chunk in chunk_list:
            chunk_name = re.findall(r"media_b.+ts", chunk)[0]
            task = threading.Thread(target=download_chunk, args=(chunk_name,))
            task.daemon = True
            tasks.append(task)
            limiter.acquire()
            task.start()

        # 等待所有任務完成
        for task in tasks:
            while task.is_alive():
                if failed_flag:
                    err_print(self._sn, "下載失败", self._filename, status=1)
                    self.video_size = 0
                    return False
                time.sleep(1)

        if self.realtime_show:
            sys.stdout.write("\n")
            sys.stdout.flush()

        return True

    def _localize_m3u8(
        self, m3u8_content: str, key_path: Path, chunk_list: list[str], temp_dir: Path
    ) -> str:
        """本地化 M3U8 檔案。

        Args:
            m3u8_content: M3U8 內容
            key_path: 金鑰路徑
            chunk_list: 片段列表
            temp_dir: 臨時目錄

        Returns:
            本地化後的 M3U8 內容
        """
        # 替換金鑰路徑
        key_match = re.search(r'(?<=AES-128,URI=")(.*)(?=")', m3u8_content)
        original_key_uri = key_match.group() if key_match else ""

        localized = m3u8_content.replace(
            original_key_uri, str(key_path).replace("\\", "\\\\")
        )

        # 替換片段路徑
        for chunk in chunk_list:
            chunk_name = re.findall(r"media_b.+ts", chunk)[0]
            chunk_path = str(temp_dir / chunk_name).replace("\\", "\\\\")
            localized = localized.replace(chunk, chunk_path)

        return localized

    def _merge_segments(self, m3u8_path: Path) -> None:
        """合併片段。

        Args:
            m3u8_path: M3U8 檔案路徑
        """
        err_print(self._sn, "下載狀態", f"{self._filename} 下載完成, 正在解密合并……")
        config.tasks_progress_rate[int(self._sn)]["status"] = DownloadStatus.MERGING

        cmd = self._build_ffmpeg_cmd(str(m3u8_path), str(self._temp_path))
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process.communicate()


class FfmpegDownloader(BaseDownloader):
    """FFmpeg 下載器。

    使用 FFmpeg 直接下載影片。
    """

    def download(self) -> bool:
        """執行 FFmpeg 下載。

        Returns:
            是否下載成功
        """
        # 清理舊檔案
        if self._temp_path.exists():
            self._temp_path.unlink()

        # 建構命令
        cmd = [
            self._ffmpeg_path,
            "-user_agent",
            self._cfg.ua,
            "-headers",
            "Origin: https://ani.gamer.com.tw",
            "-i",
            self._m3u8_url,
            "-c",
            "copy",
            str(self._temp_path),
            "-y",
        ]

        # 執行下載
        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, bufsize=204800, stderr=subprocess.PIPE
        )

        # 監控下載
        if not self._monitor_ffmpeg(process):
            return False

        # 檢查結果
        stdout, stderr = process.communicate()
        return_str = stderr.decode()

        if self.realtime_show:
            sys.stdout.write("\n")
            sys.stdout.flush()

        if process.returncode == 0 and "Failed to open segment" not in return_str:
            self._move_to_output(self._temp_path)
            return True
        else:
            err_print(
                self._sn,
                "下載失败",
                f"{self._filename} ffmpeg_return_code={process.returncode}",
                status=1,
            )
            return False

    def _monitor_ffmpeg(self, process: subprocess.Popen) -> bool:
        """監控 FFmpeg 執行。

        Args:
            process: FFmpeg 進程

        Returns:
            是否正常執行
        """
        # 顯示開始訊息
        if self.realtime_show:
            sys.stdout.write(f"正在下載: sn={self._sn} {self._filename}")
            sys.stdout.flush()
        else:
            err_print(self._sn, "正在下載", f"{self._filename} title={self._title}")

        time.sleep(2)
        time_counter = 1
        prev_size = 0

        while process.poll() is None:
            # 實時顯示檔案大小
            if self.realtime_show and self._temp_path.exists():
                size_mb = round(self._temp_path.stat().st_size / (1024 * 1024), 2)
                sys.stdout.write(
                    f"\r正在下載: sn={self._sn} {self._filename}    {size_mb}MB      "
                )
                sys.stdout.flush()

            # 檢查是否卡死
            if time_counter % Timeout.FFMPEG_CHECK_INTERVAL == 0 and self._temp_path.exists():
                current_size = self._temp_path.stat().st_size
                growth = current_size - prev_size

                if growth < 3 * 1024 * 1024:  # 少於 3MB
                    err_print(
                        self._sn,
                        "下載失败",
                        f"{self._filename} 在一分鐘內僅增加{int(growth/1024)}KB 判定為卡死",
                        status=1,
                    )
                    process.kill()
                    return False

                prev_size = current_size

            time.sleep(1)
            time_counter += 1

        return True
