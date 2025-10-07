import codecs
import json
import random
import re
import socket
import sys
import time
from pathlib import Path
from urllib.parse import quote

import chardet
import httpx

from .config_manager import load_config, save_config
from .schema import Config, Settings

# 你猜猜看我是 .exe 或是 .py 檔案
if getattr(sys, "frozen", False):
    working_dir = Path(sys.executable).parent
else:
    # 回到專案根目錄（從 src/backend 回到 ../../）
    working_dir = Path(__file__).resolve().parent.parent.parent

# 配置文件路徑
config_path = working_dir / "config.toml"
sn_list_path = working_dir / "sn_list.txt"
logs_dir = working_dir / "logs"
aniGamerPlus_version = "v24.6"
cookie = None
max_multi_thread = 5
max_multi_downloading_segment = 5
tasks_progress_rate = {}  # 储存任务进度, 供面板使用,
# 格式: {sn: {'rate': 任務进度百分比(float), 'status': 任務状态, 'filename': 文件名} }
# 任務状态有:  '正在下載' '正在解密合并' '正在移至番劇目錄' '任務失敗, 等待重啓' '等待下載'

# 已完成任務記錄（供 Dashboard 顯示）
completed_tasks = {}  # 储存已完成的任務, 格式: {sn: {'filename': str, 'completion_time': str, 'status': 'success'|'failed'}}
_completed_tasks_lock = None  # 線程鎖，確保並發安全

# 任務佇列資訊（由 ani_gamer_next 模組設置）
_task_queue_ref = None  # 儲存對 ani_gamer_next.queue 的引用
_processing_queue_ref = None  # 儲存對 ani_gamer_next.processing_queue 的引用

# 手動任務佇列（用於 Dashboard 手動下載）
manual_task_queue = {}  # 格式: {sn: {"filename": str, "mode": str, "started": bool}}
_manual_task_lock = None  # 線程鎖

# 全局配置對象
_global_config: Config | None = None


def get_config() -> Config:
    """獲取全局配置對象。

    Returns:
        Config: 配置對象
    """
    global _global_config
    if _global_config is None:
        _global_config = load_config()
    return _global_config


def __color_print(sn, err_msg, detail="", status=0, no_sn=False, display=True):
    # 避免与 color_print.py 相互调用产生问题
    from .color_print import err_print  # type: ignore[used-before-def]

    err_print(sn, err_msg, detail=detail, status=status, no_sn=no_sn, display=display)


def get_max_multi_thread():
    return max_multi_thread


def legalize_filename(filename):
    # 文件名合法化
    legal_filename = re.sub(r"\|+", "｜", filename)  # 处理 | , 转全型｜
    legal_filename = re.sub(r"\?+", "？", legal_filename)  # 处理 ? , 转中文 ？
    legal_filename = re.sub(r"\*+", "＊", legal_filename)  # 处理 * , 转全型＊
    legal_filename = re.sub(r"<+", "＜", legal_filename)  # 处理 < , 转全型＜
    legal_filename = re.sub(r">+", "＞", legal_filename)  # 处理 < , 转全型＞
    legal_filename = re.sub(r"\"+", "＂", legal_filename)  # 处理 " , 转全型＂
    legal_filename = re.sub(r":+", "：", legal_filename)  # 处理 : , 转中文：
    legal_filename = re.sub(r"\\", "＼", legal_filename)  # 处理 \ , 转全型＼
    legal_filename = re.sub(r"/", "／", legal_filename)  # 处理 / , 转全型／
    return legal_filename


def get_working_dir():
    return str(working_dir)


def get_config_path():
    """獲取配置文件路徑（返回 config.toml）。"""
    return str(config_path)


def get_sn_list_content():
    """返回 sn_list 所有内容（包括注释），提供給 Web 控制台。"""
    cfg = get_config()
    return cfg.sn_list


def __init_settings():
    """初始化設置（已棄用，使用 TOML 系統）。"""
    # 此函數已廢棄，新系統使用 config_manager
    pass


