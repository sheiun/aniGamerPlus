# Dashboard SPA Migration 指南

## 概述

已將 aniGamerPlus dashboard 從多頁應用遷移到單頁應用（SPA），提供更流暢的用戶體驗。

## 主要變更

### 1. 新的頁面結構

#### **app.html** - 主要 SPA 頁面
整合了所有功能到一個單頁應用：
- **Tab 導航**：使用 Bootstrap tabs 在不同功能間切換
- **自動模式設定**：配置下載參數
- **任務監控中心**：即時監控下載任務
- **sn_list 管理**：管理訂閱列表
- **手動任務**：添加單次下載任務

#### **partials/settings.html** - 設定頁面部分
抽取的設定表單部分，通過 Jinja2 include 載入。

### 2. 路由變更

| 舊路由 | 新路由 | 說明 |
|--------|--------|------|
| `/` | `/` | 現在載入 `app.html` (SPA) |
| `/monitor` | `/#monitor` | 重定向到 SPA 的監控 tab |
| `/data/sn_list` | `/data/sn_list` | API endpoint (保持不變) |
| `/sn_list` (GET) | `/sn_list` | 返回 HTML 片段 |
| `/sn_list` (POST) | `/api/sn_list` | 更新 sn_list |

### 3. JavaScript 更新

#### **monitor.js**
添加了 SPA 支持：
```javascript
// 啟動監控
function startMonitoring() { ... }

// 停止監控
function stopMonitoring() { ... }
```

- **Tab 切換時自動管理 WebSocket 連接**
- 進入監控頁面時啟動，離開時停止
- 避免資源浪費和 WebSocket 泄漏

#### **app.html 腳本**
```javascript
// Tab 切換事件處理
$('a[data-toggle="tab"]').on('shown.bs.tab', function(e) {
    var target = $(e.target).attr("href");
    if (target === '#monitor') {
        startMonitoring();  // 啟動監控
    } else {
        stopMonitoring();   // 停止監控
    }
});
```

### 4. 模態框整合

所有模態框（Modal）都整合到主頁面：
- **手動任務模態框**
- **sn_list 編輯模態框**
- **上傳狀態模態框**

### 5. 樣式優化

```css
.nav-tabs .nav-link {
    color: #495057;
}
.nav-tabs .nav-link.active {
    color: #007bff;
    font-weight: bold;
}
.tab-content {
    padding-top: 20px;
}
```

## 使用方式

### 訪問 Dashboard

1. 啟動應用程序：`uv run ani_gamer_next.py`
2. 在瀏覽器中打開：`http://localhost:5000`
3. 使用配置的用戶名和密碼登入

### 功能切換

- **Tab 導航**：點擊頂部的 tab 切換功能
- **自動切換**：使用 URL 錨點（如 `/#monitor`）直接跳轉到特定 tab
- **模態框**：點擊對應的 tab 或按鈕打開模態框

## 優勢

### 1. 性能提升
- **無需頁面重新載入**：切換功能即時響應
- **智能資源管理**：只有在監控頁面時才啟動 WebSocket
- **減少服務器請求**：共享頁面資源

### 2. 用戶體驗改善
- **統一導航**：所有功能在同一頁面，無需記憶多個 URL
- **狀態保持**：切換 tab 時保持表單狀態
- **流暢動畫**：Bootstrap tab 過渡效果

### 3. 維護便利
- **模組化設計**：設定表單抽取為獨立部分
- **代碼復用**：共享樣式和腳本
- **易於擴展**：添加新 tab 只需要添加內容

## 技術細節

### Jinja2 Include
```html
{% include 'partials/settings.html' %}
```
允許模組化組織模板。

### WebSocket 生命週期管理
```javascript
let monitorWS = null;
let monitoringActive = false;

// 在 tab 切換時自動管理
```

### 錨點路由
使用 URL 錨點實現 SPA 內部路由：
- `/#settings` - 設定頁面
- `/#monitor` - 監控頁面

## 遷移檢查清單

- [x] 創建 `app.html` SPA 主頁面
- [x] 抽取 `partials/settings.html`
- [x] 更新路由到 SPA
- [x] 修改 `monitor.js` 支持啟動/停止
- [x] 添加 Tab 切換事件處理
- [x] 整合所有模態框
- [x] 更新 `sn_list` 路由
- [x] 測試所有功能

## 測試

### 功能測試
1. ✅ 登入/登出
2. ✅ Tab 切換（設定/監控/sn_list/手動任務）
3. ✅ 設定保存和載入
4. ✅ 監控任務即時更新
5. ✅ sn_list 編輯
6. ✅ 手動任務添加

### WebSocket 測試
1. ✅ 進入監控頁面時啟動 WebSocket
2. ✅ 離開監控頁面時關閉 WebSocket
3. ✅ 任務進度即時更新

## 向後兼容

- 舊的 `/monitor` 路由自動重定向到 `/#monitor`
- API endpoints 保持不變
- 可以選擇性保留 `index.html` 和 `monitor.html` 作為備份

## 未來改進

- [ ] 使用 Vue.js 或 React 重寫（可選）
- [ ] 添加更多動畫效果
- [ ] 實現離線支持（PWA）
- [ ] 添加暗黑模式
- [ ] 使用 SPA 路由庫（如 page.js）

## 相關文件

- `dashboard/templates/app.html` - SPA 主頁面
- `dashboard/templates/partials/settings.html` - 設定部分
- `dashboard/static/js/monitor.js` - 監控邏輯
- `dashboard/static/js/aniGamerPlus.js` - 主要邏輯
- `dashboard/server.py` - 後端路由

