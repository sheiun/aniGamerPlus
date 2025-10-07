# aniGamerPlus 使用指南

## 🚀 快速開始

### 方式一：使用 `uv run` 命令（推薦）

```bash
# 1. 構建 Dashboard 前端（首次使用或前端更新後）
uv run build-dashboard

# 2. 啟動 Dashboard Web 介面
uv run app.py --dashboard

# 3. 運行自動下載器
uv run app.py
```

### 方式二：使用 `uv run python`

```bash
# 構建 Dashboard
uv run python scripts/build_dashboard.py

# 啟動 Dashboard
uv run python app.py --dashboard

# 運行下載器
uv run python app.py
```

### 方式三：直接運行（需先構建）

```bash
# 構建 Dashboard（僅需一次）
uv run build-dashboard

# 啟動 Dashboard
uv run app.py --dashboard

# 或運行下載器
uv run app.py
```

## 📋 詳細命令說明

### 構建 Dashboard 前端

構建 Dashboard 的靜態資源（HTML、CSS、JavaScript）：

```bash
uv run build-dashboard
```

**何時需要構建：**
- 首次使用 Dashboard
- 更新了前端代碼
- 拉取了新版本代碼

**構建產物：**
- 位置：`dashboard/static/dist/`
- 大小：約 150KB（Gzip 後 ~40KB）

### 啟動 Dashboard

#### 基本用法

```bash
uv run app.py --dashboard
```

訪問 `http://localhost:5000` 即可使用 Web 介面。

#### 自訂端口

```bash
uv run app.py --dashboard --port 8080
```

#### 自訂監聽地址

```bash
uv run app.py --dashboard --host 127.0.0.1
```

#### 開發模式（熱更新）

如果你正在修改前端代碼並希望即時看到效果：

```bash
# 終端 1: 啟動 Vite 開發伺服器
cd dashboard
npm run dev

# 終端 2: 啟動 Dashboard（開發模式）
uv run app.py --dashboard --dev
```

修改前端代碼後，瀏覽器會自動刷新，無需手動重新構建。

### 運行下載器

運行自動下載功能（原 `ani_gamer_next.py` 功能）：

```bash
uv run app.py
```

這會啟動自動下載器，根據 `config.toml` 和 `sn_list` 中的配置自動下載動畫。

## 📚 完整命令參考

### app.py 參數

```
uv run app.py [選項]

選項：
  -h, --help              顯示幫助信息
  -d, --dashboard         啟動 Web Dashboard
  --host HOST             Dashboard 監聽地址（默認：0.0.0.0）
  -p PORT, --port PORT    Dashboard 監聽端口（默認：5000）
  --dev                   開發模式（啟用 Vite HMR）

示例：
  uv run app.py                        # 運行下載器
  uv run app.py --dashboard            # 啟動 Dashboard
  uv run app.py -d -p 8080             # Dashboard 使用端口 8080
  uv run app.py --dashboard --dev      # Dashboard 開發模式
```

## 🔧 配置說明

### 初次配置

1. **複製配置範例**

```bash
cp config-sample.toml config.toml
```

2. **編輯配置文件**

```bash
# 使用任意文本編輯器
nano config.toml
# 或
vim config.toml
```

3. **配置 Dashboard 帳號**

在 `config.toml` 中設置：

```toml
[dashboard]
username = "admin"        # 修改為你的用戶名
password = "your_password"  # 修改為你的密碼
host = "0.0.0.0"
port = 5000
SSL = false
```

4. **配置訂閱清單**

創建 `sn_list` 文件，添加要訂閱的動畫：

```
# 格式：sn碼 下載模式 <自訂名稱>（可選） #備註（可選）
@分類名稱
12345 latest <我的最愛動畫> #這是備註
67890 all
```

也可以在 Dashboard Web 介面中直接編輯。

## 💡 使用場景

### 場景 1: 日常使用（自動下載）

