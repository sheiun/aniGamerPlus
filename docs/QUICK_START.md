# aniGamerPlus 快速開始指南

## 📦 安裝

```bash
# 1. 安裝 Python 依賴
uv sync

# 2. 安裝前端依賴
npm install

# 3. 構建前端
npm run build
```

## 🚀 運行

### 啟動 Dashboard（推薦）

```bash
uv run ani-gamer-next --dashboard
```

然後在瀏覽器打開：http://localhost:5000

### 運行自動下載器

```bash
uv run ani-gamer-next
```

## ⚙️ 常用命令

| 命令 | 說明 |
|------|------|
| `uv run ani-gamer-next --dashboard` | 啟動 Dashboard |
| `uv run ani-gamer-next --dashboard -p 8080` | 指定端口 |
| `uv run ani-gamer-next --dashboard --dev` | 開發模式 |
| `uv run ani-gamer-next` | 運行下載器 |
| `uv run ani-gamer-next --help` | 查看幫助 |
| `npm run build` | 構建前端 |
| `npm run dev` | 前端開發模式 |

## 🔧 開發模式

### 前後端同時開發

```bash
# 終端 1: 啟動前端開發伺服器（支持熱更新）
npm run dev

# 終端 2: 啟動後端
uv run ani-gamer-next --dashboard --dev
```

## ❓ 常見問題

### Dashboard 提示「前端未構建」

```bash
# 執行前端構建
npm run build
```

### 端口被占用

```bash
# 使用其他端口
uv run ani-gamer-next --dashboard -p 8080
```

### 找不到模組

```bash
# 確保在專案根目錄執行命令
cd /path/to/aniGamerPlus
uv sync
```

## 📚 詳細文檔

- [UV 使用指南](UV_USAGE_GUIDE.md) - 完整的 UV 使用說明
- [重構總結](RESTRUCTURE_SUMMARY.md) - 目錄重構詳情

## 🎯 新目錄結構

```
aniGamerPlus/
├── src/
│   ├── frontend/          # 前端源碼
│   │   ├── src/          # JavaScript
│   │   ├── templates/    # HTML 模板
│   │   └── static/       # 靜態資源
│   └── backend/          # 後端 Python 代碼
├── dist/                 # 前端編譯輸出
├── package.json          # 前端依賴
├── pyproject.toml        # Python 依賴
└── config.toml           # 配置文件
```

## ✅ 測試狀態

- ✅ 前端構建：正常
- ✅ Dashboard 啟動：正常
- ✅ 自訂端口：正常
- ✅ 路徑配置：已更新
- ✅ 模組導入：已修正
