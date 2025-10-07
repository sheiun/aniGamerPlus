# Dashboard 目錄重構完成總結

## 重構目標

將 dashboard 相關原始碼移至 `src/dashboard/` 目錄下，構建產物輸出至 `dashboard/dist/`。

## 目錄結構

### 重構後的目錄結構

```
aniGamerPlus/
├── dashboard/                    # 僅存放構建產物
│   └── dist/                     # Vite 構建輸出
│       ├── .vite/
│       │   └── manifest.json
│       ├── assets/               # CSS, 字體等靜態資源
│       ├── chunks/               # JS 代碼分割
│       └── *.js                  # 入口文件
│
├── src/
│   └── dashboard/                # Dashboard 原始碼
│       ├── src/                  # 前端源碼
│       │   ├── components/       # React 組件
│       │   ├── utils/            # 工具函數
│       │   ├── styles/           # CSS 樣式
│       │   ├── main.js           # 主應用入口
│       │   └── login.js          # 登入頁入口
│       ├── templates/            # Jinja2 模板
│       ├── static/               # 開發用靜態資源
│       ├── package.json          # 前端依賴
│       ├── vite.config.js        # Vite 配置
│       ├── tailwind.config.js    # Tailwind 配置
│       └── server.py             # 舊版 server（保留參考）
│
├── dashboard_server.py           # Dashboard FastAPI 應用（新版）
├── vite_manifest.py              # Vite manifest 讀取工具
├── app.py                        # 統一入口
└── scripts/
    └── build_dashboard.py        # 構建腳本
```

## 核心文件變更

### 1. vite.config.js

**位置**: `src/dashboard/vite.config.js`

**關鍵配置**:
```javascript
export default defineConfig({
  root: 'src',
  build: {
    outDir: '../../../dashboard/dist',  // 輸出至項目根目錄的 dashboard/dist
    emptyOutDir: true,
    manifest: true,
  },
});
```

### 2. dashboard_server.py

**位置**: 項目根目錄

**路徑配置**:
```python
WORKING_DIR = Path(config.get_working_dir())
SRC_DASHBOARD = WORKING_DIR / "src" / "dashboard"
TEMPLATE_PATH = SRC_DASHBOARD / "templates"
DIST_PATH = WORKING_DIR / "dashboard" / "dist"

# 靜態文件掛載 - 優先使用 dist
if DIST_PATH.exists():
    app.mount("/static", StaticFiles(directory=str(DIST_PATH)), name="static")
else:
    src_static = SRC_DASHBOARD / "static"
    if src_static.exists():
        app.mount("/static", StaticFiles(directory=str(src_static)), name="static")
```

### 3. vite_manifest.py

**位置**: 項目根目錄

**路徑配置**:
```python
WORKING_DIR = Path(os.getcwd())
DIST_DIR = WORKING_DIR / "dashboard" / "dist"
MANIFEST_PATH = DIST_DIR / ".vite" / "manifest.json"
```

### 4. scripts/build_dashboard.py

**更新內容**:
- 構建目錄: `root_dir / "src" / "dashboard"`
- 輸出檢查: `root_dir / "dashboard" / "dist"`

### 5. app.py

**更新內容**:
- 導入改為: `from dashboard_server import app`
- dist 路徑: `root_dir / "dashboard" / "dist"`
- 開發模式提示: `cd src/dashboard && npm run dev`

## 構建流程

### 開發模式

```bash
# 1. 啟動 Vite 開發伺服器
cd src/dashboard
npm run dev

# 2. 啟動 FastAPI（開發模式）
uv run python app.py --dashboard --dev
```

### 生產模式

```bash
# 1. 構建前端
uv run build-dashboard

# 2. 啟動服務
uv run python app.py --dashboard
```

## 構建輸出

**位置**: `/home/sheildon/aniGamerPlus/dashboard/dist`

**大小**: 約 1.2 MB

**內容**:
- JavaScript 入口文件（main, login）
- JavaScript chunks（代碼分割）
- Legacy 版本（支援舊瀏覽器）
- CSS 樣式文件
- Font Awesome 字體檔案
- Vite manifest.json

## 優勢

1. **清晰的源碼/產物分離**
   - 源碼: `src/dashboard/`
   - 產物: `dashboard/dist/`

