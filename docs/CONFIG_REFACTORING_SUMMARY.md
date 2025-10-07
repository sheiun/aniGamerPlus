# 配置系統重構總結

## 完成的工作

### ✅ 1. 創建 TOML + DataClass 配置系統
- **`config_schema.py`**: 使用 dataclass 定義配置結構
  - `Config`: 主配置類別
  - `FTPConfig`: FTP 配置
  - `DashboardConfig`: Web 控制面板配置
  - `CoolQSettings`: CoolQ 推送設置
  
- **`config_manager.py`**: 配置管理器
  - 讀取和寫入 TOML 格式
  - 自動從 JSON 遷移到 TOML
  - 備份舊配置為 `config.json.bak`

### ✅ 2. 更新配置訪問方式
將所有 `settings["key"]` 改為 `cfg.key` 的對象訪問方式：

- **ani_gamer_next.py**: 40 處替換
  - 所有函數添加 `cfg = config.get_config()`
  - 使用類型安全的屬性訪問
  
- **anime.py**: 88 處替換
  - `Anime.__init__()` 添加 `self._cfg`
  - 所有配置訪問改為對象方式
  
- **color_print.py**: 1 處替換
  - 日誌配置訪問更新

### ✅ 3. 添加依賴
```toml
requires-python = ">=3.12"
dependencies = [
    "tomli-w>=1.0.0",  # TOML 寫入支持
]
```

**注意**: Python 3.12+ 內建 `tomllib`，無需額外依賴。

### ✅ 4. 保持向後兼容
- `config.read_settings()` 仍然可用，返回字典
- `config.get_config()` 返回 Config 對象
- 運行時屬性（如 `use_gost`）仍使用舊方式

### ✅ 5. 自動遷移
- 檢測 `config.json` 並自動轉換為 `config.toml`
- 備份舊配置
- 處理字段名映射（`multi-thread` → `multi_thread`）

## 配置文件變化

### 之前 (JSON)
```json
{
    "download_resolution": "1080",
    "multi-thread": 1,
    "danmu": false,
    "ftp": {
        "server": "",
        "port": 0
    }
}
```

### 之後 (TOML)
```toml
download_resolution = "1080"
multi_thread = 1
danmu = false

[ftp]
server = ""
port = 0
```

## 使用方式

### 新方式（推薦）
```python
import config

# 獲取配置對象
cfg = config.get_config()

# 類型安全的訪問
print(cfg.download_resolution)  # IDE 自動補全
print(cfg.multi_thread)
print(cfg.ftp.server)
print(cfg.dashboard.port)
```

### 舊方式（仍支持）
```python
import config

# 獲取配置字典
settings = config.read_settings()

# 字典訪問
print(settings["download_resolution"])
print(settings["multi_thread"])
```

## 優勢

1. **類型安全**: IDE 提供完整的類型提示和自動補全
2. **易讀配置**: TOML 格式更清晰，支持註釋
3. **結構化**: dataclass 提供清晰的配置結構
4. **自動遷移**: 無縫從 JSON 升級到 TOML
5. **向後兼容**: 現有代碼無需修改即可繼續工作

## 統計數據

- **總替換次數**: 129 處
  - ani_gamer_next.py: 40
  - anime.py: 88
  - color_print.py: 1
  
- **新增文件**: 3 個
  - config_schema.py
  - config_manager.py
  - config-sample.toml
  
- **新增依賴**: 1 個
  - tomli-w

## 遷移狀態

✅ **完成**
- [x] 創建配置結構定義
- [x] 創建配置管理器
- [x] 更新主要文件的配置訪問
- [x] 添加依賴
- [x] 自動 JSON → TOML 遷移
- [x] 創建示例配置文件
- [x] 保持向後兼容性
- [x] 測試通過

## 注意事項

1. **運行時屬性**: `use_gost`、`working_dir`、`aniGamerPlus_version` 等運行時計算的屬性仍使用 `settings` 字典

2. **配置文件位置**: 
   - 新: `config.toml`
   - 舊備份: `config.json.bak`
   - 示例: `config-sample.toml`

3. **Python 版本**: 
   - Python 3.11+: 使用內建 `tomllib`
   - Python < 3.11: 需要安裝 `tomli`

## 後續建議

- [ ] 逐步移除 `settings` 字典，完全使用 `cfg` 對象
- [ ] 添加配置驗證（範圍檢查、必填字段等）
- [ ] 支持環境變量覆蓋配置
- [ ] 添加配置熱重載功能