def del_bom(path, display=True):
    # 处理 UTF-8-BOM
    have_bom = False
    with open(path, "rb") as f:
        content = f.read()
        if content.startswith(codecs.BOM_UTF8):
            content = content[len(codecs.BOM_UTF8) :]
            have_bom = True
    if have_bom:
        filename = Path(path).name
        if display:
            __color_print(
                0, "發現 " + filename + " 帶有BOM頭, 將移除后保存", no_sn=True
            )
        try_counter = 0
        while True:
            try:
                with open(path, "wb") as f:
                    f.write(content)
            except BaseException as e:
                if try_counter > 3:
                    if display:
                        __color_print(
                            0,
                            "無BOM " + filename + " 保存失敗! 发生异常: " + str(e),
                            status=1,
                            no_sn=True,
                        )
                    raise e
                random_wait_time = random.uniform(2, 5)
                time.sleep(random_wait_time)
                try_counter = try_counter + 1
            else:
                if display:
                    __color_print(
                        0, "無BOM " + filename + " 保存成功", status=2, no_sn=True
                    )
                break


# 全局 Settings 對象緩存
_global_settings: Settings | None = None


def get_settings(skip_dashboard_check: bool = False) -> Settings:
    """獲取運行時設置對象（Settings dataclass）。

    Args:
        skip_dashboard_check: 是否跳過 Dashboard 檢查（避免在 write_settings 時自動禁用）

    Returns:
        Settings: 運行時設置對象
    """
    global _global_settings, _global_config
    from dataclasses import replace

    if _global_settings is None:
        # 使用新的 TOML 配置系統
        _global_config = load_config()
        cfg = _global_config

        # 準備需要覆蓋的字段（防呆處理和路徑解析）
        overrides = {}

        # 防呆處理：確保類型正確
        overrides["check_frequency"] = int(cfg.check_frequency)
        overrides["download_resolution"] = str(cfg.download_resolution)
        overrides["zerofill"] = int(cfg.zerofill)

        # 防呆處理：驗證下載模式
        if not re.match(r"^(all|latest|largest-sn)$", cfg.default_download_mode):
            overrides["default_download_mode"] = "latest"

        # 防呆處理：日誌數量至少為 1
        overrides["quantity_of_logs"] = max(cfg.quantity_of_logs, 1)

        # 防呆處理：UA 不能為空
        if not cfg.ua:
            overrides["ua"] = (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"
            )

        # 路徑處理：番劇目錄
        if cfg.bangumi_dir and Path(cfg.bangumi_dir).exists():
            overrides["bangumi_dir"] = str(Path(cfg.bangumi_dir).resolve())
        else:
            overrides["bangumi_dir"] = str(working_dir / "bangumi")

        # 路徑處理：緩存目錄
        if cfg.temp_dir and Path(cfg.temp_dir).exists():
            overrides["temp_dir"] = str(Path(cfg.temp_dir).resolve())
        else:
            overrides["temp_dir"] = str(working_dir / "temp")

        # 運行時計算：是否使用 Gost 代理
        overrides["use_gost"] = not any(
            [
                re.match(r"^http://", cfg.proxy.lower()),
                re.match(r"^https://", cfg.proxy.lower()),
                re.match(r"^socks5://", cfg.proxy.lower()),
                re.match(r"^socks5h://", cfg.proxy.lower()),
            ]
        )

        # 防呆處理：代理設置
        overrides["use_proxy"] = cfg.use_proxy and bool(cfg.proxy)

        # 防呆處理：線程數限制
        overrides["multi_thread"] = min(cfg.multi_thread, max_multi_thread)
        overrides["multi_downloading_segment"] = min(
            cfg.multi_downloading_segment, max_multi_downloading_segment
        )

        # 防呆處理：影片格式
        if cfg.video_filename_extension.lower() == "flv":
            overrides["video_filename_extension"] = "mp4"
        if (
            overrides.get(
                "video_filename_extension", cfg.video_filename_extension
            ).lower()
            != "mp4"
        ):
            overrides["faststart_movflags"] = False

        # 日誌清理
        if cfg.save_logs:
            __remove_superfluous_logs(
                overrides.get("quantity_of_logs", cfg.quantity_of_logs)
            )

        # Dashboard 檢查
        if not skip_dashboard_check and cfg.use_dashboard:
            if not (working_dir / "dist").exists():
                overrides["use_dashboard"] = False
                __color_print(
                    0,
                    "Web控制面板",
                    "未發現控制面板所必須的 dist 資料夾（前端未構建），运行時禁用控制面板（不會保存到配置文件）! 請先執行: npm run build",
                    no_sn=True,
                    status=1,
                )

        # 運行時專屬字段
        overrides["working_dir"] = str(working_dir)
        overrides["aniGamerPlus_version"] = aniGamerPlus_version

        # 使用 dataclass replace 創建 Settings（繼承所有 Config 字段 + 覆蓋值）
        # 注意：不使用 asdict() 以保持嵌套 dataclass 類型
        # 創建一個臨時 Settings 對象，然後用 replace 覆蓋字段
        base_settings = Settings(
            # 從 cfg 複製所有字段（Settings 繼承 Config，所以可以直接傳遞）
            **{field: getattr(cfg, field) for field in cfg.__dataclass_fields__},
            # 添加運行時專屬字段的默認值
            working_dir="",
            use_gost=False,
            aniGamerPlus_version="",
        )
        _global_settings = replace(base_settings, **overrides)

    return _global_settings


