"""FastAPI Web 控制台伺服器。

此模組提供 aniGamerPlus 的 Web 控制台介面，
支援配置管理、手動任務下達、即時進度監控等功能。

Classes:
    WebSocketTokenManager: WebSocket 認證令牌管理器
    SettingsManager: 配置管理器（帶快取）
"""

from __future__ import annotations

import asyncio
import json
import logging
import mimetypes
import random
import re
import secrets
import string
import threading
from datetime import datetime, timedelta, timezone
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Annotated, Any

import jwt
import uvicorn
from fastapi import (
    Cookie,
    Depends,
    FastAPI,
    HTTPException,
    Request,
    Response,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import (
    FileResponse,
    JSONResponse,
    PlainTextResponse,
    RedirectResponse,
)
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import config
from .ani_gamer_next import __cui as cui
from .color_print import err_print
from .schema import Settings

# Configuration
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("application/x-javascript", ".js")

WORKING_DIR = Path(config.get_working_dir())
FRONTEND_PATH = WORKING_DIR / "src" / "frontend"
STATIC_PATH = WORKING_DIR / "src" / "frontend" / "static"
DIST_PATH = WORKING_DIR / "dist"
LOGS_DIR = WORKING_DIR / "logs"


class WebSocketTokenManager:
    """Manages WebSocket authentication tokens."""

    def __init__(self) -> None:
        self._valid_tokens: set[str] = set()

    @staticmethod
    def _generate_token() -> str:
        """Generate a random 32-character token."""
        return "".join(random.sample(string.ascii_letters + string.digits, 32))

    def get_and_regenerate(self) -> str:
        """Get a new token."""
        new_token = self._generate_token()
        self._valid_tokens.add(new_token)

        # 限制有效 token 數量（保留最近 5 個）
        if len(self._valid_tokens) > 5:
            # 移除最舊的 token（set 不保證順序，但這裡只是為了限制大小）
            self._valid_tokens.pop()

        return new_token

    def consume(self, token: str | None) -> bool:
        """Check if token is valid and consume it."""
        if not token:
            return False

        if token in self._valid_tokens:
            self._valid_tokens.discard(token)
            return True

        return False


class SettingsManager:
    """Manages application settings with caching."""

    def __init__(self) -> None:
        self._cache: Settings | None = None

    def get(self) -> Settings:
        """Get settings with caching."""
        if self._cache is None:
            self._cache = config.read_settings()
        return self._cache

    def update(self, new_settings: Settings) -> None:
        """Update settings and invalidate cache."""
        config.write_settings(new_settings)
        self._cache = None


# Global instances
ws_token_manager = WebSocketTokenManager()
settings_manager = SettingsManager()


def setup_logging() -> None:
    """Configure logging with rotation."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("uvicorn")
    logging.basicConfig(level=logging.INFO)

    web_log_path = LOGS_DIR / "web.log"
    handler = TimedRotatingFileHandler(
        filename=str(web_log_path),
        when="midnight",
        backupCount=7,
        encoding="utf-8",
    )
    handler.suffix = "%Y-%m-%d.log"
    handler.extMatch = re.compile(r"^\d{4}-\d{2}-\d{2}\.log")
    logger.addHandler(handler)


setup_logging()


# Settings ID list - 定義前端可以修改的配置欄位
id_list = [
    'bangumi_dir',
    'temp_dir',
    'classify_bangumi',
    'lock_resolution',
    'segment_download_mode',
    'add_bangumi_name_to_video_filename',
    'add_resolution_to_video_filename',
    'download_resolution',
    'default_download_mode',
    'check_frequency',
    'multi_thread',
    'multi_downloading_segment',
    'customized_video_filename_prefix',
    'customized_video_filename_suffix',
    'ua',
    'use_mobile_api',
    'danmu',
    'use_proxy',
    'proxy_protocol',
    'proxy_ip',
    'proxy_port',
    'proxy_user',
    'proxy_passwd',
    'check_latest_version',
    'read_sn_list_when_checking_update',
    'read_config_when_checking_update',
    'save_logs',
    'quantity_of_logs',
    'max_completed_tasks',
    'download_cd',
    'parse_sn_cd',
    'cookie',
]


# JWT Configuration
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24


def get_or_create_secret_key() -> str:
    """Get or create persistent SECRET_KEY for JWT signing.

    Returns:
        str: The SECRET_KEY from config or newly generated one
    """
    from dataclasses import replace

    current_config = config.get_config()

    # 檢查配置中是否已有 secret_key
    if current_config.dashboard.secret_key:
        return current_config.dashboard.secret_key

    # 生成新的 secret_key
    new_secret_key = secrets.token_urlsafe(32)

    # 更新配置中的 dashboard.secret_key
    new_dashboard_config = replace(current_config.dashboard, secret_key=new_secret_key)
    new_config = replace(current_config, dashboard=new_dashboard_config)

    # 保存配置
    config.save_config(new_config)
    config.invalidate_settings_cache()
    settings_manager._cache = None

    err_print(
        0, "Dashboard", f"已生成並保存 JWT SECRET_KEY 到配置文件", no_sn=True, status=2
    )

    return new_secret_key


SECRET_KEY = get_or_create_secret_key()


# Pydantic models
class LoginRequest(BaseModel):
    """Login request model."""

    username: str
    password: str


def create_access_token(
    data: dict[str, Any], expires_delta: timedelta | None = None
) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(
    token: str | None = Cookie(None, alias="access_token"),
) -> dict[str, Any]:
    """Verify JWT token from cookie."""
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
        )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidSignatureError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


# FastAPI application
app = FastAPI(
    title="aniGamerPlus Dashboard",
    description="Web dashboard for aniGamerPlus anime downloader",
    version="1.0.0",
)

# Mount static files - 優先使用 dist，如果不存在則使用 src/frontend/static
if DIST_PATH.exists():
    app.mount("/static", StaticFiles(directory=str(DIST_PATH)), name="static")
else:
    # 開發模式或未構建時，使用源文件目錄
    if STATIC_PATH.exists():
        app.mount("/static", StaticFiles(directory=str(STATIC_PATH)), name="static")


# Exception handler for authentication errors
@app.exception_handler(HTTPException)
async def auth_exception_handler(request: Request, exc: HTTPException):
    """Return JSON error for 401 errors (SPA handles auth state)."""
    if exc.status_code == 401:
        return JSONResponse(
            status_code=exc.status_code, content={"detail": exc.detail}
        )
    raise exc


@app.post("/api/login")
async def login(login_data: LoginRequest, response: Response) -> JSONResponse:
    """Authenticate user and return JWT token."""
    settings = settings_manager.get()

    correct_username = settings.dashboard.username
    correct_password = settings.dashboard.password

    # Verify credentials
    is_correct_username = secrets.compare_digest(
        login_data.username.encode("utf-8"), correct_username.encode("utf-8")
    )
    is_correct_password = secrets.compare_digest(
        login_data.password.encode("utf-8"), correct_password.encode("utf-8")
    )

    if not (is_correct_username and is_correct_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    # Create access token
    access_token = create_access_token(data={"sub": login_data.username})

    # Set cookie
    response = JSONResponse(
        content={"status": "success", "message": "Login successful"}
    )
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_HOURS * 3600,
        path="/",
        samesite="lax",
    )

    return response


@app.get("/api/check_auth")
async def check_auth(token: str | None = Cookie(None, alias="access_token")) -> JSONResponse:
    """Check if user is authenticated."""
    if not token:
        return JSONResponse(content={"authenticated": False})
    
    try:
        jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return JSONResponse(content={"authenticated": True})
    except (jwt.ExpiredSignatureError, jwt.InvalidSignatureError, Exception):
        return JSONResponse(content={"authenticated": False})


@app.post("/api/logout")
async def logout(response: Response) -> JSONResponse:
    """Logout user by deleting JWT cookie."""
    response = JSONResponse(
        content={"status": "success", "message": "Logout successful"}
    )
    response.delete_cookie(key="access_token", path="/", samesite="lax")
    return response


@app.get("/")
async def home() -> FileResponse:
    """Serve SPA index page (no auth required - handled client-side)."""
    return FileResponse(FRONTEND_PATH / "index.html", media_type="text/html")


@app.get("/data/config.json")
async def get_config(
    _user: Annotated[dict[str, Any], Depends(verify_token)],
) -> JSONResponse:
    """Get web-relevant configuration (returns JSON format from config.toml)."""
    settings = config.read_settings()

    # 前端輔助字段（從 proxy 字段解析）
    proxy_fields = {'proxy_protocol', 'proxy_ip', 'proxy_port', 'proxy_user', 'proxy_passwd'}

    web_settings = {}
    for id_ in id_list:
        if id_ in proxy_fields:
            # 跳過前端輔助字段，這些會從 proxy 解析
            continue
        elif hasattr(settings, id_):
            web_settings[id_] = getattr(settings, id_)

    # 解析 proxy 字段為前端格式
    if hasattr(settings, 'proxy') and settings.proxy:
        proxy_str = settings.proxy
        # 解析格式: protocol://[user:pass@]host:port
        import re
        match = re.match(r'(\w+)://(([^:]+):([^@]+)@)?([^:]+):(\d+)', proxy_str)
        if match:
            web_settings['proxy_protocol'] = match.group(1).upper()
            web_settings['proxy_user'] = match.group(3) or ''
            web_settings['proxy_passwd'] = match.group(4) or ''
            web_settings['proxy_ip'] = match.group(5)
            web_settings['proxy_port'] = match.group(6)
        else:
            web_settings['proxy_protocol'] = ''
            web_settings['proxy_user'] = ''
            web_settings['proxy_passwd'] = ''
            web_settings['proxy_ip'] = ''
            web_settings['proxy_port'] = ''
    else:
        web_settings['proxy_protocol'] = ''
        web_settings['proxy_user'] = ''
        web_settings['proxy_passwd'] = ''
        web_settings['proxy_ip'] = ''
        web_settings['proxy_port'] = ''

    return JSONResponse(content=web_settings)


@app.post("/api/config")
async def upload_config(
    request: Request,
    _user: Annotated[dict[str, Any], Depends(verify_token)],
) -> JSONResponse:
    """Update configuration from web interface."""
    from dataclasses import replace

    data = await request.json()

    # 讀取當前的 Config（不是 Settings）
    current_config = config.get_config()

    # 前端輔助字段，不需要保存到配置（它們只是用來組成 proxy 字段）
    frontend_helper_fields = {
        "proxy_protocol",
        "proxy_ip",
        "proxy_port",
        "proxy_user",
        "proxy_passwd",
    }

    # 只更新 id_list 中的字段（這些是前端可以修改的字段）
    updates = {}
    for field_name in id_list:
        if field_name in frontend_helper_fields:
            # 跳過前端輔助字段
            continue
        if field_name in data:
            updates[field_name] = data[field_name]

    # 從前端輔助字段組合 proxy 字段
    if "proxy_protocol" in data and data.get("proxy_protocol"):
        protocol = data.get("proxy_protocol", "").lower()
        ip = data.get("proxy_ip", "")
        port = data.get("proxy_port", "")
        user = data.get("proxy_user", "")
        passwd = data.get("proxy_passwd", "")

        if ip and port:
            if user and passwd:
                updates["proxy"] = f"{protocol}://{user}:{passwd}@{ip}:{port}"
            else:
                updates["proxy"] = f"{protocol}://{ip}:{port}"
        else:
            updates["proxy"] = ""
    elif "proxy" in data:
        # 如果前端直接發送了 proxy 字段
        updates["proxy"] = data["proxy"]

    # 使用 dataclass replace 創建新的 Config 對象
    try:
        new_config = replace(current_config, **updates)

        # 保存到文件並更新緩存
        config.save_config(new_config)
        config.invalidate_settings_cache()
        settings_manager._cache = None

        err_print(
            0,
            "Dashboard",
            "通過 Web 控制臺更新了配置 (config.toml)",
            no_sn=True,
            status=2,
        )
        return JSONResponse(content={"status": "200"})
    except Exception as e:
        err_print(0, "Dashboard", f"配置更新失敗: {e}", no_sn=True, status=1)
        return JSONResponse(
            content={"status": "error", "message": str(e)}, status_code=400
        )


@app.post("/manualTask")
async def create_manual_task(
    request: Request,
    _user: Annotated[dict[str, Any], Depends(verify_token)],
) -> JSONResponse:
    """Create a manual download task.

    For 'all' mode downloads, this will add each episode as a separate task
    to the queue, allowing proper tracking in the UI.
    """
    data = await request.json()
    settings = config.read_settings()

    # Validate and set resolution
    valid_resolutions = ("360", "480", "540", "720", "1080")
    resolution = (
        data["resolution"]
        if data["resolution"] in valid_resolutions
        else settings.download_resolution
    )

    # Validate and set download mode
    valid_modes = ("single", "latest", "all", "largest-sn")
    mode = data["mode"] if data["mode"] in valid_modes else "single"

    # Validate and set thread limit
    thread = int(data["thread"]) if data["thread"] else 1
    max_threads = config.get_max_multi_thread()
    thread_limit = min(thread, max_threads)

    def run_cui_task() -> None:
        """Run the CUI download task in a separate thread."""
        try:
            cui(
                data["sn"],
                resolution,
                mode,
                thread_limit,
                [],
                classify=data["classify"],
                realtime_show=False,
                cui_danmu=data["danmu"],
            )
        except SystemExit:
            # cui() 會調用 sys.exit()，在 daemon thread 中捕獲並忽略
            pass
        except Exception as e:
            err_print(0, "Dashboard", f"手動任務執行失敗: {e}", no_sn=True, status=1)

    task_thread = threading.Thread(target=run_cui_task, daemon=True)
    task_thread.start()

    # 提示信息根據模式不同而變化
    mode_text = {
        "single": "單集",
        "latest": "最新一集",
        "all": "全部劇集",
        "largest-sn": "最大 SN"
    }.get(mode, mode)

    err_print(
        0,
        "Dashboard",
        f"通過 Web 控制臺下達了手動任務 (SN: {data['sn']}, 模式: {mode_text})",
        no_sn=True,
        status=2,
    )
    return JSONResponse(content={"status": "200"})


@app.get("/data/sn_list")
async def get_sn_list(
    _user: Annotated[dict[str, Any], Depends(verify_token)],
) -> PlainTextResponse:
    """Get sn_list content (API endpoint)."""
    return PlainTextResponse(content=config.get_sn_list_content())


@app.post("/api/sn_list")
async def update_sn_list(
    request: Request,
    _user: Annotated[dict[str, Any], Depends(verify_token)],
) -> JSONResponse:
    """Update sn_list content."""
    data = await request.body()
    config.write_sn_list(data.decode("utf-8"))
    config.invalidate_settings_cache()  # 使緩存失效
    err_print(0, "Dashboard", "通過 Web 控制臺更新了 sn_list", no_sn=True, status=2)
    return JSONResponse(content={"status": "200"})


@app.get("/data/get_token")
async def get_websocket_token(
    _user: Annotated[dict[str, Any], Depends(verify_token)],
) -> PlainTextResponse:
    """Generate and return a WebSocket authentication token."""
    token = ws_token_manager.get_and_regenerate()
    return PlainTextResponse(content=token, status_code=200)


@app.websocket("/data/tasks_progress")
async def stream_tasks_progress(websocket: WebSocket, token: str | None = None) -> None:
    """Stream task progress updates via WebSocket."""
    # Authenticate
    if not ws_token_manager.consume(token):
        await websocket.accept()
        await websocket.send_text("Unauthorized")
        await websocket.close()
        return

    await websocket.accept()

    # Stream progress updates
    try:
        # 立即發送第一次數據，不等待
        queue_info = config.get_task_queue_info()
        completed_tasks = config.get_completed_tasks()

        response_data = {
            "active": config.tasks_progress_rate,  # 正在執行的任務
            "pending": queue_info.get("pending", {}),  # 等待執行的任務
            "completed": completed_tasks,  # 已完成的任務
            "stats": {
                "active_count": len(config.tasks_progress_rate),
                "pending_count": len(queue_info.get("pending", {})),
                "completed_count": len(completed_tasks)
            }
        }

        msg = json.dumps(response_data)
        await websocket.send_text(msg)

        # 定期更新
        while True:
            await asyncio.sleep(1)
            
            # 獲取任務佇列資訊
            queue_info = config.get_task_queue_info()
            completed_tasks = config.get_completed_tasks()

            # 構建回傳數據
            response_data = {
                "active": config.tasks_progress_rate,  # 正在執行的任務
                "pending": queue_info.get("pending", {}),  # 等待執行的任務
                "completed": completed_tasks,  # 已完成的任務
                "stats": {
                    "active_count": len(config.tasks_progress_rate),
                    "pending_count": len(queue_info.get("pending", {})),
                    "completed_count": len(completed_tasks)
                }
            }

            msg = json.dumps(response_data)
            await websocket.send_text(msg)
    except WebSocketDisconnect:
        pass


def run() -> None:
    """Start the web server."""
    settings = settings_manager.get()

    host = settings.dashboard.host
    port = settings.dashboard.port

    uvicorn_config = {
        "host": host,
        "port": port,
        "log_config": None,
    }

    if settings.dashboard.SSL:
        ssl_path = WORKING_DIR / "src" / "frontend" / "sslkey"
        uvicorn_config.update(
            {
                "ssl_certfile": str(ssl_path / "server.crt"),
                "ssl_keyfile": str(ssl_path / "server.key"),
            }
        )

    uvicorn.run(app=app, **uvicorn_config)


if __name__ == "__main__":
    run()
