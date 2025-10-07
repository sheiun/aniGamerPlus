# Cookie 整合到 Config 文檔

## 概述

Cookie 配置已從獨立的 `cookie.txt` 文件整合到 `config.toml` 配置文件中，提供更統一的配置管理。

## 變更內容

### 1. Schema 更新

#### `schema.py`
```python
@dataclass
class Config:
    # 網絡配置
    ua: str = "..."
    cookie: str = ""  # ✅ 新增：動畫瘋 Cookie
    use_proxy: bool = False
    proxy: str = "..."
    ...
```

### 2. 配置文件

#### `config.toml`
```toml
# 網絡配置
ua = "Mozilla/5.0 ..."
cookie = "ANIME_SIGN=xxx; nologinuser=yyy"  # ✅ 新增
use_proxy = false
proxy = "..."
```

**Cookie 格式：**
```
key1=value1; key2=value2; key3=value3
```

### 3. 讀取邏輯

#### 新的 `read_cookie()` 函數
```python
def read_cookie(log=False) -> dict:
    """讀取 Cookie 配置。
    
    優先級：
    1. config.toml 中的 cookie 字段
    2. cookie.txt 文件（自動遷移）
    3. 返回空字典
    """
```

#### 讀取流程
```
┌─────────────────────┐
│ read_cookie() 調用  │
└──────────┬──────────┘
           │
           ├─ 1. 檢查內存緩存
           │   └─ 如果已讀取 → 返回
           │
           ├─ 2. 讀取 config.toml
           │   ├─ 如果有 cookie → 解析並返回 ✅
           │   └─ 如果沒有 → 繼續
           │
           ├─ 3. 檢查 cookie.txt
           │   ├─ 如果存在 → 遷移到 config.toml ✅
           │   │   ├─ 更新 config.toml
           │   │   ├─ 備份為 cookie.txt.bak
           │   │   └─ 返回 cookie
           │   └─ 如果不存在 → 繼續
           │
           └─ 4. 返回空字典 {}
```

## 自動遷移

### 遷移觸發條件
- `config.toml` 中 `cookie` 字段為空
- 存在 `cookie.txt` 文件

### 遷移過程
```bash
# 遷移前
cookie.txt  (內容: ANIME_SIGN=xxx; nologinuser=yyy)
config.toml (cookie = "")

# 遷移中
讀取 cookie.txt → 解析 → 寫入 config.toml

# 遷移後
cookie.txt.bak  (備份)
config.toml     (cookie = "ANIME_SIGN=xxx; nologinuser=yyy")
```

### 遷移日誌
```
2025-10-04 03:34:37 Cookie 遷移 已將 cookie.txt 遷移到 config.toml（備份：cookie.txt.bak）
```

## 向後兼容

### 完全兼容 ✅
1. **舊版 cookie.txt**
   - 自動檢測並遷移
   - 備份原文件為 `cookie.txt.bak`
   - 遷移失敗時繼續使用 `cookie.txt`

2. **舊版命名**
   - `cookies.txt` → 自動重命名為 `cookie.txt`
   - `cookie.txt.txt` → 自動重命名為 `cookie.txt`（防呆）

3. **現有代碼**
   - `config.read_cookie()` API 保持不變
   - 返回格式保持不變（dict）
   - 所有使用 cookie 的代碼無需修改

## 使用方式

### 方式 1：直接編輯 config.toml（推薦）✅

```toml
# config.toml
cookie = "ANIME_SIGN=your_anime_sign; nologinuser=your_nologinuser"
```

**優點：**
- 統一管理所有配置
- 便於版本控制
- 支持註釋
- 可以通過 Web Dashboard 管理

### 方式 2：使用 cookie.txt（向後兼容）

```bash
# cookie.txt
ANIME_SIGN=your_anime_sign; nologinuser=your_nologinuser
```

**特點：**
- 首次讀取時自動遷移到 `config.toml`
- 原文件備份為 `cookie.txt.bak`
- 適合從舊版本升級

### 方式 3：Web Dashboard（未來支持）

通過 Web 界面直接編輯 cookie 配置。

## Cookie 格式說明

### 標準格式
```
key1=value1; key2=value2; key3=value3
```

### 動畫瘋必需的 Cookie
```
ANIME_SIGN=xxxxx
nologinuser=xxxxx
```

### 獲取 Cookie 的方法

1. **瀏覽器開發者工具**
   ```
   F12 → Network → 找到動畫瘋請求 → Cookie 標籤
   ```

2. **瀏覽器擴展**
   - EditThisCookie
   - Cookie Editor

3. **從 cookie.txt 導入**
   - 放置 `cookie.txt` 到程序目錄
   - 運行程序自動遷移

## 代碼示例

### 讀取 Cookie
```python
import config

# 讀取 cookie
cookies = config.read_cookie()

# 檢查是否有 cookie
if cookies:
    print(f"找到 {len(cookies)} 個 cookie")
else:
    print("沒有 cookie")
```

### 更新 Cookie
```python
import config
from config_manager import load_config, save_config

# 載入配置
cfg = load_config()

# 更新 cookie
cfg.cookie = "ANIME_SIGN=new_value; nologinuser=new_value"

# 保存配置
save_config(cfg)

# 清除緩存以重新讀取
config.cookie = None
```

