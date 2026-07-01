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

**问题 7: 服务端口被占用**
- 症状：启动服务时返回 `port in use, port: 9377`
- 解决：服务已经在运行，直接使用即可。如果服务无响应，先查找并杀死占用进程，再重启。

## 服务健康检查流程

1. 发送探活请求：`GET http://localhost:9377/tabs?userId=probe`
2. 若无响应 → 检查进程 → 重启服务
3. 等待 5-10 秒后再次探活
4. 确认 `{"running":true,...}` 后再开始采集
