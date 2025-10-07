<h1 align="center">ani-gamer-next</h1>

<p align="center">
  <strong>巴哈姆特動畫瘋自動下載工具</strong><br>
  支援自動追蹤番劇更新、命令行批量下載，適合部署在伺服器或 NAS 上
</p>

<p align="center">
  <a href="#特性">特性</a> •
  <a href="#安裝">安裝</a> •
  <a href="#快速開始">快速開始</a> •
  <a href="#使用方式">使用方式</a> •
  <a href="#配置說明">配置說明</a> •
  <a href="#文檔">文檔</a>
</p>

---

## ⚠️ 重要提醒

1. **本專案依賴 ffmpeg**，請事先將 ffmpeg 放入系統 PATH 或程序目錄下
   - [**點擊這裡下載 ffmpeg**](https://ffmpeg.org/download.html)
   - 若不知道如何設置 PATH，直接將 `ffmpeg` 可執行檔放在程序同一目錄即可

2. **使用 Cookie 存在帳號封鎖風險**
   - [⚠️ Cookie 使用風險說明](https://github.com/miyouzi/aniGamerPlus/issues/207)
   - 封鎖後無法解除，請謹慎使用

## 特性

- ✅ 多線程下載，速度快
- ✅ 支援 Cookie，可下載 1080P
- ✅ 多種下載模式：最新一集、全部集數、最新上傳
- ✅ 自定義檢查更新間隔
- ✅ 自定義下載目錄和檔名格式
- ✅ 下載失敗自動重試
- ✅ 支援 FTP 上傳（支援斷點續傳、TLS）
- ✅ Cookie 自動刷新
- ✅ 支援代理（HTTP/HTTPS/SOCKS5）
- ✅ 日誌記錄功能
- ✅ 番劇分類管理
- ✅ Web 控制面板
- ✅ 彈幕下載（.ass 格式）
- ✅ 支援通知推送（酷Q、Telegram、Discord）
- ✅ Plex 整合

## 系統要求

- **Python**: 3.12 或以上
- **Node.js**: 16 或以上（僅 Web 控制面板需要）
- **ffmpeg**: 必須

## 安裝

### 方法一：使用 uv（推薦）

[uv](https://github.com/astral-sh/uv) 是一個快速的 Python 套件管理器。

```bash
# 1. 安裝 uv
curl -LsSf https://astral.sh/uv/install.sh | sh
# 或使用 pip
pip install uv

# 2. 下載源碼
git clone https://github.com/miyouzi/aniGamerPlus.git
cd aniGamerPlus

# 3. 安裝依賴
uv sync

# 4. 建構 Web 控制面板（可選）
npm install
npm run build
```

### 方法二：使用傳統 pip

```bash
# 1. 下載源碼
git clone https://github.com/miyouzi/aniGamerPlus.git
cd aniGamerPlus

# 2. 創建虛擬環境（建議）
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows

# 3. 安裝依賴
pip3 install -e .

# 4. 建構 Web 控制面板（可選）
npm install
npm run build
```

### 方法三：使用預編譯 EXE（僅 Windows）

Windows 用戶可以直接[**下載 EXE 檔案**](https://github.com/miyouzi/aniGamerPlus/releases/latest)使用。

## 快速開始

### 1. 初始化配置

```bash
# 複製配置範例
cp config-sample.toml config.toml

# 編輯配置檔（設定下載目錄、帳號密碼等）
nano config.toml
```

### 2. 啟動程式

**使用 Web 控制面板（推薦）：**

```bash
# 使用 uv
uv run ani-gamer-next

# 或使用 Python（需先啟用虛擬環境）
python3 -m src.backend.app

# 訪問 http://localhost:5000
```

**命令行模式：**

```bash
# 下載單集
uv run ani-gamer-next --sn 12345

# 下載整部番劇
uv run ani-gamer-next --sn 12345 --download_mode all

# 更多選項
uv run ani-gamer-next --help
```

## 使用方式

### Web 控制面板

1. 啟動程式後訪問 `http://localhost:5000`
2. 使用配置檔中設定的帳號密碼登入
3. 在控制面板中：
   - 管理訂閱清單
   - 查看下載進度
   - 修改配置
   - 手動添加下載任務

### 命令行模式

```bash
# 基本用法
ani-gamer-next --sn <SN碼> [選項]

# 常用選項
--sn SN                    # 影片 SN 碼
--resolution 1080          # 指定清晰度 (360/480/540/576/720/1080)
--download_mode MODE       # 下載模式 (single/latest/all/largest-sn/range/multi/sn-range/list/db)
--episodes 1,2,3-5         # 指定集數
--thread_limit 3           # 並發下載數
--danmu                    # 下載彈幕
--current_path             # 下載到當前目錄
--no_classify              # 不建立番劇資料夾
--information_only         # 僅查詢資訊
--my_anime                 # 匯出「我的動畫」至 my_anime.txt
```

**範例：**

```bash
# 下載單集
uv run ani-gamer-next --sn 12345

# 下載整部番劇的 1080P
uv run ani-gamer-next --sn 12345 --download_mode all --resolution 1080

# 下載指定集數（1,2,3 和 5-8 集）
uv run ani-gamer-next --sn 12345 --episodes 1,2,3,5-8

# 下載最新一集並包含彈幕
uv run ani-gamer-next --sn 12345 --download_mode latest --danmu

# 使用 3 個線程下載全部
uv run ani-gamer-next --sn 12345 --download_mode all --thread_limit 3

# 下載多個 SN
uv run ani-gamer-next --download_mode multi --episodes 12345,12346,12347

# 僅查詢影片資訊
uv run ani-gamer-next --sn 12345 --information_only
```

### Docker 運行

#### 使用官方 Image

```bash
docker run -td --name anigamerplus \
    -v /path/to/config.toml:/app/config.toml \
    -v /path/to/download:/app/bangumi \
    -v /path/to/aniGamer.db:/app/aniGamer.db \
    -p 5000:5000 \
    tonypepe/anigamerplus

# 訪問 localhost:5000 使用 Web 控制面板
```

**注意事項：**
1. `config.toml` 中的 Dashboard Host 請設定為 `0.0.0.0`
2. 不要設定 `bangumi_dir`，保持為空字串
3. 可綁定 cookie 至 `/app/cookie.txt`（可選）

#### 自行建構 Image

```bash
# 1. 下載源碼
git clone https://github.com/miyouzi/aniGamerPlus.git
cd aniGamerPlus

# 2. 建構 Image
docker build -t anigamerplus .

# 3. 運行容器
docker run -td --name anigamerplus \
    -v $(pwd)/config.toml:/app/config.toml \
    -v $(pwd)/bangumi:/app/bangumi \
    -p 5000:5000 \
    anigamerplus
```

### Docker Compose

```yaml
version: '3.8'
services:
  anigamerplus:
    image: tonypepe/anigamerplus
    container_name: anigamerplus
    ports:
      - "5000:5000"
    volumes:
      - ./config.toml:/app/config.toml
      - ./bangumi:/app/bangumi
      - ./aniGamer.db:/app/aniGamer.db
    restart: unless-stopped
```

## 配置說明

### 主配置檔（config.toml）

配置檔使用 TOML 格式，比 JSON 更易讀。參考 `config-sample.toml` 進行配置。

**主要配置項：**

```toml
# 目錄配置
bangumi_dir = ""              # 番劇保存目錄（留空使用默認 bangumi 目錄）
temp_dir = ""                 # 臨時檔案目錄（留空使用默認 temp 目錄）
classify_bangumi = true       # 是否建立番劇資料夾
classify_season = false       # 是否建立季度子目錄

# 下載配置
check_frequency = 5           # 檢查更新頻率（分鐘）
download_cd = 60              # 下載冷卻時間（秒）
parse_sn_cd = 5               # SN 解析冷卻時間（秒）
download_resolution = "1080"  # 下載清晰度
lock_resolution = false       # 鎖定清晰度（不存在則下載失敗）
only_use_vip = false          # 僅使用 VIP 帳號下載
default_download_mode = "latest"  # 默認下載模式 (latest/all/largest-sn)
use_copyfile_method = false   # 使用複製而非移動檔案（適用於 rclone）

# 多線程配置
multi_thread = 1              # 最大並發下載數
multi_upload = 3              # 最大並發上傳數
segment_download_mode = true  # 分段下載模式
multi_downloading_segment = 2 # 每個影片並發下載分段數
segment_max_retry = 8         # 分段最大重試次數（-1 無限重試）

# 檔名配置
add_bangumi_name_to_video_filename = true    # 檔名包含番劇名
add_resolution_to_video_filename = true      # 檔名包含清晰度
customized_video_filename_prefix = "【動畫瘋】"  # 檔名前綴
customized_bangumi_name_suffix = ""          # 番劇名後綴
customized_video_filename_suffix = ""        # 檔名後綴
video_filename_extension = "mp4"             # 影片副檔名
zerofill = 1                                 # 集數補零位數

# 網路配置
ua = "Mozilla/5.0 ..."        # User-Agent
use_proxy = false             # 是否使用代理
proxy = ""                    # 代理設定
no_proxy_akamai = false       # 不代理 Akamai CDN

# Web 控制面板
use_dashboard = true

[dashboard]
host = "127.0.0.1"            # 監聽地址（外部訪問用 0.0.0.0）
port = 5000                   # 監聽端口
username = "admin"            # 登入帳號
password = "admin"            # 登入密碼
SSL = false                   # 是否啟用 SSL
secret_key = ""               # JWT 密鑰（留空自動生成）

# 彈幕配置
danmu = false                 # 是否下載彈幕
danmu_ban_words = []          # 彈幕過濾詞

# 日誌配置
save_logs = true              # 是否記錄日誌
quantity_of_logs = 7          # 日誌保留數量

# 訂閱清單（也可在 Web 面板編輯）
sn_list = """
@本季新番
12345 latest <我推的孩子>
12346 all
"""
```

### 訂閱清單（sn_list）

在 `config.toml` 中直接編輯 `sn_list` 欄位，或在 Web 控制面板中編輯。

**格式：**

```
# 基本格式：SN碼 下載模式 <自定義名稱> #註解

# 範例
@本季新番
12345 latest <我推的孩子> #每週更新
12346 all <咒術迴戰>

@舊番補完
12347 all

@
12348  # 不分類的番劇
```

**下載模式：**
- `latest`: 僅下載最新一集
- `all`: 下載全部集數
- `largest-sn`: 下載最新上傳的一集

**特殊語法：**
- `@分類名`: 定義番劇分類，後續番劇會放在此分類資料夾
- `@`: 取消分類
- `<自定義名稱>`: 自定義番劇目錄名
- `#註解`: 添加註解說明

### Cookie 設定

如需下載 1080P 或會員限定內容，需要配置 Cookie。

**獲取 Cookie：**

1. 在瀏覽器無痕模式登入動畫瘋（勾選「保持登入狀態」）
2. 按 F12 打開開發者工具
3. 切換到 Network 標籤
4. 訪問動畫瘋首頁
5. 找到 `ani.gamer.com.tw` 請求
6. 複製 Cookie 字串

**設定 Cookie：**

- **方式一**：在 Web 控制面板的設定頁面貼上
- **方式二**：在 `config.toml` 中設定 `cookie` 欄位
- **方式三**：創建 `cookie.txt` 檔案（舊版相容）

**設定 User-Agent：**

必須與獲取 Cookie 的瀏覽器相同。

- 在 Web 控制面板可自動獲取當前瀏覽器 UA
- 或訪問 https://www.whatismyua.info/ 查看 UA
- 在 `config.toml` 中設定 `ua` 欄位

⚠️ **重要**：
- 請勾選「保持登入狀態」
- 使用無痕模式獲取 Cookie
- Cookie 會自動刷新，無需手動更新

### 代理設定

支援 HTTP、HTTPS 和 SOCKS5 代理。

**配置範例：**

```toml
use_proxy = true

# HTTP/HTTPS 代理
proxy = "http://user:passwd@example.com:1000"

# SOCKS5 代理（支援遠端 DNS）
proxy = "socks5h://127.0.0.1:1080"
```

**使用建議：**
- 建議啟用分段下載模式
- 網路不穩定時將 `multi_thread` 設為 1
- 可設定 `no_proxy_akamai = true` 不代理 CDN

### FTP 上傳

支援將下載的影片自動上傳到 FTP 伺服器。

```toml
upload_to_server = true

[ftp]
server = "ftp.example.com"
port = 21
user = "username"
pwd = "password"
tls = true                  # FTP over TLS
cwd = "/anime"              # 登入後的目錄
show_error_detail = false
max_retry_num = 15          # 支援斷點續傳
```

### 通知推送

支援多種通知方式：

**酷Q：**
```toml
coolq_notify = true

[coolq_settings]
msg_argument_name = "message"
message_suffix = "追加的資訊"
query = [
    "http://127.0.0.1:5700/send_group_msg?access_token=abc&group_id=12345678"
]
```

**Telegram：**
```toml
telebot_notify = true
telebot_token = "your_bot_token"
telebot_use_chat_id = true
telebot_chat_id = "your_chat_id"
```

**Discord：**
```toml
discord_notify = true
discord_token = "your_webhook_url"
```

### Plex 整合

```toml
plex_refresh = true
plex_url = "http://localhost:32400"
plex_token = "your_plex_token"
plex_section = "Anime"
plex_naming = true  # 使用 Plex 命名規則
```

## 文檔

### 用戶文檔
- [**快速開始**](docs/QUICK_START.md) - 5 分鐘上手指南
- [**使用指南**](docs/USAGE_GUIDE.md) - 詳細使用說明
- [**命令速查**](docs/COMMANDS.md) - 常用命令參考
- [**Cookie 管理**](docs/COOKIE_MANAGEMENT.md) - Cookie 設定詳解

### 開發文檔
- [**UV 使用指南**](docs/UV_USAGE_GUIDE.md) - uv 套件管理器說明
- [**Dashboard 開發**](docs/DASHBOARD_DEVELOPMENT.md) - Web 控制面板開發指南
- [**目錄結構**](docs/RESTRUCTURE_SUMMARY.md) - 專案目錄說明
- [**重構總結**](docs/REFACTORING_SUMMARY_ZH_TW.md) - 現代化重構說明

## 專案結構

```
aniGamerPlus/
├── src/
│   └── backend/           # Python 後端代碼
│       ├── app.py         # 主程式入口
│       ├── anime.py       # 動畫資訊解析
│       ├── downloader.py  # 下載器
│       ├── config.py      # 配置管理
│       └── ...
├── dashboard/             # Web 控制面板（已編譯）
│   ├── templates/         # HTML 模板
│   ├── static/           # 靜態資源
│   └── src/              # 前端源碼
├── scripts/              # 建構腳本
├── docs/                 # 文檔
├── config.toml           # 配置檔
├── config-sample.toml    # 配置範例
├── pyproject.toml        # Python 依賴
├── package.json          # Node.js 依賴
└── README.md
```

## 升級

```bash
# 拉取最新代碼
git pull

# 更新 Python 依賴
uv sync

# 更新前端依賴並重新建構
npm install
npm run build
```

## 常見問題

### Q: 提示找不到 ffmpeg？

**A:** 下載 ffmpeg 並放入系統 PATH 或程序目錄：
- [ffmpeg 官方下載](https://ffmpeg.org/download.html)
- **Windows**: 將 `ffmpeg.exe` 放在程式同一資料夾
- **Linux**: `sudo apt install ffmpeg` 或 `brew install ffmpeg`
- **macOS**: `brew install ffmpeg`

### Q: Web 控制面板無法訪問？

**A:** 檢查以下幾點：
1. 確認已建構前端：`npm run build`
2. 確認 `use_dashboard = true`
3. 確認端口未被占用：可在 `config.toml` 中更改端口
4. 如需外部訪問，將 `host` 設為 `0.0.0.0`

### Q: Cookie 失效怎麼辦？

**A:** Cookie 會自動刷新，如果持續失效：
1. 重新獲取 Cookie（使用無痕模式）
2. 確認 User-Agent 與瀏覽器相同
3. 檢查是否勾選「保持登入狀態」
4. 查看 [Cookie 管理文檔](docs/COOKIE_MANAGEMENT.md)

### Q: 下載速度慢或經常失敗？

**A:** 嘗試以下方法：
1. 啟用分段下載：`segment_download_mode = true`
2. 增加並發分段數：`multi_downloading_segment = 3`
3. 增加重試次數：`segment_max_retry = 10`
4. 如使用代理，將 `multi_thread` 設為 1

### Q: 命令行模式看不到進度？

**A:** 將 `multi_thread` 設為 1，並使用 `segment_download_mode = true`

### Q: Docker 容器無法訪問？

**A:** 確認：
1. `config.toml` 中 `host = "0.0.0.0"`
2. 端口映射正確：`-p 5000:5000`
3. 容器正在運行：`docker ps`

### Q: 如何更新到最新版本？

**A:** 執行以下命令：
```bash
git pull
uv sync
npm install
npm run build
```

### Q: 彈幕下載失敗？

**A:** 確認：
1. 配置中 `danmu = true` 或命令行使用 `--danmu`
2. 影片有彈幕內容
3. 使用 [XySubFilter](https://github.com/Cyberbeing/xy-VSFilter) 渲染彈幕

## 鳴謝

本專案 m3u8 獲取模組參考自 [BahamutAnimeDownloader](https://github.com/c0re100/BahamutAnimeDownloader)

## 第三方擴展工具

- [aniGamerPlus-swapHistorySnList](https://github.com/chumicat/aniGamerPlus-swapHistorySnList)
  - 將資料庫中的番劇導出到 sn_list，方便切換和檢查過往番劇更新

## 授權

MIT License

## 貢獻

歡迎提交 Issue 和 Pull Request！

在提交 PR 前，請確保：
1. 代碼遵循 PEP 8 規範
2. 添加適當的測試
3. 更新相關文檔

## 支援

如有問題或建議，歡迎：
- 提交 [Issue](https://github.com/miyouzi/aniGamerPlus/issues)
- 發起 [Pull Request](https://github.com/miyouzi/aniGamerPlus/pulls)
- 查看 [完整文檔](docs/)
- 加入討論區

---

<p align="center">Made with ❤️ by the aniGamerPlus Community</p>