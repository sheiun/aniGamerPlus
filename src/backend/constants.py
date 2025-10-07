"""常數定義模組。

集中管理專案中使用的常數、URL、設定值等。
"""

from __future__ import annotations

from enum import Enum


class VideoResolution(Enum):
    """影片解析度常數。"""

    P360 = "360"
    P480 = "480"
    P540 = "540"
    P576 = "576"
    P720 = "720"
    P1080 = "1080"

    @classmethod
    def is_valid(cls, value: str) -> bool:
        """檢查解析度是否有效。"""
        return value in {r.value for r in cls}

    @classmethod
    def get_closest(cls, target: int) -> str:
        """獲取最接近的解析度。"""
        resolutions = [int(r.value) for r in cls]
        closest = min(resolutions, key=lambda x: abs(x - target))
        return str(closest)


class DownloadMode(Enum):
    """下載模式常數。"""

    ALL = "all"  # 下載所有集數
    LATEST = "latest"  # 下載最後一集
    LARGEST_SN = "largest-sn"  # 下載最新上傳（SN 最大）
    SINGLE = "single"  # 下載單集


class EpisodeType(Enum):
    """劇集類型常數。"""

    MAIN = "0"  # 本篇
    MOVIE = "1"  # 電影
    SPECIAL = "2"  # 特別篇
    CHINESE_DUB = "3"  # 中文配音
    CHINESE_MOVIE = "4"  # 中文電影


class AnimeUrl:
    """動畫瘋 URL 常數。"""

    BASE = "https://ani.gamer.com.tw"
    VIDEO = BASE + "/animeVideo.php"
    MOBILE_API = "https://api.gamer.com.tw/mobile_app/anime"

    # API endpoints
    DEVICE_ID = BASE + "/ajax/getdeviceid.php"
    M3U8 = BASE + "/ajax/m3u8.php"
    M3U8_MOBILE = MOBILE_API + "/v3/m3u8.php"
    TOKEN = BASE + "/ajax/token.php"
    UNLOCK = BASE + "/ajax/unlock.php"
    CHECK_LOCK = BASE + "/ajax/checklock.php"
    VIDEO_START = BASE + "/ajax/videoStart.php"
    VIDEO_AD = BASE + "/ajax/videoCastcishu.php"
    DANMU_GET = BASE + "/ajax/danmuGet.php"
    KEYWORD_GET = BASE + "/ajax/keywordGet.php"


class HttpHeader:
    """HTTP Header 模板。"""

    # Web 版 Header
    WEB_COMMON = {
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.6",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate",
        "Cache-Control": "max-age=0",
    }

    # Mobile API Header
    MOBILE_API = {
        "User-Agent": "Animad/1.16.16 (tw.com.gamer.android.animad; build:328; Android 9) okHttp/4.4.0",
        "X-Bahamut-App-Android": "tw.com.gamer.android.animad",
        "X-Bahamut-App-Version": "328",
        "Accept-Encoding": "gzip",
        "Connection": "Keep-Alive",
    }

    # 彈幕 Header
    DANMU = {
        "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",
        "authority": "ani.gamer.com.tw",
    }


class FileExtension:
    """檔案副檔名常數。"""

    MP4 = "mp4"
    MKV = "mkv"
    ASS = "ass"
    M3U8 = "m3u8"
    M3U8KEY = "m3u8key"


class DownloadStatus:
    """下載狀態常數。"""

    PARSING = "正在解析"
    DOWNLOADING = "正在下載"
    MERGING = "解密合并中"
    MOVING = "正在移至番劇目錄"
    COMPLETED = "下載完成"
    FAILED = "任務失敗"
    WAITING = "等待下載"
    RETRYING = "失敗! 重啓中"


class Timeout:
    """超時設定常數（秒）。"""

    HTTP_REQUEST = 10.0
    DANMU_REQUEST = 30.0
    FTP_SOCKET = 20.0
    FFMPEG_CHECK_INTERVAL = 60  # ffmpeg 活動檢查間隔


class RetryConfig:
    """重試配置常數。"""

    MAX_REQUEST_RETRY = 3
    MAX_SEGMENT_RETRY = 8
    MAX_FTP_RETRY = 15
    MAX_DOWNLOAD_RETRY = 3


class AdConfig:
    """廣告相關配置。"""

    DEFAULT_WEB_AD_TIME = 25  # 網頁版預設廣告時間（秒）
    DEFAULT_MOBILE_AD_TIME = 25  # 手機版預設廣告時間（秒）
    MIN_AD_TIME = 8  # 最小廣告時間
    AD_CHECK_MAX_RETRY = 10  # 廣告檢查最大重試次數


class DefaultConfig:
    """預設配置值。"""

    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"
    VIDEO_FILENAME_PREFIX = "【動畫瘋】"
    DEFAULT_RESOLUTION = "1080"
    DEFAULT_ZEROFILL = 1
    DEFAULT_CHECK_FREQUENCY = 5  # 分鐘
    DEFAULT_DOWNLOAD_CD = 60  # 秒
    MAX_MULTI_THREAD = 5
    MAX_MULTI_DOWNLOAD_SEGMENT = 5


class SeasonPattern:
    """季度相關正則表達式。"""

    SEASON_TITLE = r"第[零一二三四五六七八九十]{1,3}季$"
    EXTRA_TITLE = r"\[(特別篇|中文配音)\]$"


class ChineseNumberMap:
    """中文數字映射。"""

    MAPPING = {
        "零": 0,
        "一": 1,
        "二": 2,
        "兩": 2,
        "三": 3,
        "四": 4,
        "五": 5,
        "六": 6,
        "七": 7,
        "八": 8,
        "九": 9,
        "十": 10,
    }