def read_settings(
    config: dict | None = None, skip_dashboard_check: bool = False
) -> Settings:
    """讀取配置文件並返回 Settings 對象。

    Args:
        config: 用於檢查 Web 控制台回傳的配置（字典格式），忽略此參數
        skip_dashboard_check: 是否跳過 Dashboard 檢查

    Returns:
        Settings: 運行時設置對象
    """
    return get_settings(skip_dashboard_check=skip_dashboard_check)


def invalidate_settings_cache() -> None:
    """清除 Settings 緩存，用於配置更新後重新加載。"""
    global _global_settings
    _global_settings = None


def check_encoding(file_path):
    # 识别文件编码, 将非 UTF-8 编码转为 UTF-8
    with open(file_path, "rb") as f:
        data = f.read()
        file_encoding = chardet.detect(data)["encoding"]  # 识别文件编码
        if file_encoding == "utf-8" or file_encoding == "ascii":
            # 如果为 UTF-8 编码, 无需操作
            return
        else:
            # 如果为其他编码, 则转为 UTF-8 编码, 包含處理 BOM 頭
            with open(file_path, "wb") as f2:
                __color_print(
                    0,
                    "檔案讀取",
                    file_path + " 編碼為 " + file_encoding + " 將轉碼為 UTF-8",
                    no_sn=True,
                    status=1,
                )
                data = data.decode(file_encoding)  # 解码
                data = data.encode("utf-8")  # 编码
                f2.write(data)  # 写入文件
                __color_print(
                    0, "檔案讀取", file_path + " 轉碼成功", no_sn=True, status=2
                )


def _parse_sn_list_text(sn_list_text: str, default_download_mode: str) -> dict:
    """解析 sn_list 文本內容為字典。

    Args:
        sn_list_text: sn_list 文本內容
        default_download_mode: 默認下載模式

    Returns:
        dict: 解析後的 sn 字典
    """
    sn_dict = {}
    bangumi_tag = ""

    for i in sn_list_text.splitlines():
        if re.match(r"^@.+", i):  # 读取番剧分类
            bangumi_tag = i[1:].rstrip()
            continue
        elif re.match(r"^@ *", i):
            bangumi_tag = ""
            continue
        i = re.sub(r"#.+$", "", i).strip()  # 刪除注释
        i = re.sub(r" +", " ", i)  # 去除多余空格
        a = i.split(" ")
        if not a[0]:  # 跳过纯注释行
            continue
        if re.match(r"^\d+$", a[0]):
            rename = ""
            if len(a) > 1:  # 如果有特別指定下载模式
                if re.match(r"^(all|latest|largest-sn)$", a[1]):  # 仅认可合法的模式
                    sn_dict[int(a[0])] = {"mode": a[1]}
                else:
                    sn_dict[int(a[0])] = {
                        "mode": default_download_mode
                    }  # 非法模式一律替换成默认模式
                # 是否有设定番剧重命名
                if re.match(r".*<.*>.*", i):
                    rename = re.findall(r"<.*>", i)[0][1:-1]
            else:  # 没有指定下载模式则使用默认设定
                sn_dict[int(a[0])] = {"mode": default_download_mode}
            bangumi_tag = re.sub(r"( )+$", "", bangumi_tag)
            sn_dict[int(a[0])]["tag"] = bangumi_tag
            sn_dict[int(a[0])]["rename"] = rename

    return sn_dict


