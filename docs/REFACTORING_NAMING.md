# Python 命名規範重構總結

## 檔案名稱重構

根據 PEP 8 Python 命名規範，所有模組名稱（檔案名）應使用小寫加底線格式：

### 重命名對照表

| 原檔名 | 新檔名 | 說明 |
|--------|--------|------|
| `aniGamerPlus.py` | `ani_gamer_next.py` | 主程式入口 |
| `Anime.py` | `anime.py` | 動畫下載核心模組 |
| `Config.py` | `config.py` | 配置管理模組 |
| `ColorPrint.py` | `color_print.py` | 彩色終端輸出模組 |
| `Danmu.py` | `danmu.py` | 彈幕下載模組 |
| `Dashboard/Server.py` | `Dashboard/server.py` | Web 控制台服務器 |

## 導入語句更新

所有 Python 檔案中的導入語句已更新：

```python
# 舊寫法
import Config
from Anime import Anime
from ColorPrint import err_print
from Danmu import Danmu

# 新寫法
import config
from anime import Anime
from color_print import err_print
from danmu import Danmu
```

## 模組引用更新

所有程式碼中的模組引用已更新為小寫：

```python
# 舊寫法
Config.read_settings()
Config.write_settings()

# 新寫法
config.read_settings()
config.write_settings()
```

## Python 命名規範摘要（PEP 8）

### 檔案和模組名稱
- ✅ 使用小寫字母
- ✅ 單詞間使用底線分隔
- ✅ 範例：`my_module.py`, `config.py`, `color_print.py`

### 類別名稱
- ✅ 使用 CapWords（駝峰式）
- ✅ 範例：`Anime`, `Danmu`, `WebSocketTokenManager`

### 函式和方法名稱
- ✅ 使用小寫字母
- ✅ 單詞間使用底線分隔
- ✅ 範例：`read_settings()`, `download_chunk()`

### 常數名稱
- ✅ 使用大寫字母
- ✅ 單詞間使用底線分隔
- ✅ 範例：`MAX_RETRY`, `DEFAULT_TIMEOUT`

### 私有方法/屬性
- ✅ 以單底線開頭
- ✅ 範例：`_private_method()`, `_internal_data`

## 配置檔案更新

### pyproject.toml
```toml
[project]
name = "ani-gamer-next"

[project.scripts]
ani-gamer-next = "ani_gamer_next:main"
```

### Dockerfile
```dockerfile
ENTRYPOINT [ "python3", "-u", "ani_gamer_next.py" ]
```

### README.md
所有文件中的程式名稱引用已更新為 `ani_gamer_next.py`

## 使用方式

### 執行程式
```bash
# 使用 uv
uv run python ani_gamer_next.py

# 使用傳統方式
python3 ani_gamer_next.py
```

### 導入模組
```python
# 在其他 Python 檔案中使用
from anime import Anime
import config
from color_print import err_print
```

## 驗證

所有模組已通過導入測試：
```bash
✓ anime 模組導入成功
✓ config 模組導入成功  
✓ color_print 模組導入成功
✓ danmu 模組導入成功
✓ Dashboard.server 模組導入成功
```

## 相容性說明

- ✅ 所有內部導入已更新
- ✅ 所有外部引用（README、Dockerfile）已更新
- ✅ pyproject.toml 配置已更新
- ✅ 程式功能完全保持不變

## 後續維護建議

1. **新增模組時**：使用小寫加底線命名，如 `new_module.py`
2. **新增類別時**：使用駝峰式命名，如 `MyNewClass`
3. **新增函式時**：使用小寫加底線命名，如 `my_new_function()`
4. **使用 ruff 檢查**：`uv run ruff check .` 確保符合規範
5. **使用 ruff 格式化**：`uv run ruff format .` 自動格式化程式碼

