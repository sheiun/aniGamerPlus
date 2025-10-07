# 配置系統遷移說明

## 概述

aniGamerPlus 的配置系統已從 JSON 格式遷移到 TOML 格式，並使用 dataclass 進行類型規範。

## 主要改進

### 1. 使用 TOML 格式
- **更易讀**：TOML 格式更簡潔，支持註釋
- **更直觀**：層級結構更清晰
- **標準化**：符合 Python 生態系統的最佳實踐

### 2. 使用 dataclass 規範
- **類型安全**：使用 Python 類型提示
- **自動驗證**：dataclass 提供基本的類型檢查
- **IDE 支持**：更好的代碼補全和類型提示

### 3. 自動遷移
- 程序會自動檢測舊的 `config.json` 文件
- 自動遷移到新的 `config.toml` 格式
- 舊配置會備份為 `config.json.bak`

## 文件結構

```
config_schema.py      - 配置結構定義（dataclass）
config_manager.py     - 配置管理器（讀取/寫入 TOML）
config.py            - 主配置模組（保持向後兼容）
config.toml          - TOML 格式配置文件
config-sample.toml   - TOML 格式示例配置
```

## 配置結構

### 主配置類 (Config)
```python
@dataclass
class Config:
    # 目錄配置
    bangumi_dir: str
    temp_dir: str
    classify_bangumi: bool
    
    # 下載配置
    download_resolution: str
    multi_thread: int
    
    # 嵌套配置
    ftp: FTPConfig
    dashboard: DashboardConfig
    coolq_settings: CoolQSettings
    
    # ... 更多字段
```

### 嵌套配置

#### FTPConfig
```python
@dataclass
class FTPConfig:
    server: str
    port: int
    user: str
    pwd: str
    tls: bool
    # ...
```

#### DashboardConfig
```python
@dataclass
class DashboardConfig:
    host: str
    port: int
    SSL: bool
    BasicAuth: bool
    username: str
    password: str
```

## 使用方式

### 讀取配置

```python
from config_manager import load_config

config = load_config()
print(config.download_resolution)  # 類型安全的訪問
print(config.ftp.server)           # 嵌套配置
```

### 保存配置

```python
from config_manager import save_config

config.download_resolution = "720"
save_config(config)
```

### 向後兼容

現有代碼仍然可以使用原來的方式：

```python
import config

settings = config.read_settings()
print(settings["download_resolution"])  # 仍然返回字典
```

## 配置文件示例

### TOML 格式
```toml
# 下載配置
download_resolution = "1080"
multi_thread = 1
danmu = false

# FTP 配置
[ftp]
server = ""
port = 0
tls = true

# Dashboard 配置
[dashboard]
host = "127.0.0.1"
port = 5000
SSL = false
```

## 字段名稱變更

為了符合 Python 命名規範，部分字段名稱已更改：

| 舊名稱 (JSON)    | 新名稱 (TOML)   |
|------------------|-----------------|
| `multi-thread`   | `multi_thread`  |

配置管理器會自動處理這些映射，確保向後兼容。

## 依賴項

新增以下依賴：

```toml
[project]
requires-python = ">=3.12"

[project.dependencies]
tomli-w = ">=1.0.0"      # TOML 寫入
```

**注意**: 本項目要求 Python 3.12+，使用內建的 `tomllib` 讀取 TOML。

## 測試

運行測試腳本驗證配置系統：

```bash
uv run python test_config.py
```

測試內容：
- ✓ 配置載入
- ✓ 配置保存
- ✓ 配置驗證
- ✓ 嵌套配置訪問

## 遷移檢查清單

- [x] 創建 `config_schema.py` 定義配置結構
- [x] 創建 `config_manager.py` 管理 TOML 配置
- [x] 更新 `config.py` 整合新系統
- [x] 添加 TOML 依賴到 `pyproject.toml`
- [x] 創建 `config-sample.toml` 示例文件
- [x] 實現自動從 JSON 遷移
- [x] 保持向後兼容性
- [x] 創建測試腳本

## 注意事項

1. **自動備份**：舊的 `config.json` 會自動備份為 `config.json.bak`
2. **向後兼容**：現有代碼無需修改即可繼續工作
3. **類型安全**：建議新代碼使用 `load_config()` 獲得類型提示
4. **配置驗證**：dataclass 會在創建時進行基本的類型檢查

## 未來改進

- [ ] 添加更詳細的配置驗證（例如：範圍檢查）
- [ ] 支持配置文件熱重載
- [ ] 添加配置遷移工具命令行界面
- [ ] 支持環境變量覆蓋配置