def read_sn_list():
    """讀取 sn_list（優先從 config.toml，自動遷移 sn_list.txt）。"""
    settings = get_settings()
    cfg = get_config()

    # 自動遷移舊的 sn_list.txt 檔案
    # 防呆 https://github.com/miyouzi/aniGamerPlus/issues/5
    error_sn_list_path = sn_list_path.parent / "sn_list.txt.txt"
    if error_sn_list_path.exists():
        error_sn_list_path.rename(sn_list_path)

    # 如果 config 中沒有 sn_list，但 sn_list.txt 存在，則遷移
    if not cfg.sn_list and sn_list_path.exists():
        if sn_list_path.stat().st_size > 0:
            check_encoding(sn_list_path)
            with open(sn_list_path, "r", encoding="utf-8") as f:
                sn_list_text = f.read()

            # 保存到 config
            cfg.sn_list = sn_list_text
            save_config(cfg)

            # 備份並移除舊檔案
            backup_path = sn_list_path.with_suffix(".txt.bak")
            if backup_path.exists():
                backup_path.unlink()
            sn_list_path.rename(backup_path)
            print(f"已將 sn_list.txt 遷移到 config.toml，舊檔案已備份到 {backup_path}")

    # 從 config 讀取並解析 sn_list
    if not cfg.sn_list:
        return {}

    return _parse_sn_list_text(cfg.sn_list, settings.default_download_mode)


def test_cookie():
    # 测试cookie.txt是否存在, 是否能正常读取, 并记录日志
    read_cookie(log=True)


def read_cookie(log=False):
    """讀取 Cookie 配置（僅從 config.toml）。

    Returns:
        dict: Cookie 字典，格式為 {key: value}
    """
    # 如果 cookie 已讀入內存，則直接返回
    global cookie
    if cookie is not None:
        return cookie

    # 從 config.toml 讀取
    cfg = get_config()
    if cfg.cookie and cfg.cookie.strip():
        if log:
            __color_print(
                0, "讀取cookie", detail="從 config.toml 讀取", no_sn=True, display=False
            )
        cookie_str = cfg.cookie.strip()
        cookies = __parse_cookie_string(cookie_str)
        if cookies:
            cookie = cookies
            if log:
                __color_print(
                    0,
                    "讀取cookie",
                    detail="已讀取cookie",
                    no_sn=True,
                    display=False,
                )
            return cookie

    # 沒有找到 cookie
    if log:
        __color_print(
            0,
            "讀取cookie",
            detail="未設置 cookie（請在 config.toml 中配置 cookie 字段）",
            no_sn=True,
            display=False,
        )
    cookie = {}
    return cookie


def __parse_cookie_string(cookie_str: str) -> dict:
    """解析 cookie 字符串為字典。

    Args:
        cookie_str: Cookie 字符串，格式為 "key1=value1; key2=value2"

    Returns:
        dict: Cookie 字典
    """
    try:
        cookies = dict(
            [
                list(
                    map(
                        lambda x: quote(x, safe="")
                        if re.match(r"[\u4e00-\u9fa5]", x)
                        else x,
                        l.split("=", 1),
                    )
                )
                for l in cookie_str.split("; ")
                if "=" in l
            ]
        )
        cookies.pop("ckBH_lastBoard", None)
        return cookies
    except Exception as e:
        __color_print(0, "解析cookie", f"解析失敗: {e}", no_sn=True, status=1)
        return {}


def invalid_cookie():
    """標記 cookie 失效，清除內存中的 cookie。"""
    global cookie
    cookie = None  # 重置已讀取的 cookie
    __color_print(
        0,
        "Cookie 失效",
        "請在 config.toml 中更新 cookie 字段",
        no_sn=True,
        status=1,
    )


def time_stamp_to_time(timestamp):
    # 把时间戳转化为时间: 1479264792 to 2016-11-16 10:53:12
    # 代码来自: https://www.cnblogs.com/shaosks/p/5614630.html
    timeStruct = time.localtime(timestamp)
    return time.strftime("%Y-%m-%d %H:%M:%S", timeStruct)


def get_cookie_time():
    """獲取 cookie 最後修改時間（從 config.toml）。"""
    toml_mtime = config_path.stat().st_mtime
    return time_stamp_to_time(toml_mtime)


