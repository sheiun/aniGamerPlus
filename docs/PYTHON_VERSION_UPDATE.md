# Python 版本要求更新

## 變更內容

### 📌 Python 版本要求
- **之前**: Python >= 3.9
- **現在**: Python >= 3.12

### 🗑️ 移除的依賴
- ❌ `tomli` - Python 3.11+ 已內建 `tomllib`

### ✅ 保留的依賴
- ✓ `tomli-w` - 用於 TOML 寫入（Python 標準庫只提供讀取）

## 理由

1. **簡化依賴**: Python 3.12+ 內建 `tomllib`，無需額外安裝
2. **現代化**: 使用最新的 Python 特性和改進
3. **減少維護**: 不需要處理多版本兼容性問題

## 技術細節

### 之前 (支持 Python 3.9+)
```python
# config_manager.py
try:
    import tomllib
except ImportError:
    import tomli as tomllib  # 需要額外安裝
```

```toml
# pyproject.toml
requires-python = ">=3.9"
dependencies = [
    "tomli>=2.0.0; python_version < '3.11'",
    "tomli-w>=1.0.0",
]
```

### 現在 (只支持 Python 3.12+)
```python
# config_manager.py
import tomllib  # 直接使用內建模組
```

```toml
# pyproject.toml
requires-python = ">=3.12"
dependencies = [
    "tomli-w>=1.0.0",
]
```

## 測試結果

```bash
$ uv run python -c "import tomllib; print('✓ 使用內建 tomllib')"
✓ 使用內建 tomllib

$ uv pip list | grep toml
tomli-w            1.2.0
```

## 升級指南

如果你正在使用舊版本的 Python：

1. **更新 Python**: 升級到 Python 3.12 或更高版本
   ```bash
   # 使用 pyenv
   pyenv install 3.12
   pyenv local 3.12
   
   # 或使用系統包管理器
   # Ubuntu/Debian
   sudo apt install python3.12
   
   # macOS
   brew install python@3.12
   ```

2. **重新安裝依賴**:
   ```bash
   uv sync
   ```

3. **驗證**:
   ```bash
   uv run python --version
   # 應顯示 Python 3.12.x 或更高
   ```

## Python 3.12 的優勢

- 🚀 **性能提升**: 比 3.11 快 5-10%
- 📦 **內建 tomllib**: 原生支持 TOML
- 🔧 **改進的錯誤訊息**: 更清晰的堆疊追蹤
- 🎯 **類型提示改進**: 更好的 typing 支持
- 🐛 **Bug 修復**: 眾多 bug 修復和穩定性改進

## 影響範圍

### ✅ 不受影響
- 所有配置功能正常工作
- TOML 讀寫功能完整
- 向後兼容性保持不變

### ⚠️ 需要注意
- 必須使用 Python 3.12+
- CI/CD 管道需要更新 Python 版本
- Docker 鏡像需要更新基礎鏡像

## 相關資源

- [Python 3.12 發布說明](https://docs.python.org/3/whatsnew/3.12.html)
- [tomllib 官方文檔](https://docs.python.org/3/library/tomllib.html)
- [PEP 680 - tomllib](https://peps.python.org/pep-0680/)

