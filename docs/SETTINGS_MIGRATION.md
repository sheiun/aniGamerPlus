# Settings Migration 指南

## 概述

我們已將配置系統從字典遷移到類型安全的 `Settings` dataclass，與 `Config` dataclass 保持一致的設計風格。

## 檔案結構

### 新增檔案
- `schema.py` - 整合了 `Config` 和 `Settings` 的 dataclass 定義

### 刪除檔案
- `config_schema.py` - 已整合到 `schema.py`

## 主要變更

### 1. 新的 Settings Dataclass

在 `schema.py` 中定義了 `Settings` dataclass：

```python
from schema import Settings

# Settings 包含所有運行時處理過的配置
# - 處理過的目錄路徑（絕對路徑）
# - 運行時計算的值（如 use_gost）
# - 版本資訊
```

### 2. 新的 API

#### `config.get_settings() -> Settings`
**推薦使用** - 返回類型安全的 Settings 對象

```python
import config

# 新方式（推薦）
settings = config.get_settings()
bangumi_dir = settings.bangumi_dir  # 類型安全
use_gost = settings.use_gost  # IDE 自動完成

# 舊方式（仍然支持，但不推薦）
settings = config.read_settings()
bangumi_dir = settings["bangumi_dir"]  # 無類型檢查
```

#### `config.invalidate_settings_cache()`
清除 Settings 緩存，用於配置更新後重新加載

```python
# 更新配置後
config.write_settings(new_settings)
config.invalidate_settings_cache()  # 清除緩存
settings = config.get_settings()  # 獲取新的設置
```

### 3. 遷移的文件

#### `anime.py`
```python
# 之前
self._settings = config.read_settings()
self._bangumi_dir = self._settings["bangumi_dir"]

# 之後
self._settings = config.get_settings()
self._bangumi_dir = self._settings.bangumi_dir
```

#### `ani_gamer_next.py`
```python
# 之前
settings = config.read_settings()
version = settings["aniGamerPlus_version"]
if settings["use_gost"]:
    # ...

# 之後
settings = config.get_settings()
version = settings.aniGamerPlus_version
if settings.use_gost:
    # ...
```

## 遷移指南

### 對於新代碼
使用 `config.get_settings()` 獲取 Settings 對象：

```python
import config

settings = config.get_settings()

# 訪問屬性
bangumi_dir = settings.bangumi_dir
use_proxy = settings.use_proxy
danmu = settings.danmu
```

### 對於現有代碼
1. 將 `config.read_settings()` 改為 `config.get_settings()`
2. 將字典訪問 `settings["key"]` 改為屬性訪問 `settings.key`
3. 享受類型檢查和 IDE 自動完成的好處！

### 向後兼容
`config.read_settings()` 仍然保留並正常工作，返回字典格式。
這確保了：
- 現有代碼不會立即中斷
- 可以逐步遷移
- Web dashboard 等使用字典的部分仍能工作

## Settings vs Config 的區別

| 特性 | Config | Settings |
|------|--------|----------|
| 來源 | 直接從 TOML 讀取 | 從 Config 處理後生成 |
| 目錄路徑 | 原始值（可能為空） | 處理過的絕對路徑 |
| 運行時值 | 無 | 包含（如 use_gost） |
| 版本資訊 | 基本版本號 | 包含 aniGamerPlus_version |
| 使用場景 | 配置讀寫 | 運行時使用 |

## 類型安全的好處

### 1. 編譯時錯誤檢查
```python
# 拼寫錯誤會被 IDE 和類型檢查器捕獲
settings.bangumi_dr  # ❌ 屬性錯誤
settings.bangumi_dir  # ✅ 正確
```

### 2. IDE 自動完成
輸入 `settings.` 後，IDE 會顯示所有可用屬性

### 3. 重構安全
重命名屬性時，IDE 可以自動更新所有引用

### 4. 文檔化
Settings dataclass 本身就是最好的文檔，清楚列出所有可用屬性

## 測試

```bash
# 測試 Settings 導入
uv run python -c "from schema import Settings; print('✅ Settings import OK')"

# 測試獲取設置
uv run python -c "import config; s = config.get_settings(); print(f'bangumi_dir={s.bangumi_dir}')"

# 測試應用程序
uv run ani_gamer_next.py
```

## 未來計劃

- [ ] 完全遷移所有 `read_settings()` 使用到 `get_settings()`
- [ ] 考慮棄用 `read_settings()`，僅保留內部使用
- [ ] 為 Settings 添加驗證邏輯
- [ ] 添加更多類型提示

## 相關文檔

- `CONFIG_REFACTORING_SUMMARY.md` - Config 重構總結
- `CONFIG_MIGRATION.md` - Config 遷移指南
- `schema.py` - Settings 和 Config 的定義

