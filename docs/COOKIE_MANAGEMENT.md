# Cookie 管理指南

本文檔說明 aniGamerPlus 的 Cookie 管理機制和正確的使用方式。

## 📋 目錄

- [問題背景](#問題背景)
- [新的 Cookie 管理架構](#新的-cookie-管理架構)
- [使用方式](#使用方式)
- [Cookie 刷新機制](#cookie-刷新機制)
- [常見問題](#常見問題)

---

## 問題背景

### 原有實現的問題

原本的 `renew_cookies()` 函數只是簡單地將傳入的 cookie 字典轉換為字串並保存到配置文件：

```python
# 舊的實現（有問題）
def renew_cookies(new_cookie, log=True):
    cookie = None
    new_cookie_str = ""
    for key, value in new_cookie.items():
        new_cookie_str = new_cookie_str + key + "=" + value + "; "
    new_cookie_str = new_cookie_str[0:-2]

    # 直接保存到配置，沒有刷新
    cfg.cookie = new_cookie_str
    save_config(cfg)
```

**問題**:
1. ❌ 沒有實際向動畫瘋發送請求獲取新的 cookie
2. ❌ 只是保存了從 HTTP 回應中提取的 cookie
3. ❌ 無法確保 cookie 的有效性
4. ❌ 缺少 cookie 驗證機制

### 正確的 Cookie 刷新流程

```
現有 Cookie → 發送請求到動畫瘋 → 服務器返回 Set-Cookie →
獲取新 Cookie → 驗證有效性→ 保存到配置
```

---

## 新的 Cookie 管理架構

### CookieManager 類別

```python
from cookie_manager import CookieManager

# 初始化
cfg = get_config()
manager = CookieManager(cfg)

# 載入 cookie
cookies = manager.load_cookies()

# 刷新 cookie（真正向動畫瘋發送請求）
new_cookies = manager.refresh_cookies(cookies)

# 保存 cookie
manager.save_cookies(new_cookies)

# 驗證 cookie
is_valid = manager.validate_cookies(cookies)

# 檢查是否為 VIP
is_vip = manager.is_vip_cookie(cookies)
```

### AutoCookieRefresher 類別

自動定期刷新 cookie：

```python
from cookie_manager import CookieManager, AutoCookieRefresher

manager = CookieManager(cfg)
refresher = AutoCookieRefresher(
    manager,
    refresh_interval=3600  # 每小時刷新
)

# 在下載循環中使用
current_cookies = manager.load_cookies()
cookies = refresher.refresh_if_needed(current_cookies)
```

---

## 使用方式

### 1. 基本使用

```python
import config
from cookie_manager import CookieManager

# 獲取配置
cfg = config.get_config()

# 創建 Cookie 管理器
manager = CookieManager(cfg)

# 載入現有 cookie
cookies = manager.load_cookies()

if not cookies:
    print("未設置 Cookie，請在 config.toml 中配置")
else:
    print(f"已載入 Cookie: {manager.get_cookie_info()}")
```

### 2. 刷新 Cookie

```python
# 當檢測到 cookie 失效時刷新
if cookie_expired:
    current_cookies = config.read_cookie()

    # 刷新 cookie（向動畫瘋發送請求）
    manager = CookieManager(cfg)
    new_cookies = manager.refresh_cookies(current_cookies)

    # 保存新 cookie
    manager.save_cookies(new_cookies)

    print("Cookie 已刷新並保存")
```

### 3. 在下載流程中使用

```python
from http_client import HttpClient
from cookie_manager import CookieManager

# 初始化
cfg = config.get_config()
cookie_manager = CookieManager(cfg)

# 載入 cookie
cookies = cookie_manager.load_cookies()

# 創建 HTTP 客戶端
http_client = HttpClient(sn, cfg)
http_client.set_cookies(cookies)

# 發送請求
response = http_client.request(url)

# HTTP 客戶端會自動處理 cookie 更新
# 如果收到 Set-Cookie，會自動調用 config.renew_cookies()
```

### 4. 自動刷新（推薦）

```python
from cookie_manager import CookieManager, AutoCookieRefresher

# 設置自動刷新器
manager = CookieManager(cfg)
refresher = AutoCookieRefresher(
    manager,
    refresh_interval=3600  # 每小時檢查並刷新
)

# 在主循環中
while True:
    current_cookies = manager.load_cookies()

    # 如果需要，自動刷新
    cookies = refresher.refresh_if_needed(current_cookies)

    # 使用 cookies 進行下載
    download_with_cookies(cookies)

    time.sleep(300)  # 每 5 分鐘檢查一次
```

---

## Cookie 刷新機制

### 刷新流程詳解

```python
def refresh_cookies(self, current_cookies: dict[str, str]) -> dict[str, str]:
    """
    1. 使用當前 cookie 創建 HTTP 客戶端
    2. 向動畫瘋首頁發送 GET 請求
    3. 檢查回應的 Set-Cookie header
    4. 提取新的 cookie
    5. 驗證 cookie 有效性
    6. 返回刷新後的 cookie
    """
```

### 刷新時機

建議在以下情況刷新 cookie：

1. **收到 Cookie 過期錯誤**
   ```python
   if "cookie expired" in error_message:
       manager.refresh_cookies(current_cookies)
   ```

2. **定期刷新（推薦）**
   ```python
   # 使用 AutoCookieRefresher
   refresher.refresh_if_needed(current_cookies)
   ```

3. **檢測到 Set-Cookie header**
   ```python
   # HttpClient 會自動處理
   # 無需手動調用
   ```

4. **用戶手動觸發**
   ```python
   # Web 控制台提供刷新按鈕
   if user_clicked_refresh:
       manager.refresh_cookies(current_cookies)
   ```

---

## 常見問題

### Q1: Cookie 刷新失敗怎麼辦？

**A**: Cookie 刷新可能失敗的原因：

1. **網絡問題**: 檢查網絡連線
2. **Cookie 已失效**: 需要重新登入獲取新 cookie
3. **IP 被限制**: 動畫瘋可能限制頻繁請求

解決方法：
```python
try:
    new_cookies = manager.refresh_cookies(current_cookies)
    if not manager.validate_cookies(new_cookies):
        print("Cookie 刷新失敗，請重新登入")
except Exception as e:
    print(f"刷新異常: {e}")
```

### Q2: 如何判斷 Cookie 是否需要刷新？

**A**: 可以通過以下方式：

```python
# 方法 1: 檢查上次刷新時間
if (time.time() - last_refresh) > 3600:  # 超過 1 小時
    refresh_cookies()

# 方法 2: 發送測試請求
try:
    response = http_client.request(test_url)
    if response.status_code == 401:  # 未授權
        refresh_cookies()
except:
    refresh_cookies()

# 方法 3: 使用 AutoCookieRefresher（推薦）
refresher.refresh_if_needed(cookies)
```

### Q3: Cookie 存儲在哪裡？

**A**: Cookie 存儲在 `config.toml` 中：

```toml
# config.toml
cookie = "BAHAID=xxx; BAHARUNE=yyy; ..."
```

刷新後會自動更新此文件。

### Q4: 如何獲取初始 Cookie？

**A**:

1. **瀏覽器手動獲取**:
   - 登入動畫瘋
   - 按 F12 開啟開發者工具
   - 前往 Network 標籤
   - 刷新頁面
   - 找到請求的 Cookie header
   - 複製到 `config.toml`

2. **使用登入 API**（未實作）:
   ```python
   # 未來可以實作自動登入
   manager.login(username, password)
   ```

### Q5: VIP 和非 VIP Cookie 有什麼區別？

**A**:

```python
# VIP Cookie 包含 BAHAID（已登入用戶）
vip_cookie = {
    "BAHAID": "xxx",
    "BAHARUNE": "yyy",
    # ... 其他欄位
}

# 非 VIP Cookie（遊客）
guest_cookie = {
    "nologinuser": "xxx",
    # ... 其他欄位
}

# 檢查
is_vip = manager.is_vip_cookie(cookies)
```

VIP Cookie 可以：
- 跳過廣告
- 觀看 VIP 限定內容
- 更高的下載優先級

### Q6: 多個下載任務如何共享 Cookie？

**A**: 使用全域 Cookie 管理：

```python
# 方法 1: 使用 config.read_cookie()（原有方式）
cookies = config.read_cookie()

# 方法 2: 使用共享 CookieManager 實例
global_manager = CookieManager(cfg)
cookies = global_manager.load_cookies()

# 所有 HttpClient 使用相同的 cookies
client1.set_cookies(cookies)
client2.set_cookies(cookies)
```

---

## 最佳實踐

### 1. 定期自動刷新

```python
from cookie_manager import CookieManager, AutoCookieRefresher

manager = CookieManager(cfg)
refresher = AutoCookieRefresher(manager, refresh_interval=3600)

# 在主循環開始時刷新
cookies = refresher.refresh_if_needed(manager.load_cookies())
```

### 2. 錯誤處理

```python
try:
    cookies = manager.refresh_cookies(current_cookies)
    if not manager.validate_cookies(cookies):
        # Cookie 無效，使用遊客模式
        cookies = {}
except Exception as e:
    logger.error(f"Cookie 刷新失敗: {e}")
    # 回退到原有 cookie
    cookies = current_cookies
```

### 3. 日誌記錄

```python
# 記錄 cookie 刷新事件
err_print(
    0,
    "Cookie 管理",
    f"Cookie 刷新成功，類型: {'VIP' if manager.is_vip_cookie(cookies) else '一般用戶'}",
    status=2,
    no_sn=True,
)
```

### 4. 測試環境

```python
# 使用測試 cookie
test_cookies = {
    "test": "cookie"
}
manager = CookieManager(cfg)
manager.save_cookies(test_cookies)
```

---

## 遷移指南

### 從舊版本遷移

如果您使用的是舊版本的 cookie 管理：

1. **更新配置格式**（自動完成）
   ```toml
   # 舊格式（JSON）已自動遷移到
   # 新格式（TOML）
   ```

2. **更新程式碼**
   ```python
   # 舊方式
   cookies = config.read_cookie()
   config.renew_cookies(new_cookies)

   # 新方式（推薦）
   from cookie_manager import CookieManager
   manager = CookieManager(cfg)
   cookies = manager.load_cookies()
   new_cookies = manager.refresh_cookies(cookies)
   manager.save_cookies(new_cookies)
   ```

3. **兼容性**: 舊的 `config.read_cookie()` 和 `config.renew_cookies()` 仍然可用，但內部已使用新的 `CookieManager`

---

**最後更新**: 2025-01-XX
**相關文檔**: [REFACTORING_SUMMARY.md](../REFACTORING_SUMMARY.md)
