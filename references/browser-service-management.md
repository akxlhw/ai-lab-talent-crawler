# 浏览器服务管理参考

## Camofox 服务生命周期

### 检查服务是否存活
```bash
curl -s "http://localhost:9377/tabs?userId=probe"
# 预期返回: {"running":true,"tabs":[]}
```

### 启动服务（Windows + Git Bash）
```bash
cd /d/AI/hermes/camofox-browser && npm start
```
- 需要 Node.js >= 22
- 首次运行需 `npm install`（可能超时，需重试）
- 服务默认监听端口 9377

### 后台启动（Hermes 方式）
```bash
terminal(background=true, notify_on_complete=true):
  command: "cd /d/AI/hermes/camofox-browser && npm start"
```

### 常见问题

**问题 1: 服务假死（返回空响应或超时）**
- 症状：`curl` 无返回或浏览器工具超时
- 解决：检查进程并重启
  ```bash
  process(action="list")  # 查看进程
  process(action="kill", session_id="...")  # 杀死旧进程
  # 重新启动
  ```

**问题 2: 首次安装超时**
- 症状：`npm install` 超时退出（exit 124）
- 解决：Camoufox 二进制文件较大（~530MB），超时后重试即可
  ```bash
  cd /d/AI/hermes/camofox-browser && npm install
  ```

**问题 3: 路径问题（Windows Git Bash）**
- 使用 MSYS 路径格式：`/d/AI/hermes/...` 或 `D:/AI/hermes/...`
- 避免使用 `/d/D:/...` 混合路径

**问题 4: 浏览器 navigate 超时（Read timed out）**
- 症状：browser_navigate 返回 `Read timed out. (read timeout=30)`
- 解决：这是服务暂时无响应，通常页面实际已加载。直接继续下一步操作（browser_snapshot 或 browser_console）即可获取页面内容。如果多次超时，考虑重启服务。

**问题 5: 页面内容截断（[... N more lines truncated]）**
- 症状：browser_snapshot 返回内容被截断，无法完整提取数据
- 解决：使用 browser_console 执行 JavaScript 提取完整数据，例如：
  ```javascript
  Array.from(document.querySelectorAll('table tr')).map(row => {
    const cells = row.querySelectorAll('td');
    return {name: cells[0]?.textContent, ...};
  })
  ```
- 适用于：表格数据（如 statsml 的 Post-Docs 列表）、长列表等

**问题 6: 浏览器标签页过期/会话失效**
- 症状：browser_navigate 返回 `404 Client Error: Not Found for url: .../tabs/.../navigate`
- 解决：标签页会话已过期，需要重新创建标签页
  ```bash
  # 先检查服务健康状态
  curl -s http://localhost:9377/health
  # 如果 browserConnected=false，需要重启服务或重新初始化会话
  # 使用 browser_navigate 重新创建标签页（会自动创建新会话）
  ```

**问题 7: 新建标签页返回 503 "session_expired"**
- 症状：POST /tabs 返回 HTTP 503 `{"error":"Browser session expired. Retry to get a fresh session.","code":"session_expired"}`
- 区别：这不同于问题 6（已有标签页过期），而是在尝试创建新标签页时服务报告内部浏览器会话已失效
- 原因：Camofox 的内部浏览器实例长时间运行后会话 token 过期。通常是暂时的 — 重试即可恢复
- 解决：立即重试一次即可。如果连续重试仍然 503，考虑重启 Camofox 服务（npm start 重新启动）
- 生产策略：在批量 bio 采集中遇到此错误时，**只重试当前人员**，不要重启整个批次。使用 per-person tab 模式（见 batch-bio-extraction.md 中的 Variant: Per-Person Tab）隔离故障，避免单个 session_expired 影响后续人员
  ```python
  # Retry once on session_expired
  try:
      info = fetch_person_via_camofox(url, name)
  except Exception as e:
      if 'session_expired' in str(e) or '503' in str(e):
          info = fetch_person_via_camofox(url, name)  # retry
  ```

**问题 8: 服务端口被占用**
- 症状：启动服务时返回 `port in use, port: 9377`
- 解决：服务已经在运行，直接使用即可。如果服务无响应，先查找并杀死占用进程，再重启。

**问题 9: 标签页空闲约 5 分钟被自动回收**
- 症状：日志出现 `tab reaped (inactive)` / `session empty after tab reaper, closing`，之后对该 tabId 的操作返回 404
- 原因：Camofox 内置 tab reaper 会清理空闲超时的标签页（实测约 5 分钟），长时间用 HTTP 抓取、未操作浏览器时必然触发
- 解决：属正常行为，不影响服务本身。需要浏览器时重新 `POST /tabs` 创建标签页即可

**问题 10: 后台启动的服务被任务超时杀掉**
- 症状：以固定 timeout（如 600s）后台运行的 `npm start` 到点被杀，9377 端口失联
- 解决：后台启动服务时设置 `disable_timeout=true`（或足够大的 timeout）；采集中途发现服务没了，若后续步骤已切换为 HTTP 直连抓取则无需重启，仅在还需要浏览器时重启服务

## 服务健康检查流程

1. 发送探活请求：`GET http://localhost:9377/tabs?userId=probe`
2. 若无响应 → 检查进程 → 重启服务
3. 等待 5-10 秒后再次探活
4. 确认 `{"running":true,...}` 后再开始采集

## Camofox REST API 端点

当使用 Python/urllib 直接调用 Camofox REST API 而非 Hermes 浏览器工具时，以下端点最常用：

### 创建标签页
```http
POST /tabs
Content-Type: application/json

{"userId": "mit-scraper", "sessionKey": "batch8"}
```

`userId` 和 `sessionKey` 都是必需的。返回 `{"tabId": "uuid", "url": "about:blank"}`。

### 关闭标签页
```http
DELETE /tabs/{tabId}
Content-Type: application/json

{"userId": "mit-scraper"}
```

### 导航到 URL
```http
POST /tabs/{tabId}/navigate
Content-Type: application/json

{"userId": "mit-scraper", "url": "https://www.csail.mit.edu/person/..."}
```

返回 `{"ok": true, "tabId": "...", "url": "..."}`。需要 `userId` 参数。

### 执行 JavaScript 提取数据
```http
POST /tabs/{tabId}/evaluate
Content-Type: application/json

{"userId": "mit-scraper", "expression": "document.title"}
```

JS expression 可以是任意 JavaScript 表达式，返回值会被序列化为 JSON。适合用于 DOM 数据提取。

返回 `{"ok": true, "result": <serialized_value>}`。

### 获取页面可访问性树快照
```http
GET /tabs/{tabId}/snapshot?userId=mit-scraper&full=false
```

`full=false`（默认）返回精简视图（可交互元素），`full=true` 返回完整页面内容。

### 翻页/滚动
```http
POST /tabs/{tabId}/scroll
Content-Type: application/json

{"userId": "mit-scraper", "direction": "down"}
```

### 获取页面截图
```http
GET /tabs/{tabId}/screenshot?userId=mit-scraper
```

### 关键用法模式（Python，避免 curl）

所有 `/evaluate` 调用 **必须使用 Python 的 `json.dumps()`** 而不是 curl，因为 JS 表达式包含引号、多行字符串等特殊字符，shell 级 JSON 转义极易出错。

```python
def call_evaluate(tab_id, js_expression):
    import urllib.request, json
    url = f"http://localhost:9377/tabs/{tab_id}/evaluate"
    data = json.dumps({"userId": "mit-scraper", "expression": js_expression}).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    resp = json.loads(urllib.request.urlopen(req).read())
    return resp.get("result")
```
