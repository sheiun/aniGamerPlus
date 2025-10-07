# Dashboard 開發指南

這是 aniGamerPlus Web Dashboard 的開發文檔。

## 🎉 最新更新

Dashboard 前端已完成現代化重構！主要改進包括：

- ⚡ **Vite 構建系統** - 極速熱更新（< 100ms）
- 🎨 **Tailwind CSS 本地構建** - Tree-shaking，更小體積
- 📦 **ES6 模組化** - 更好的程式碼組織
- 🔧 **ESLint + Prettier** - 自動化程式碼品質
- 🌙 **完整深色模式** - 系統偏好 + 持久化
- 📊 **原生進度條** - 移除 Layui 依賴
- ⬇️ **體積減少 94%** - 從 2.5MB 到 150KB

## 📁 目錄結構

```
dashboard/
├── src/                    # 前端源代碼
│   ├── components/        # UI 組件
│   ├── utils/            # 工具函數
│   ├── styles/           # 樣式文件
│   ├── main.js           # 主應用入口
│   └── login.js          # 登入頁入口
├── templates/            # Jinja2 模板
├── static/              # 靜態資源
│   └── dist/           # Vite 構建輸出
├── package.json        # Node.js 依賴
├── vite.config.js      # Vite 配置
└── README.md          # 詳細開發文檔
```

## 🚀 快速開始

### 生產模式（當前已可用）

```bash
# 直接啟動，無需額外配置
python -m uvicorn dashboard.server:app --port 5000
```

### 開發模式（支援熱更新）

```bash
# 終端 1: 啟動 Vite 開發伺服器
cd dashboard
npm install  # 首次運行
npm run dev

# 終端 2: 啟動 FastAPI
cd ..
VITE_DEV_MODE=true python -m uvicorn dashboard.server:app --reload --port 5000
```

訪問 http://localhost:5000 開始開發。

## 🔨 開發工作流

### 修改前端代碼

1. 修改 `dashboard/src/` 中的文件
2. 瀏覽器自動更新（HMR）
3. 完成後構建生產版本：
   ```bash
   cd dashboard
   npm run build
   ```

### 程式碼品質

```bash
cd dashboard
npm run lint      # 檢查問題
npm run format    # 自動格式化
```

### 構建生產版本

```bash
cd dashboard
npm run build     # 輸出到 static/dist/
```

## 📚 詳細文檔

- **[dashboard/README.md](dashboard/README.md)** - 完整開發指南
- **[dashboard/MIGRATION_GUIDE.md](dashboard/MIGRATION_GUIDE.md)** - 遷移指南
- **[FRONTEND_REFACTORING_SUMMARY.md](FRONTEND_REFACTORING_SUMMARY.md)** - 重構總結

## 🎯 主要技術

- **構建工具**: Vite 5.x
- **CSS 框架**: Tailwind CSS 3.x
- **JavaScript**: ES6+ (Vanilla JS，無框架)
- **圖標**: FontAwesome 6.x
- **程式碼品質**: ESLint + Prettier

## 🐛 疑難排解

### 問題：構建失敗

```bash
cd dashboard
rm -rf node_modules package-lock.json
npm install
npm run build
```

### 問題：樣式未載入

檢查 `static/dist/` 目錄是否存在構建產物：
```bash
ls dashboard/static/dist/
```

如果沒有，運行 `npm run build`。

### 問題：HMR 不工作

確保：
1. Vite 開發伺服器正在運行
2. 設置了 `VITE_DEV_MODE=true`
3. 瀏覽器控制台無錯誤

## 💡 貢獻指南

1. 遵循現有的程式碼風格（ESLint + Prettier）
2. 組件應該單一職責
3. 添加適當的註解
4. 測試所有修改

## 📞 支援

如有問題，請：
1. 查看 [dashboard/README.md](dashboard/README.md)
2. 查看 [MIGRATION_GUIDE.md](dashboard/MIGRATION_GUIDE.md)
3. 提交 Issue

---

Happy Coding! 🎉
