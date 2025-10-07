# 目錄重構完成總結

## 新的目錄結構

```
根目錄/
├── pyproject.toml          # Python 專案配置
├── package.json            # 前端專案配置
├── package-lock.json       # npm 依賴鎖定
├── Dockerfile              # Docker 配置
├── docker-compose.yml      # Docker Compose 配置
├── config-sample.toml      # 配置範例
├── README.md               # 專案說明
├── node_modules/           # npm 依賴
├── dist/                   # 前端編譯輸出
│   ├── *.js                # 編譯後的 JavaScript
│   ├── assets/             # 字體、圖片等資源
│   └── .vite/              # Vite manifest
├── src/
│   ├── frontend/           # 前端源碼
│   │   ├── src/            # JavaScript 源碼
│   │   │   ├── main.js
│   │   │   ├── login.js
│   │   │   ├── components/
│   │   │   ├── utils/
│   │   │   └── styles/
│   │   ├── templates/      # HTML 模板
│   │   │   ├── app_main.html
│   │   │   ├── login.html
│   │   │   └── partials/
│   │   │       ├── settings_tailwind.html
│   │   │       └── snlist.html
│   │   ├── static/         # 靜態資源
│   │   │   ├── layui/
│   │   │   ├── webfonts/
│   │   │   ├── img/
│   │   │   └── js/settings_id_list.js
│   │   ├── vite.config.js
│   │   ├── tailwind.config.js
│   │   └── postcss.config.js
│   └── backend/            # 後端源碼
│       ├── __init__.py
│       ├── app.py          # 主程式入口
│       ├── dashboard_server.py  # Web 控制台
│       ├── anime.py
│       ├── config.py
│       └── [其他 Python 模組]
└── scripts/
    ├── __init__.py
    └── build_dashboard.py  # 前端構建腳本
```

## 主要變更

### 1. 前後端完全分離
- **前端**: `src/frontend/` - 所有前端相關文件
- **後端**: `src/backend/` - 所有 Python 後端代碼

### 2. 前端改動
- ✅ 將 `src/dashboard/` 重命名並移至 `src/frontend/`
- ✅ 模板重命名：
  - `app_main_new.html` → `app_main.html`
  - `login_new.html` → `login.html`
- ✅ 新增 `partials/snlist.html` 模板（從後端遷移）
- ✅ 移除未使用的文件：
  - `static/js/aniGamerPlus.js` (舊版，已被 Vite 構建替代)
  - `static/js/monitor.js` (舊版，已被 Vite 構建替代)
  - `static/js/tailwind-components.js` (舊版，已被 Vite 構建替代)
  - `static/dist/` (舊的構建產物)
  - `static_src/` (已無用)

### 3. 後端改動
- ✅ 所有 `.py` 文件移至 `src/backend/`
- ✅ 修改路徑配置：
  - `TEMPLATE_PATH`: `src/frontend/templates/`
  - `STATIC_PATH`: `src/frontend/static/`
  - `DIST_PATH`: `dist/`
- ✅ `/sn_list` 端點改用 Jinja2 模板渲染（不再使用 f-string 拼接 HTML）
- ✅ 更新 `vite_manifest.py` 的 dist 路徑

### 4. 配置文件更新
- **pyproject.toml**:
  - `entry_point`: `src.backend.app:main`
  - `packages`: `["src/backend"]`
- **package.json**:
  - 所有命令前加上 `cd src/frontend &&`
- **vite.config.js**:
  - `outDir`: `../../dist` (相對於 src/frontend)
  - `publicDir`: `../static/img`
- **Dockerfile**:
  - `ENTRYPOINT`: `python3 -u -m src.backend.ani_gamer_next`
- **scripts/build_dashboard.py**:
  - `frontend_dir`: `root_dir / "src" / "frontend"`
  - `dist_dir`: `root_dir / "dist"`

### 5. 已刪除的目錄
- ❌ `src/dashboard/` (已移至 `src/frontend/`)
- ❌ `dashboard/` (舊的構建輸出目錄)
- ❌ 根目錄的所有 `.py` 文件 (已移至 `src/backend/`)

## 如何使用

### 前端開發
```bash
# 安裝依賴（首次）
npm install

# 開發模式（熱更新）
npm run dev

# 生產構建
npm run build

# 預覽構建結果
npm run preview
```

### 後端開發
```bash
# 安裝 Python 依賴
uv pip install -r pyproject.toml

# 運行主程式
python -m src.backend.ani_gamer_next

# 運行 Dashboard 伺服器
python -m src.backend.dashboard_server
```

### 完整構建流程
```bash
# 1. 構建前端
npm run build

# 2. 運行後端
python -m src.backend.dashboard_server
```

或使用 uv:
```bash
uv run build-dashboard
uv run ani-gamer-next
```

## 測試狀態
- ✅ 前端構建成功
- ✅ dist 輸出到根目錄
- ⏳ 後端運行測試（需要安裝依賴）
- ⏳ Docker 構建測試

## 注意事項
1. `node_modules` 位於根目錄
2. 前端構建輸出 `dist/` 位於根目錄
3. 所有 Python import 路徑已更新為使用 `src.backend` 前綴（通過 pyproject.toml 的 packages 配置）
