"""配置和運行時設置結構定義模組。

使用 dataclass 定義配置結構，提供類型安全和驗證。
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class FTPConfig:
    """FTP 配置。"""

    server: str = ""
    port: int = 0
    user: str = ""
    pwd: str = ""
    tls: bool = True
    cwd: str = ""
    show_error_detail: bool = False
    max_retry_num: int = 15


@dataclass
class CoolQSettings:
    """CoolQ 推送設置。"""

    msg_argument_name: str = "message"
    message_suffix: str = "追加的資訊"
    query: list[str] = field(
        default_factory=lambda: [
            "http://127.0.0.1:5700/send_group_msg?access_token=abc&group_id=12345678",
            "http://127.0.0.1:5700/send_group_msg?access_token=abc&group_id=87654321",
        ]
    )


@dataclass
class DashboardConfig:
    """Web 控制面板配置。"""

    host: str = "127.0.0.1"
    port: int = 5000
    SSL: bool = False
    username: str = "admin"
    password: str = "admin"
    secret_key: str = ""  # JWT 密鑰（自動生成，用於持久化 token）


@dataclass
class Config:
    """主配置類別。"""

    # 目錄配置
    bangumi_dir: str = ""
    temp_dir: str = ""
    classify_bangumi: bool = True
    classify_season: bool = False

    # 下載配置
    check_frequency: int = 5
    download_cd: int = 60
    parse_sn_cd: int = 5
    download_resolution: str = "1080"
    lock_resolution: bool = False
    only_use_vip: bool = False
    disable_guest_mode: bool = False  # 不使用遊客帳號（當 cookie 更新失敗時暫停下載）
    default_download_mode: str = "latest"
    use_copyfile_method: bool = False

    # 多線程配置
    multi_thread: int = 1
    multi_upload: int = 3
    segment_download_mode: bool = True
    multi_downloading_segment: int = 2
    segment_max_retry: int = 8

    # 文件名配置
    add_bangumi_name_to_video_filename: bool = True
    add_resolution_to_video_filename: bool = True
    customized_video_filename_prefix: str = "【動畫瘋】"
    customized_bangumi_name_suffix: str = ""
    customized_video_filename_suffix: str = ""
    video_filename_extension: str = "mp4"
    zerofill: int = 1

    # 網絡配置
    ua: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"
    cookie: str = ""  # 動畫瘋 Cookie（格式：key1=value1; key2=value2）
    use_proxy: bool = False
    proxy: str = "http://user:passwd@example.com:1000"
    no_proxy_akamai: bool = False

    # 上傳配置
    upload_to_server: bool = False
    ftp: FTPConfig = field(default_factory=FTPConfig)

    # 用戶命令
    user_command: str = "shutdown -s -t 60"

    # 通知配置
    coolq_notify: bool = False
    coolq_settings: CoolQSettings = field(default_factory=CoolQSettings)
    telebot_notify: bool = False
    telebot_token: str = ""
    telebot_use_chat_id: bool = False
    telebot_chat_id: str = ""
    discord_notify: bool = False
    discord_token: str = ""

    # Plex 配置
    plex_refresh: bool = False
    plex_url: str = ""
    plex_token: str = ""
    plex_section: str = ""
    plex_naming: bool = False

    # 其他配置
    faststart_movflags: bool = False
    audio_language: bool = False
    use_mobile_api: bool = False

    # 彈幕配置
    danmu: bool = False
    danmu_ban_words: list[str] = field(default_factory=list)

    # 系統配置
    check_latest_version: bool = True
    read_sn_list_when_checking_update: bool = True
    read_config_when_checking_update: bool = True
    ads_time: int = 25
    mobile_ads_time: int = 25
    max_completed_tasks: int = 100  # 最多保留的已完成任務數量（0 表示不限制）

    # Web 控制面板
    use_dashboard: bool = True
    dashboard: DashboardConfig = field(default_factory=DashboardConfig)

    # 日誌配置
    save_logs: bool = True
    quantity_of_logs: int = 7

    # SN 列表配置 (文本格式，保留原有的注釋和標籤)
    sn_list: str = ""


@dataclass
class Settings(Config):
    """運行時設置類別（繼承自 Config，添加運行時計算字段）。

    此類繼承 Config 的所有字段，並添加以下運行時字段：
    - working_dir: 工作目錄（運行時確定）
    - use_gost: 是否使用 Gost 代理（根據 proxy 格式計算）
    - aniGamerPlus_version: 版本號（運行時注入）

    注意：以下字段在運行時會被覆蓋為處理後的值：
    - bangumi_dir, temp_dir: 轉換為絕對路徑
    """

    # 運行時專屬字段（不在 Config 中）
    working_dir: str = ""
    use_gost: bool = False  # 運行時計算：是否使用 Gost 代理
    aniGamerPlus_version: str = ""  # 運行時注入的版本號
