# ⚡ aniGamerPlus 快速參考

## 🎯 最常用命令

```bash
# 構建 Dashboard（首次使用或前端更新後）
uv run build-dashboard

# 啟動 Dashboard Web 介面
uv run app.py --dashboard

# 運行自動下載器
uv run app.py
```

## 📋 命令速查表

| 功能 | 命令 | 說明 |
|------|------|------|
| **構建前端** | `uv run build-dashboard` | 構建 Dashboard 靜態資源 |
| **啟動 Dashboard** | `uv run app.py --dashboard` | 啟動 Web 管理介面（端口 5000） |
| **自訂端口** | `uv run app.py -d -p 8080` | 使用端口 8080 |
| **運行下載器** | `uv run app.py` | 自動下載訂閱的動畫 |
| **開發模式** | `uv run app.py --dashboard --dev` | 啟用前端熱更新 |
| **查看幫助** | `uv run app.py --help` | 顯示所有可用選項 |

## 🔧 前端開發

| 任務 | 命令 |
|------|------|
| 安裝依賴 | `cd dashboard && npm install` |
| 開發伺服器 | `cd dashboard && npm run dev` |
| 構建生產版 | `cd dashboard && npm run build` |
| 程式碼檢查 | `cd dashboard && npm run lint` |
| 自動格式化 | `cd dashboard && npm run format` |

## 📁 重要文件

| 文件 | 用途 |
|------|------|
| `config.toml` | 主配置文件 |
| `sn_list` | 訂閱清單 |
| `app.py` | 主入口程式 |
| `dashboard/static/dist/` | 前端構建產物 |

## 🚀 快速流程

### 首次使用
```bash
# 1. 配置
cp config-sample.toml config.toml
vim config.toml

# 2. 構建前端
uv run build-dashboard

# 3. 啟動 Dashboard
uv run app.py --dashboard

# 4. 訪問 http://localhost:5000
```

### 開發前端
```bash
# 終端 1
cd dashboard && npm run dev

# 終端 2
uv run app.py --dashboard --dev
```

## 📚 完整文檔

- **詳細使用指南**: [USAGE_GUIDE.md](USAGE_GUIDE.md)
- **所有命令**: [COMMANDS.md](COMMANDS.md)
- **實現總結**: [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)
- **Dashboard 開發**: [dashboard/README.md](dashboard/README.md)

---

**提示**: 所有命令都使用 `uv run` 開頭，會自動管理虛擬環境。
