# UV 使用指南

## 安裝依賴

```bash
# 安裝所有依賴（包括開發依賴）
uv sync

# 或者只安裝生產依賴
uv pip install -e .
```

## 運行後端

### 方式 1: 使用 uv run（推薦）

#### 運行主程式（自動下載器）
```bash
uv run ani-gamer-next
```

#### 啟動 Dashboard（生產模式）
```bash
# 先構建前端
uv run build-dashboard

# 啟動 Dashboard
uv run ani-gamer-next --dashboard
```

#### 啟動 Dashboard（開發模式）
```bash
# 終端 1: 啟動前端開發伺服器
npm run dev

# 終端 2: 啟動後端（開發模式）
uv run ani-gamer-next --dashboard --dev
```

#### 自訂 Dashboard 端口和地址
```bash
uv run ani-gamer-next --dashboard --host 0.0.0.0 --port 8080
```

### 方式 2: 使用 Python 模組運行

#### 運行主程式
```bash
uv run python -m src.backend.ani_gamer_next
```

#### 啟動 Dashboard 伺服器
```bash
uv run python -m src.backend.dashboard_server
```

### 方式 3: 直接運行 Python 文件

```bash
cd src/backend
uv run python dashboard_server.py
```

## 構建前端

```bash
# 使用專案腳本構建
uv run build-dashboard

# 或者直接使用 npm
npm run build
```

## 開發模式

### 前端開發
```bash
# 啟動 Vite 開發伺服器（支持熱更新）
npm run dev
```

### 前後端同時開發
```bash
# 終端 1: 啟動前端開發伺服器
npm run dev

# 終端 2: 啟動後端 Dashboard（開發模式）
uv run ani-gamer-next --dashboard --dev --port 5000
```

這樣前端會在 http://localhost:5173 運行（Vite 開發伺服器），
後端 API 會在 http://localhost:5000 運行，
前端會自動代理 API 請求到後端。

## 完整工作流程

### 首次設置
```bash
# 1. 安裝 Python 依賴
uv sync

# 2. 安裝前端依賴
npm install

# 3. 構建前端
npm run build
```

### 生產環境運行
```bash
# 運行自動下載器
uv run ani-gamer-next

# 或啟動 Dashboard
uv run ani-gamer-next --dashboard
```

### 開發環境
```bash
# 終端 1: 前端開發伺服器
npm run dev

# 終端 2: 後端開發模式
uv run ani-gamer-next --dashboard --dev
```

## 常用命令總結

| 功能 | 命令 |
|------|------|
| 安裝依賴 | `uv sync` |
| 構建前端 | `uv run build-dashboard` 或 `npm run build` |
| 運行下載器 | `uv run ani-gamer-next` |
| 啟動 Dashboard | `uv run ani-gamer-next --dashboard` |
| 開發模式 Dashboard | `uv run ani-gamer-next --dashboard --dev` |
| 前端開發伺服器 | `npm run dev` |
| 指定端口 | `uv run ani-gamer-next --dashboard -p 8080` |

## 注意事項

1. **首次運行 Dashboard** 需要先構建前端：`npm run build`
2. **開發模式** 需要同時運行前端開發伺服器和後端
3. **生產模式** 只需運行後端，前端已經構建到 `dist/` 目錄
4. 所有 `uv run` 命令都會自動管理虛擬環境，無需手動激活
5. Python 模組路徑已更新為 `src.backend.*`，確保在專案根目錄執行命令

## 疑難排解

### Dashboard 顯示「前端未構建」
```bash
# 執行前端構建
npm run build
```

### 模組導入錯誤
```bash
# 確保在專案根目錄執行
cd /path/to/aniGamerPlus
uv run ani-gamer-next --dashboard
```

### 端口被占用
```bash
# 使用不同端口
uv run ani-gamer-next --dashboard -p 8080
```

## ✅ 測試結果

### 已驗證的命令

```bash
# ✅ 構建前端 - 成功
npm run build

# ✅ 啟動 Dashboard - 成功
uv run ani-gamer-next --dashboard

# ✅ 自訂端口 - 成功
uv run ani-gamer-next --dashboard --port 5001
```

### 啟動成功輸出示例
```
============================================================
🌐 啟動 aniGamerPlus Dashboard
============================================================

✓ Dashboard 地址: http://localhost:5000
✓ 模式: 生產

按 Ctrl+C 停止伺服器

============================================================

INFO:uvicorn.error:Started server process [xxxxx]
INFO:uvicorn.error:Waiting for application startup.
INFO:uvicorn.error:Application startup complete.
INFO:uvicorn.error:Uvicorn running on http://0.0.0.0:5000 (Press CTRL+C to quit)
```

## 重構完成確認

✅ 所有後端文件已移至 `src/backend/`
✅ 所有前端文件已移至 `src/frontend/`
✅ 前端編譯輸出至根目錄 `dist/`
✅ 所有 Python 導入已修正為相對導入
✅ Dashboard 成功啟動並運行
✅ 路徑配置已更新