def renew_cookies(new_cookie, log=True):
    """刷新並保存 Cookie（使用 CookieManager）。

    Args:
        new_cookie: 新的 Cookie 字典
        log: 是否記錄日誌
    """
    global cookie, _global_config
    from .cookie_manager import CookieManager

    # 重置全域 cookie
    cookie = None

    # 使用 CookieManager
    cfg = get_config()
    manager = CookieManager(cfg)

    # 先刷新 cookie（向動畫瘋發送請求獲取最新 cookie）
    refreshed_cookie = manager.refresh_cookies(new_cookie)

    # 保存刷新後的 cookie
    if manager.save_cookies(refreshed_cookie):
        _global_config = get_config()  # 重新載入配置
        if log:
            __color_print(
                0,
                "Cookie 更新成功",
                f"Keys: {', '.join(refreshed_cookie.keys())}",
                status=2,
                no_sn=True,
                display=False,
            )
    else:
        __color_print(0, "Cookie 保存失敗", status=1, no_sn=True)


def read_latest_version_on_github():
    req = "https://api.github.com/repos/miyouzi/aniGamerPlus/releases/latest"
    remote_version = {}
    try:
        with httpx.Client() as client:
            response = client.get(req, timeout=3)
            latest_releases_info = response.json()
            remote_version["tag_name"] = latest_releases_info["tag_name"]
            remote_version["body"] = latest_releases_info["body"]  # 更新内容
        __color_print(0, "檢查更新", "檢查更新成功", no_sn=True, display=False)
    except:
        remote_version["tag_name"] = aniGamerPlus_version  # 拉取github版本号失败
        remote_version["body"] = ""
        __color_print(0, "檢查更新", "檢查更新失敗", no_sn=True, display=False)
    return remote_version


def __remove_superfluous_logs(max_num):
    if logs_dir.exists():
        logs_list = [x.name for x in logs_dir.iterdir() if "web" not in x.name]
        if len(logs_list) > max_num:
            logs_list.sort()
            logs_need_remove = logs_list[0 : len(logs_list) - max_num]
            for log in logs_need_remove:
                log_path = logs_dir / log
                log_path.unlink()
                __color_print(0, "刪除過期日志: " + log, no_sn=True, display=False)


def write_settings(web_config: dict | Settings):
    """寫入配置到文件。

    Args:
        web_config: 配置字典或 Settings 對象
    """
    global _global_config, _global_settings

    # 如果是 Settings 對象，轉換為字典
    if isinstance(web_config, Settings):
        from dataclasses import asdict

        web_config = asdict(web_config)

    # 創建副本以避免修改原始字典
    web_config = web_config.copy()

    # 還原配置
    a = working_dir / "bangumi"  # 默认番剧目录
    b = working_dir / "temp"  # 默认缓存目录
    if Path(web_config.get("bangumi_dir", "")).resolve() == a.resolve():
        web_config["bangumi_dir"] = ""
    if Path(web_config.get("temp_dir", "")).resolve() == b.resolve():
        web_config["temp_dir"] = ""

    # 移除運行時生成的字段和 sn_list（sn_list 應該獨立管理，不應該通過 Settings 保存）
    for key in ["working_dir", "aniGamerPlus_version", "use_gost", "sn_list"]:
        web_config.pop(key, None)

    # 處理 multi-thread -> multi_thread 的映射
    if "multi-thread" in web_config:
        web_config["multi_thread"] = web_config.pop("multi-thread")

    # 使用新的 TOML 配置系統保存
    try:
        from schema import CoolQSettings, DashboardConfig, FTPConfig
        from dataclasses import replace

        # 處理嵌套對象
        if "ftp" in web_config and isinstance(web_config["ftp"], dict):
            web_config["ftp"] = FTPConfig(**web_config["ftp"])
        if "coolq_settings" in web_config and isinstance(
            web_config["coolq_settings"], dict
        ):
            web_config["coolq_settings"] = CoolQSettings(**web_config["coolq_settings"])
        if "dashboard" in web_config and isinstance(web_config["dashboard"], dict):
            web_config["dashboard"] = DashboardConfig(**web_config["dashboard"])

        # 獲取當前 config 以保留 sn_list
        current_config = get_config()

        # 使用 replace 更新配置，保留 sn_list
        config_obj = replace(current_config, **web_config)
        _global_config = config_obj
        _global_settings = None  # 清除緩存
        save_config(config_obj)
    except Exception as e:
        # 如果 TOML 寫入失敗，回退到 JSON
        __color_print(
            0, f"TOML 配置寫入失敗: {e}, 使用 JSON 格式", status=1, no_sn=True
        )
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(web_config, f, ensure_ascii=False, indent=4)


