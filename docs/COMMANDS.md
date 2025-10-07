# 🚀 aniGamerPlus 命令速查

## 快速開始

```bash
# 1. 構建 Dashboard（首次使用）
uv run build-dashboard

# 2. 啟動 Dashboard
uv run app.py --dashboard

# 3. 運行下載器
uv run app.py
```

---

## 所有可用命令

### 📦 構建相關

```bash
# 構建 Dashboard 前端
uv run build-dashboard

# 或使用完整路徑
uv run python scripts/build_dashboard.py
```

### 🌐 Dashboard 相關

```bash
# 啟動 Dashboard（默認端口 5000）
uv run app.py --dashboard

# 自訂端口
uv run app.py --dashboard --port 8080

# 自訂監聽地址
uv run app.py --dashboard --host 127.0.0.1

# 開發模式（需先啟動 Vite: cd dashboard && npm run dev）
uv run app.py --dashboard --dev
```

### 📥 下載器相關

```bash
# 運行自動下載器
uv run app.py

# 或使用原始命令
uv run python ani_gamer_next.py

# 或使用安裝的命令
uv run ani-gamer-next
```

### 🔧 前端開發

```bash
cd dashboard

# 安裝依賴（首次）
npm install

# 開發模式（熱更新）
npm run dev

# 構建生產版本
npm run build

# 程式碼檢查
npm run lint

# 自動格式化
npm run format
```

---

## 📚 詳細文檔

- **完整使用指南**: [USAGE_GUIDE.md](USAGE_GUIDE.md)
- **Dashboard 開發**: [dashboard/README.md](dashboard/README.md)
- **快速參考**: [dashboard/QUICK_START.md](dashboard/QUICK_START.md)

---

## 💡 常見組合

```bash
# 首次使用完整流程
cp config-sample.toml config.toml  # 複製配置
vim config.toml                     # 編輯配置
uv run build-dashboard              # 構建前端
uv run app.py --dashboard           # 啟動 Dashboard

# 開發 Dashboard 前端
cd dashboard && npm run dev         # 終端 1
uv run app.py --dashboard --dev     # 終端 2

# 伺服器部署
uv run build-dashboard              # 構建
uv run app.py --dashboard --host 0.0.0.0  # 啟動
```