2. **簡化的構建流程**
   - 單一命令: `uv run build-dashboard`
   - 自動依賴檢查和安裝

3. **開發體驗提升**
   - Vite HMR 支援
   - 開發/生產模式分離

4. **部署友好**
   - `dashboard/dist/` 可獨立部署到 CDN
   - 構建產物不包含源碼

## 測試驗證

所有功能已測試通過:
- ✅ `uv run build-dashboard` 構建成功
- ✅ `uv run python app.py --dashboard` 啟動成功
- ✅ Vite manifest 正確讀取
- ✅ 靜態資源正確掛載
- ✅ 模板渲染正常

## 已知問題修復

### 1. app.py 下載器入口修復

**問題**: 原始 `ani_gamer_next.py` 沒有 `main()` 函數，代碼直接在 `if __name__ == "__main__":` 下執行

**解決方案**: 使用 `runpy.run_path()` 直接執行腳本
```python
import runpy
runpy.run_path("ani_gamer_next.py", run_name="__main__")
```

### 2. vite_manifest.py 路徑修復

**問題**: `get_asset_url()` 錯誤地在 entry_name 前添加 `src/` 前綴，但 vite.config.js 中 root 已設為 `src`，manifest 中的 key 已經是相對於 src 的路徑

**錯誤行為**:
```python
entry_key = f"src/{entry_name}"  # 錯誤：manifest 中沒有 "src/login.js" 這個 key
if entry_key not in self._manifest:
    raise KeyError(f"Entry {entry_key} not found in manifest")
```

**修復後**:
```python
# vite root 已設為 src，manifest keys 為: "login.js", "main.js"
if entry_name not in self._manifest:
    raise KeyError(f"Entry {entry_name} not found in manifest")
```

**開發模式 URL 修復**:
```python
# 修復前: f"{self.dev_server}/src/{entry_name}"  # http://localhost:5173/src/login.js
# 修復後: f"{self.dev_server}/{entry_name}"      # http://localhost:5173/login.js
```

### 3. ani_gamer_next.py 導入修復

**問題**: 舊的導入路徑 `from dashboard.server import run` 已失效

**修復**:
```python
# 修復前: from dashboard.server import run as dashboard
# 修復後: from dashboard_server import run as dashboard
```

### 4. CSS 文件載入修復

**問題**: Vite 構建後 CSS 被分割到 chunks 中，但模板沒有引入 CSS 文件

**解決方案**:
1. 在 `vite_manifest.py` 添加 `get_css_urls()` 方法，遞迴收集入口和 imports 的 CSS
2. 在 `dashboard_server.py` 將 `vite_css` 函數註冊到模板全局變量
3. 在模板中添加 CSS 引用：
```html
{% for css_url in vite_css('login.js') %}
<link rel="stylesheet" href="{{ css_url }}">
{% endfor %}
```

### 5. 靜態資源路徑修復

**問題**: favicon 等靜態資源未被 Vite 複製到 dist

**解決方案**:
1. 創建 `src/dashboard/static_src/` 目錄作為 Vite publicDir
2. 複製靜態資源（如 favicon）到 static_src
3. Vite 構建時會自動複製 publicDir 內容到 dist

### 6. Font Awesome 字體路徑修復

**問題**: Font Awesome 圖標無法顯示，字體文件 URL 路徑錯誤

**原因**: Vite 生成的 CSS 中字體 URL 為 `/assets/fa-*.woff2`，但靜態文件掛載在 `/static/` 下

**解決方案**: 在 `vite.config.js` 設置 `base: '/static/'`
```javascript
export default defineConfig({
  root: 'src',
  base: '/static/',  // 所有資源 URL 前綴
  // ...
});
```

**結果**: 字體 URL 正確生成為 `/static/assets/fa-*.woff2`

## 遷移完成日期

2025-10-05

## 後續建議

1. 考慮將 `ani_gamer_next.py` 重構為模組化結構，提取 `main()` 函數
2. 將 `dashboard_server.py` 整合到 `src/dashboard/` 目錄
3. 考慮將靜態資源（sslkey, static_src）也移至 `src/dashboard/`
4. 添加自動化測試確保構建和運行的穩定性
