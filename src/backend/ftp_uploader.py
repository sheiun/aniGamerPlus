"""FTP 上傳器模組。

提供檔案上傳至 FTP 伺服器的功能，支援斷點續傳。
"""

from __future__ import annotations

import ftplib
import os
import re
import socket
import time
from ftplib import FTP, FTP_TLS
from pathlib import Path

from . import config
from .color_print import err_print
from .constants import RetryConfig, Timeout


class FtpUploader:
    """FTP 上傳器。

    處理檔案上傳至 FTP 伺服器，支援斷點續傳和自動重試。
    """

    def __init__(self, sn: int | str, cfg: config.Config) -> None:
        """初始化 FTP 上傳器。

        Args:
            sn: 影片序號
            cfg: 配置物件
        """
        self._sn = str(sn)
        self._cfg = cfg
        self._ftp: FTP | FTP_TLS | None = None
        self._first_connect = True

    def upload(
        self,
        local_path: str,
        bangumi_name: str,
        bangumi_tag: str = "",
    ) -> bool:
        """上傳檔案至 FTP。

        Args:
            local_path: 本地檔案路徑
            bangumi_name: 番劇名稱
            bangumi_tag: 番劇分類標籤

        Returns:
            是否上傳成功
        """
        local_file = Path(local_path)
        if not local_file.exists():
            return False

        filename = local_file.name
        temp_dir = f"{self._sn}-uploading-by-aniGamerPlus"

        # 初始化 FTP
        self._init_ftp()

        # 連線並設定目錄
        if not self._connect_and_setup(bangumi_name, bangumi_tag, temp_dir):
            return False

        # 執行上傳
        try:
            success = self._upload_with_retry(local_file, filename, temp_dir)
            if success:
                err_print(self._sn, "上傳完成", filename, status=2)
            return success
        finally:
            self._close_ftp()

    def _init_ftp(self) -> None:
        """初始化 FTP 連線物件。"""
        socket.setdefaulttimeout(Timeout.FTP_SOCKET)
        if self._cfg.ftp.tls:
            self._ftp = FTP_TLS()
        else:
            self._ftp = FTP()

    def _connect_and_setup(
        self, bangumi_name: str, bangumi_tag: str, temp_dir: str
    ) -> bool:
        """連線並設定 FTP 目錄。

        Args:
            bangumi_name: 番劇名稱
            bangumi_tag: 番劇分類
            temp_dir: 臨時目錄名稱

        Returns:
            是否成功
        """
        if not self._connect(show_err=True):
            return False

        # 進入指定目錄
        if self._cfg.ftp.cwd:
            self._change_dir(self._cfg.ftp.cwd)

        # 處理番劇分類
        if bangumi_tag:
            self._ensure_dir_exists(bangumi_tag)

        # 處理番劇目錄
        bangumi_dir = config.legalize_filename(bangumi_name)
        self._ensure_dir_exists(bangumi_dir)

        # 首次連線時刪除舊的臨時目錄
        if self._first_connect:
            self._remove_dir(temp_dir)
            self._first_connect = False

        # 創建並進入臨時目錄
        self._ensure_dir_exists(temp_dir)

        return True

    def _connect(self, show_err: bool = True) -> bool:
        """連線至 FTP 伺服器。

        Args:
            show_err: 是否顯示錯誤訊息

        Returns:
            是否連線成功
        """
        if not self._ftp:
            return False

        self._ftp.encoding = "utf-8"
        error_count = 0

        while error_count <= 3:
            try:
                self._ftp.connect(self._cfg.ftp.server, self._cfg.ftp.port)
                self._ftp.login(self._cfg.ftp.user, self._cfg.ftp.pwd)
                self._ftp.voidcmd("TYPE I")  # 二進位模式
                return True
            except ftplib.error_temp as e:
                if show_err:
                    if "Too many connections" in str(e):
                        err_print(
                            self._sn,
                            "FTP狀態",
                            f"當前FTP連接數過多, 5分鐘后重試: {e}",
                            status=1,
                        )
                    else:
                        err_print(
                            self._sn,
                            "FTP狀態",
                            f"連接FTP時發生錯誤, 5分鐘后重試: {e}",
                            status=1,
                        )
                error_count += 1
                time.sleep(5 * 60)
            except Exception as e:
                if show_err:
                    err_print(
                        self._sn,
                        "FTP狀態",
                        f"在連接FTP時發生無法處理的異常: {e}",
                        status=1,
                    )
                break

        return False

    def _change_dir(self, directory: str) -> None:
        """切換目錄。

        Args:
            directory: 目錄路徑
        """
        if not self._ftp:
            return

        try:
            self._ftp.cwd(directory)
        except ftplib.error_perm as e:
            err_print(
                self._sn,
                "FTP狀態",
                f"進入指定FTP目錄時出錯: {e}",
                status=1,
            )

    def _ensure_dir_exists(self, directory: str) -> None:
        """確保目錄存在，不存在則創建。

        Args:
            directory: 目錄名稱
        """
        if not self._ftp:
            return

        try:
            self._ftp.cwd(directory)
        except ftplib.error_perm:
            try:
                self._ftp.mkd(directory)
                self._ftp.cwd(directory)
            except ftplib.error_perm as e:
                err_print(
                    self._sn,
                    "FTP狀態",
                    f"創建目錄時發生異常: {e}",
                    status=1,
                )

    def _remove_dir(self, directory: str) -> None:
        """刪除目錄及其內容。

        Args:
            directory: 目錄名稱
        """
        if not self._ftp:
            return

        try:
            self._ftp.rmd(directory)
        except ftplib.error_perm as e:
            if "Directory not empty" in str(e):
                self._ftp.cwd(directory)
                self._delete_all_files()
                self._ftp.cwd("..")
                self._ftp.rmd(directory)
            elif "No such file or directory" not in str(e):
                raise

    def _delete_all_files(self) -> None:
        """刪除當前目錄下所有檔案。"""
        if not self._ftp:
            return

        try:
            for filename in self._ftp.nlst():
                if not re.match(r"^(\.|\.\.)$", filename):
                    self._ftp.delete(filename)
        except ftplib.error_perm as e:
            if str(e) != "550 No files found":
                raise

    def _upload_with_retry(
        self, local_file: Path, filename: str, temp_dir: str
    ) -> bool:
        """執行上傳並重試。

        Args:
            local_file: 本地檔案
            filename: 檔案名稱
            temp_dir: 臨時目錄

        Returns:
            是否上傳成功
        """
        err_print(self._sn, "正在上傳", filename)

        local_size = local_file.stat().st_size
        retry_count = 0
        upload_filename = filename

        while retry_count <= self._cfg.ftp.max_retry_num:
            try:
                if retry_count > 0:
                    err_print(
                        self._sn,
                        "上傳狀態",
                        f"{filename} 發生異常, 重連FTP, 續傳文件",
                        status=1,
                    )
                    if not self._connect(show_err=False):
                        return False

                    # 處理 Pure-FTPd 續傳改名問題
                    for file in self._ftp.nlst():  # type: ignore
                        if "pureftpd-upload" in file:
                            upload_filename = file
                            break

                # 獲取遠端檔案大小
                try:
                    remote_size = self._ftp.size(upload_filename)  # type: ignore
                    if remote_size is None:
                        remote_size = 0
                except (ftplib.error_perm, OSError):
                    remote_size = 0
                    self._delete_all_files()

                # 執行上傳
                self._ftp.voidcmd("TYPE I")  # type: ignore
                conn = self._ftp.transfercmd(f"STOR {upload_filename}", remote_size)  # type: ignore

                with open(local_file, "rb") as f:
                    f.seek(remote_size)
                    while True:
                        block = f.read(1048576)  # 1MB
                        if not block:
                            time.sleep(3)
                            break
                        conn.sendall(block)

                conn.close()

                # 驗證上傳
                err_print(self._sn, "上傳狀態", "檢查遠端文件大小是否與本地一致……")
                self._close_ftp()
                self._connect(show_err=False)

                # 獲取最終遠端大小
                remote_size = self._get_remote_size(upload_filename)

                if remote_size != local_size:
                    err_print(
                        self._sn,
                        "上傳狀態",
                        f"{filename} 遠端{round(remote_size/(1024*1024), 2)}MB "
                        f"與本地{round(local_size/(1024*1024), 2)}MB 不一致",
                        status=1,
                    )
                    retry_count += 1
                    continue

                # 上傳成功，移出臨時目錄
                if not self._ftp:
                    return False

                self._ftp.cwd("..")
                try:
                    if self._ftp.size(filename):
                        self._ftp.delete(filename)
                except ftplib.error_perm:
                    pass

                self._ftp.rename(f"{temp_dir}/{upload_filename}", filename)
                self._remove_dir(temp_dir)

                return True

            except (ConnectionResetError, TimeoutError, socket.timeout) as e:
                if self._cfg.ftp.show_error_detail:
                    err_print(
                        self._sn,
                        "上傳狀態",
                        f"{filename} 上傳過程中網絡錯誤: {e}",
                        status=1,
                    )
                retry_count += 1

        err_print(self._sn, "上傳失敗", f"{filename} 放棄上傳!", status=1)
        return False

    def _get_remote_size(self, filename: str) -> int:
        """獲取遠端檔案大小。

        Args:
            filename: 檔案名稱

        Returns:
            檔案大小（位元組）
        """
        if not self._ftp:
            return 0

        for attempt in range(3):
            try:
                size = self._ftp.size(filename)
                return size if size is not None else 0
            except ftplib.error_perm:
                return 0
            except OSError:
                self._connect(show_err=False)

        return 0

    def _close_ftp(self) -> None:
        """關閉 FTP 連線。"""
        if not self._ftp:
            return

        try:
            self._ftp.quit()
        except Exception as e:
            if self._cfg.ftp.show_error_detail:
                err_print(
                    self._sn,
                    "FTP狀態",
                    f"將强制關閉FTP連接: {e}",
                )
            self._ftp.close()
