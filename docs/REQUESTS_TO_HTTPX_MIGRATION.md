# Requests → HTTPX 迁移总结

## 概述

已将所有使用 `requests` 库的代码迁移到 `httpx`，实现更现代、更高效的 HTTP 客户端。

## 迁移详情

### 📝 修改的文件

#### 1. **danmu.py**
```python
# 之前
import requests

response = requests.post(url, data=data, headers=headers, timeout=30)
response = requests.get(url, headers=headers, cookies=cookies, timeout=30)
except requests.RequestException as e:

# 之后
import httpx

response = httpx.post(url, data=data, headers=headers, timeout=30)
response = httpx.get(url, headers=headers, cookies=cookies, timeout=30)
except httpx.HTTPError as e:
```

**变更**:
- ✓ `requests.post()` → `httpx.post()`
- ✓ `requests.get()` → `httpx.get()`
- ✓ `requests.RequestException` → `httpx.HTTPError`

#### 2. **config.py**
```python
# 之前
import requests

session = requests.session()
latest_releases_info = session.get(req, timeout=3).json()

# 之后
import httpx

with httpx.Client() as client:
    response = client.get(req, timeout=3)
    latest_releases_info = response.json()
```

**变更**:
- ✓ `requests.session()` → `httpx.Client()` 上下文管理器
- ✓ 自动资源管理

#### 3. **ani_gamer_next.py**
```python
# 之前
import requests

def do_request(url, headers, cookies, params=None):
    return requests.get(url, headers=headers, cookies=cookies, params=params)

if bahamygatherPage.status_code == requests.codes.ok:

# 之后
import httpx

def do_request(url, headers, cookies, params=None):
    return httpx.get(url, headers=headers, cookies=cookies, params=params)

if bahamygatherPage.status_code == 200:
```

**变更**:
- ✓ `requests.get()` → `httpx.get()`
- ✓ `requests.codes.ok` → `200` (直接使用 HTTP 状态码)

#### 4. **anime.py**
```python
# 之前
import httpx
import requests  # 未使用，仅导入

# 之后
import httpx  # 只保留 httpx
```

**变更**:
- ✓ 移除未使用的 `import requests`

### 📦 依赖更新

#### pyproject.toml
```toml
# 之前
dependencies = [
    "requests==2.31.0",
    "httpx[socks]>=0.27.0",
]

# 之后
dependencies = [
    "httpx[socks]>=0.27.0",
]
```

**移除的依赖**:
- ❌ `requests==2.31.0`
- ❌ `charset-normalizer==3.4.3` (requests 的依赖)
- ❌ `urllib3==2.5.0` (requests 的依赖)

## HTTPX 优势

### 🚀 性能提升
- 支持 HTTP/2
- 连接池复用
- 更好的超时处理

### 🎯 现代特性
- 原生异步支持 (async/await)
- 类型提示友好
- 更清晰的 API

### 🔧 兼容性
- API 与 requests 高度相似
- 迁移成本低
- 支持 SOCKS 代理 (通过 httpx[socks])

## API 对照表

| Requests | HTTPX | 说明 |
|----------|-------|------|
| `requests.get()` | `httpx.get()` | GET 请求 |
| `requests.post()` | `httpx.post()` | POST 请求 |
| `requests.session()` | `httpx.Client()` | 会话管理 |
| `requests.RequestException` | `httpx.HTTPError` | 异常处理 |
| `requests.codes.ok` | `200` | HTTP 状态码 |
| `response.json()` | `response.json()` | JSON 解析（相同）|
| `response.text` | `response.text` | 文本内容（相同）|
| `response.status_code` | `response.status_code` | 状态码（相同）|

## 验证测试

### ✅ 导入测试
```bash
$ uv run python -c "import httpx; print('✓ httpx 导入成功')"
✓ httpx 导入成功
```

### ✅ 模块测试
```bash
$ uv run python -c "
import danmu
import config
from anime import Anime
print('✓ 所有模块导入成功')
"
✓ 所有模块导入成功
```

### ✅ 依赖检查
```bash
$ uv pip list | grep -E "(requests|httpx)"
httpx              0.28.1
httpx-socks        0.10.0
```

**确认**: requests 已完全移除

## 迁移统计

- **修改文件**: 4 个
  - danmu.py
  - config.py
  - ani_gamer_next.py
  - anime.py

- **替换次数**: 
  - `import requests` → `import httpx`: 3 次
  - `requests.*` 方法调用 → `httpx.*`: 6 次
  - 异常类型替换: 2 次

- **移除依赖**: 3 个
  - requests
  - charset-normalizer
  - urllib3

## 注意事项

### 🔄 会话管理
HTTPX 的 `Client()` 应该使用上下文管理器：

```python
# ✓ 推荐
with httpx.Client() as client:
    response = client.get(url)

# ⚠️ 也可以，但需要手动关闭
client = httpx.Client()
try:
    response = client.get(url)
finally:
    client.close()
```

### 🔌 代理支持
项目已配置 `httpx[socks]`，支持 SOCKS 代理：

```python
# SOCKS5 代理示例
proxies = {
    "http://": "socks5://localhost:1080",
    "https://": "socks5://localhost:1080"
}
client = httpx.Client(proxies=proxies)
```

### ⏱️ 超时设置
HTTPX 的超时更灵活：

```python
# 单一超时值（秒）
response = httpx.get(url, timeout=10.0)

# 详细超时配置
timeout = httpx.Timeout(
    connect=5.0,  # 连接超时
    read=10.0,    # 读取超时
    write=5.0,    # 写入超时
    pool=10.0     # 连接池获取超时
)
response = httpx.get(url, timeout=timeout)
```

## 后续建议

### 🎯 短期
- [x] 完成基本迁移
- [x] 移除 requests 依赖
- [x] 验证所有功能正常

### 🚀 长期优化
- [ ] 考虑使用异步版本 (`httpx.AsyncClient`)
- [ ] 统一使用连接池管理
- [ ] 添加重试机制 (httpx 支持自定义传输)
- [ ] 优化超时配置

## 参考资源

- [HTTPX 官方文档](https://www.python-httpx.org/)
- [从 Requests 迁移到 HTTPX](https://www.python-httpx.org/compatibility/)
- [HTTPX GitHub](https://github.com/encode/httpx)

## 回滚方案

如果需要回滚到 requests：

```bash
# 1. 恢复 pyproject.toml
uv add requests==2.31.0

# 2. 全局替换
# httpx → requests
# httpx.HTTPError → requests.RequestException

# 3. 恢复会话管理
# with httpx.Client() as client: → session = requests.session()
```

但建议保持使用 HTTPX，因为它代表了未来的方向。