def write_sn_list(sn_list_content: str):
    """寫入 sn_list 內容到 config.toml。

    Args:
        sn_list_content: sn_list 文本內容
    """
    cfg = get_config()
    cfg.sn_list = sn_list_content
    save_config(cfg)


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
    except:
        local_ip.close()
    return local_ip


def parse_proxy(proxy_str: str) -> dict:
    if len(proxy_str) == 0 or proxy_str.isspace():
        return {}

    result = {}

    if re.match(r".*@.*", proxy_str):
        proxy_user = re.sub(r":(\/\/)?", "", re.findall(r":\/\/.*?:", proxy_str)[0])
        proxy_passwd = re.sub(
            r"(:\/\/:)?@?",
            "",
            re.sub(proxy_user, "", re.findall(r":.*@", proxy_str)[0]),
        )
        result["proxy_user"] = proxy_user
        result["proxy_passwd"] = proxy_passwd
        proxy_str = proxy_str.replace(proxy_user + ":" + proxy_passwd + "@", "")
    else:
        result["proxy_user"] = None
        result["proxy_passwd"] = None

    proxy_protocol = re.sub(r":\/\/.*", "", proxy_str).upper()
    proxy_ip = re.sub(r":(\/\/)?", "", re.findall(r":.*:", proxy_str)[0])
    proxy_port = re.sub(r":", "", re.findall(r":\d+", proxy_str)[0])

    result["proxy_protocol"] = proxy_protocol
    result["proxy_ip"] = proxy_ip
    result["proxy_port"] = proxy_port

    return result


def set_task_queue_refs(queue_ref, processing_queue_ref):
    """設置任務佇列的引用（由 ani_gamer_next 模組呼叫）。

    Args:
        queue_ref: queue 字典的引用
        processing_queue_ref: processing_queue 列表的引用
    """
    global _task_queue_ref, _processing_queue_ref, _completed_tasks_lock, _manual_task_lock
    import threading

    _task_queue_ref = queue_ref
    _processing_queue_ref = processing_queue_ref

    # 初始化鎖
    if _completed_tasks_lock is None:
        _completed_tasks_lock = threading.Lock()
    if _manual_task_lock is None:
        _manual_task_lock = threading.Lock()


def add_manual_task(sn: int, filename: str, mode: str = "unknown"):
    """添加手動任務到等待隊列。
    
    Args:
        sn: 任務 SN
        filename: 文件名
        mode: 下載模式
    """
    global manual_task_queue, _manual_task_lock
    import threading
    
    if _manual_task_lock is None:
        _manual_task_lock = threading.Lock()
    
    with _manual_task_lock:
        manual_task_queue[int(sn)] = {
            "filename": filename,
            "mode": mode,
            "started": False  # 是否已開始執行（獲取到線程資源）
        }


def start_manual_task(sn: int):
    """標記手動任務已開始執行（獲取到線程資源）。
    
    Args:
        sn: 任務 SN
    """
    global manual_task_queue, _manual_task_lock
    
    if _manual_task_lock is None:
        return
    
    with _manual_task_lock:
        if int(sn) in manual_task_queue:
            manual_task_queue[int(sn)]["started"] = True


def remove_manual_task(sn: int):
    """從手動任務隊列中移除任務。
    
    Args:
        sn: 任務 SN
    """
    global manual_task_queue, _manual_task_lock
    
    if _manual_task_lock is None:
        return
    
    with _manual_task_lock:
        if int(sn) in manual_task_queue:
            del manual_task_queue[int(sn)]


def record_completed_task(sn: int, filename: str, status: str = "success"):
    """記錄已完成的任務。

    Args:
        sn: 任務 SN
        filename: 文件名
        status: 任務狀態，'success' 或 'failed'
    """
    global completed_tasks, _completed_tasks_lock
    from datetime import datetime

    if _completed_tasks_lock is None:
        import threading
        _completed_tasks_lock = threading.Lock()

    with _completed_tasks_lock:
        completed_tasks[int(sn)] = {
            "filename": filename,
            "completion_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": status
        }

        # 根據配置限制已完成任務數量（0 表示不限制）
        cfg = get_config()
        max_tasks = cfg.max_completed_tasks
        if max_tasks > 0 and len(completed_tasks) > max_tasks:
            # 按完成時間排序，移除最舊的
            sorted_tasks = sorted(
                completed_tasks.items(),
                key=lambda x: x[1]["completion_time"],
                reverse=True
            )
            # 保留最新的 N 個
            completed_tasks.clear()
            for sn, info in sorted_tasks[:max_tasks]:
                completed_tasks[sn] = info