### 解析 Cookie
```python
# 內部使用
from config import __parse_cookie_string

cookie_str = "key1=value1; key2=value2"
cookie_dict = __parse_cookie_string(cookie_str)
# 返回: {'key1': 'value1', 'key2': 'value2'}
```

## 文件結構

### 配置文件
```
config.toml          # 主配置文件（包含 cookie）
cookie.txt.bak       # cookie.txt 的備份（遷移後）
```

### 舊文件（已棄用）
```
cookie.txt           # 舊版 cookie 文件（已遷移）
cookies.txt          # 更舊的命名（自動重命名）
cookie.txt.txt       # 錯誤命名（自動修正）
invalid_cookie.txt   # 失效的 cookie 備份
```

## 安全性考慮

### Cookie 敏感信息
Cookie 包含登入憑證，需要妥善保管：

1. **不要公開分享 `config.toml`**
   ```toml
   # 錯誤 ❌
   git add config.toml  # 包含 cookie！
   
   # 正確 ✅
   git add config-sample.toml  # 範例文件，不包含實際 cookie
   ```

2. **使用 .gitignore**
   ```
   config.toml
   cookie.txt
   cookie.txt.bak
   ```

3. **環境變數（可選）**
   ```bash
   export ANIGAMER_COOKIE="ANIME_SIGN=xxx; nologinuser=yyy"
   ```
   （需要額外實現環境變數讀取）

## 遷移檢查清單

### 自動遷移 ✅
- [x] 檢測 `cookie.txt` 存在
- [x] 讀取並解析 cookie
- [x] 寫入 `config.toml`
- [x] 備份原文件
- [x] 清理舊命名文件

### 用戶操作 ✅
- [x] 無需手動操作
- [x] 程序自動處理
- [x] 保留備份文件

## 故障排除

### 問題 1：Cookie 讀取失敗
```
未發現cookie（請在 config.toml 設置或使用 cookie.txt）
```

**解決方案：**
1. 檢查 `config.toml` 中 `cookie` 字段是否有值
2. 或者創建 `cookie.txt` 文件
3. 確保格式正確：`key1=value1; key2=value2`

### 問題 2：Cookie 解析失敗
```
解析cookie 解析失敗: ...
```

**解決方案：**
1. 檢查 cookie 格式
2. 確保使用 `;` 分隔不同的 cookie
3. 確保每個 cookie 都有 `=` 符號
4. 移除多餘的空格或換行

### 問題 3：Cookie 遷移失敗
```
Cookie 遷移 遷移失敗: ..., 將繼續使用 cookie.txt
```

**影響：**
- Cookie 仍然可用（從 cookie.txt 讀取）
- 但不會保存到 config.toml

**解決方案：**
1. 檢查 `config.toml` 文件權限
2. 手動複製 cookie 內容到 `config.toml`
3. 檢查磁盤空間

## 測試

### 測試腳本
```python
# test_cookie.py
import config

# 測試 1: 讀取 cookie
print("=== 測試 Cookie 讀取 ===")
cookies = config.read_cookie(log=True)
print(f"Cookie 數量: {len(cookies)}")
print(f"Cookie 鍵: {list(cookies.keys())}")

# 測試 2: 檢查 config
cfg = config.get_config()
if cfg.cookie:
    print(f"✅ Config 包含 cookie: {cfg.cookie[:50]}...")
else:
    print("❌ Config 沒有 cookie")

# 測試 3: 解析測試
test_str = "key1=value1; key2=value2"
result = config.__parse_cookie_string(test_str)
print(f"解析測試: {result}")
```

### 運行測試
```bash
uv run python test_cookie.py
```

## 效益

### 用戶體驗 ✅
1. **統一配置** - 所有設置在一個文件
2. **自動遷移** - 無需手動操作
3. **安全備份** - 自動保留舊文件

### 開發體驗 ✅
1. **代碼簡化** - 統一的配置管理
2. **類型安全** - Dataclass 提供類型檢查
3. **易於擴展** - 新增配置項更容易

### 維護性 ✅
1. **減少文件** - 不需要額外的 cookie.txt
2. **版本控制** - 配置更容易管理
3. **文檔化** - 所有配置在一處

## 未來改進

### 短期 📋
- [ ] Web Dashboard 支持編輯 cookie
- [ ] Cookie 有效性驗證
- [ ] Cookie 過期提醒

### 長期 🚀
- [ ] 環境變數支持
- [ ] 加密存儲 cookie
- [ ] 多帳號支持
- [ ] OAuth 登入支持

## 相關文件

- `schema.py` - Cookie 字段定義
- `config.py` - Cookie 讀取邏輯
- `config.toml` - Cookie 存儲
- `config_manager.py` - TOML 配置管理

## 總結

Cookie 整合到 config.toml 提供了：
- ✅ 統一的配置管理
- ✅ 自動向後兼容遷移
- ✅ 更好的用戶體驗
- ✅ 代碼維護性提升

所有現有功能保持不變，用戶無需手動操作，系統自動處理遷移過程。