```bash
# 1. 配置好 config.toml 和 sn_list
# 2. 運行下載器
uv run app.py

# 下載器會根據配置自動檢查更新並下載
```

### 場景 2: 使用 Web 介面管理

```bash
# 1. 確保 Dashboard 已構建
uv run build-dashboard

# 2. 啟動 Dashboard
uv run app.py --dashboard

# 3. 訪問 http://localhost:5000
#    - 查看下載進度
#    - 管理訂閱清單
#    - 手動添加下載任務
#    - 修改配置
```

### 場景 3: 開發 Dashboard 前端

```bash
# 終端 1: Vite 開發伺服器
cd dashboard
npm install  # 首次需要
npm run dev

# 終端 2: 後端（開發模式）
uv run app.py --dashboard --dev

# 訪問 http://localhost:5000 並開始修改前端代碼
# 修改會即時反映，無需刷新頁面
```

### 場景 4: 伺服器部署

```bash
# 1. 構建前端
uv run build-dashboard

# 2. 配置系統服務（以 systemd 為例）
# 創建 /etc/systemd/system/anigamerplus.service

[Unit]
Description=aniGamerPlus Dashboard
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/aniGamerPlus
ExecStart=/usr/bin/uv run app.py --dashboard --host 0.0.0.0 --port 5000
Restart=always

[Install]
WantedBy=multi-user.target

# 3. 啟動服務
sudo systemctl enable anigamerplus
sudo systemctl start anigamerplus
```

## 🔍 疑難排解

### Q: `uv run build-dashboard` 失敗

**A:** 檢查以下幾點：
1. 是否已安裝 Node.js：`node --version`
2. 是否已安裝 npm：`npm --version`
3. 查看錯誤信息，通常會指出問題所在

如果 Node.js 未安裝：
- Linux: `curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash - && sudo apt-get install -y nodejs`
- macOS: `brew install node`
- Windows: 訪問 https://nodejs.org/ 下載安裝

### Q: Dashboard 顯示 404 或樣式錯誤

**A:** 可能是前端未構建或構建失敗。
```bash
# 重新構建
uv run build-dashboard

# 檢查構建產物
ls -la dashboard/static/dist/
```

### Q: Dashboard 無法登入

**A:** 檢查 `config.toml` 中的 Dashboard 配置：
```toml
[dashboard]
username = "admin"      # 確認用戶名
password = "password"   # 確認密碼
```

### Q: 端口已被占用

**A:** 更換端口：
```bash
uv run app.py --dashboard --port 8080
```

### Q: 開發模式 HMR 不工作

**A:** 確保：
1. Vite 開發伺服器正在運行：`cd dashboard && npm run dev`
2. 使用了 `--dev` 標誌：`uv run app.py --dashboard --dev`
3. 檢查瀏覽器控制台是否有錯誤

## 📖 更多資源

- **Dashboard 開發指南**: [dashboard/README.md](dashboard/README.md)
- **前端重構總結**: [FRONTEND_REFACTORING_SUMMARY.md](FRONTEND_REFACTORING_SUMMARY.md)
- **快速參考**: [dashboard/QUICK_START.md](dashboard/QUICK_START.md)
- **遷移指南**: [dashboard/MIGRATION_GUIDE.md](dashboard/MIGRATION_GUIDE.md)

## 🎯 快速命令速查表

| 任務 | 命令 |
|------|------|
| 首次設置 | `cp config-sample.toml config.toml` |
| 構建前端 | `uv run build-dashboard` |
| 啟動 Dashboard | `uv run app.py --dashboard` |
| 運行下載器 | `uv run app.py` |
| 開發前端 | `cd dashboard && npm run dev` |
| 格式化前端代碼 | `cd dashboard && npm run format` |
| 檢查前端代碼 | `cd dashboard && npm run lint` |

---

**提示**: 所有 `uv run` 命令都會自動管理虛擬環境和依賴，無需手動激活虛擬環境。