def get_completed_tasks():
    """獲取已完成的任務列表。

    Returns:
        dict: 已完成任務字典，格式: {sn: {"filename": str, "completion_time": str, "status": str}}
    """
    global completed_tasks, _completed_tasks_lock

    if _completed_tasks_lock is None:
        return {}

    with _completed_tasks_lock:
        # 返回副本，避免外部修改
        return completed_tasks.copy()


def get_task_queue_info():
    """獲取任務佇列資訊（供 WebSocket 使用）。

    Returns:
        dict: 包含 pending (等待中任務) 的字典
              格式: {
                  "pending": {sn: {"filename": str, "position": int, "mode": str}}
              }
    """
    result = {"pending": {}}

    # 如果沒有設置引用，返回空資料
    if _task_queue_ref is None or _processing_queue_ref is None:
        return result

    # 獲取等待中的任務
    # 1. 自動任務：在 queue 中但不在 processing_queue 中
    # 2. 手動任務：在 manual_task_queue 中且 started=False
    # 按 SN 排序以確保順序一致
    pending_tasks = []
    
    # 添加自動任務中的等待任務
    for sn, task_info in _task_queue_ref.items():
        if sn not in _processing_queue_ref:
            pending_tasks.append((sn, task_info))
    
    # 添加手動任務中的等待任務
    global manual_task_queue, _manual_task_lock
    if _manual_task_lock is not None:
        with _manual_task_lock:
            for sn, task_info in manual_task_queue.items():
                # 只顯示未開始的手動任務（started=False 且不在 tasks_progress_rate 中）
                if not task_info.get("started", False) and int(sn) not in tasks_progress_rate:
                    # 轉換為與自動任務相同的格式
                    pending_tasks.append((sn, {"mode": task_info.get("mode", "unknown")}))

    # 按照 SN 排序（數字順序）
    pending_tasks.sort(key=lambda x: x[0])

    # 調試日志：記錄等待中任務的數量
    if pending_tasks:
        __color_print(
            0, "任務佇列", 
            f"當前等待中任務: {len(pending_tasks)} 個 (總任務: {len(_task_queue_ref)}, 執行中: {len(_processing_queue_ref)})",
            no_sn=True, display=False
        )

    # 構建結果字典
    position = 1
    for sn, task_info in pending_tasks:
        # 優先從手動任務隊列獲取文件名（如果是手動任務）
        filename = None
        if _manual_task_lock is not None:
            with _manual_task_lock:
                if int(sn) in manual_task_queue:
                    manual_info = manual_task_queue[int(sn)]
                    if manual_info.get("filename") and manual_info["filename"] != f"SN: {sn}":
                        filename = manual_info["filename"]
        
        # 如果手動任務隊列中沒有詳細文件名，從資料庫讀取
        if filename is None:
            try:
                # 動態導入避免循環依賴
                from . import ani_gamer_next
                import sqlite3

                db_path = ani_gamer_next.db_path
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT bangumi_name, episode FROM anime WHERE sn = ?",
                    (int(sn),)
                )
                row = cursor.fetchone()
                cursor.close()
                conn.close()

                if row and row[0]:
                    filename = f"《{row[0]}》- {row[1]}"
                else:
                    filename = f"SN: {sn}"
            except Exception as e:
                # 如果資料庫查詢失敗，使用 SN 作為文件名
                __color_print(
                    0, "任務佇列", f"查詢 SN {sn} 資訊失敗: {e}", no_sn=True, display=False
                )
                filename = f"SN: {sn}"

        # 獲取任務模式
        if isinstance(task_info, dict):
            mode = task_info.get("mode", "unknown")
        else:
            mode = "unknown"

        result["pending"][str(sn)] = {
            "filename": filename,
            "position": position,
            "mode": mode
        }
        position += 1

    return result


if __name__ == "__main__":
    pass
