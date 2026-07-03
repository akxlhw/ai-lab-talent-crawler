# 大规模 Bio 详情跟进策略

当需要跟进 bio 详情的人员数量超过 50 人时，单会话和单子代理都会遇到工具调用上限（通常 50-100 次）。本文件记录并行化策略和最佳实践。

## 核心策略：分批次 + 并行子代理

### 批次划分

将待跟进人员分成每批 **15-30 人** 的小批次：
- 每批大小控制在子代理能在 50 次工具调用内完成
- 优先将**有 homepage** 的人员分到同一批（处理更快）
- 无 homepage 的人员需要搜索，耗时更长，单独成批或混合分配

```python
# 示例：将 143 人分成每批 15 人的小批次
batch_size = 15
batches = [need_bio_list[i:i+batch_size] for i in range(0, len(need_bio_list), batch_size)]
# 结果：约 10 批，每批 15 人
```

### 并行执行

使用 `delegate_task` 同时启动 3 个子代理处理 3 个批次：

```python
delegate_task(tasks=[
  {
    "goal": "跟进 Stanford AI Lab 人才 bio 详情（批次 1）",
    "context": "读取 batch_1.json，包含 15 人...",
    "toolsets": ["browser", "terminal", "file"]
  },
  {
    "goal": "跟进 Stanford AI Lab 人才 bio 详情（批次 2）",
    "context": "读取 batch_2.json，包含 15 人...",
    "toolsets": ["browser", "terminal", "file"]
  },
  {
    "goal": "跟进 Stanford AI Lab 人才 bio 详情（批次 3）",
    "context": "读取 batch_3.json，包含 15 人...",
    "toolsets": ["browser", "terminal", "file"]
  }
])
```

### 子代理任务规范

每个子代理的任务指令必须包含：
1. **输入文件路径**：批次 JSON 文件的绝对路径
2. **输出文件路径**：明确的 `bio_updates_*.jsonl` 输出路径（建议放在系统输出目录）
3. **提取字段优先级**：role_raw > research_areas > email > department > homepage
4. **处理策略**：
   - 有 homepage → 直接访问提取
   - 无 homepage → 通过 DuckDuckGo/Google 搜索个人主页，或访问实验室人员页面获取基础信息
   - 页面无法访问 → 记录并跳过

### 输出归集

**关键**：子代理可能将文件写入非预期路径（如当前工作目录而非系统输出目录）。合并前必须搜索所有可能的文件位置：

```bash
# 搜索所有可能的 bio_updates 文件
find /c/Users/Administrator/ -name "bio_updates_*.jsonl" -type f 2>/dev/null
find /d/AI/hermes/ -name "bio_updates_*.jsonl" -type f 2>/dev/null
```

合并逻辑：
```python
# 读取所有可能的更新文件
updates_files = [
    '系统输出目录/bio_updates_batch1.jsonl',
    '系统输出目录/bio_updates_batch2.jsonl',
    '当前工作目录/bio_updates_small4.jsonl',  # 子代理可能写在这里
    'D:/AI/hermes/bio_updates_small/bio_updates_small6.jsonl',  # 或这里
]

for uf in updates_files:
    if os.path.exists(uf):
        # 逐行解析 JSONL
        for line in open(uf):
            update = json.loads(line)
            # 合并到主数据
```

## 效率优化：实验室页面批量提取

对于人员列表页结构清晰的实验室，**优先使用 JavaScript 一次性提取所有人员**，而非逐个访问个人主页：

### NLP Group 示例
```javascript
// 从 https://nlp.stanford.edu/people/ 提取所有人员
const people = [];
const links = document.querySelectorAll('a[href*=".github.io"], a[href*=".stanford.edu"]');
links.forEach(link => {
    const parent = link.parentElement;
    const nameEl = parent.querySelector('h4') || link;
    const deptEl = parent.querySelector('p');
    people.push({
        name: nameEl.textContent.trim(),
        homepage: link.href,
        department: deptEl ? deptEl.textContent.trim() : ''
    });
});
```

### SVL 示例
```javascript
// 从 https://svl.stanford.edu/people 提取所有人员
const articles = document.querySelectorAll('article');
articles.forEach(article => {
    const nameLink = article.querySelector('a');
    const paragraphs = article.querySelectorAll('p');
    // 提取 name, role_raw, email, advisor...
});
```

### StatsML 表格示例
```javascript
// 从 https://statsml.stanford.edu/students.html 提取表格数据
const rows = document.querySelectorAll('table tr');
rows.forEach(row => {
    const cells = row.querySelectorAll('td');
    if (cells.length >= 2) {
        const name = cells[0].textContent.trim();
        const cohort_year = cells[1].textContent.trim(); // 入学年份
        // 提取 advisor, department 等
    }
});
```

## 故障处理

### 子代理 API 限制（HTTP 429）
- 症状：子代理报告 "You've reached your usage limit" 或 "HTTP 429"
- 原因：子代理使用 LLM 进行页面解析时触发 API 限流
- 解决：
  1. 停止启动新的子代理
  2. 在当前会话中直接使用 `browser_console` 执行 JavaScript 提取
  3. 对于实验室人员列表页，使用 JavaScript 一次性批量提取所有人员信息
  4. 对于无法提取的字段，记录为缺失而非编造
- 预防：
  - 子代理任务中减少 LLM 调用，优先使用 `browser_console` 提取
  - 将需要 LLM 解析的工作转移到当前会话完成

### 主会话工具调用上限
- 症状：主 agent 提示 "You've reached the maximum number of tool-calling iterations allowed"
- 原因：单次 turn 的工具调用次数达到平台上限（通常 50-100 次）
- 解决：
  1. 立即停止后续采集，保存当前 JSONL 到 checkpoint 文件
  2. 给用户一个阶段性总结，说明已完成的部分和剩余工作
  3. 用户回复 "继续" 后，读取 checkpoint 并从中断点继续
- **预防**：
  - 每个 turn 预留 10-15 次调用给保存和报告
  - 单 turn 内不要逐个访问 50+ 人员的 bio 详情页
  - 优先使用批量 JavaScript 提取，减少工具调用次数
- **实验室特定成本估算**：
  - MIT CSAIL `/person/*` 详情页：每页 2 次工具调用（1× navigate + 1× console）。25 人 ≈ 50 次调用 + 10 次保存 ≈ 60 次。一次 turn 可完成约 20-25 人，超出需分批
  - Stanford CS profiles：每页 2-3 次调用。页面更复杂可能需要解析 accessiblity tree
  - 对于已知每人需 2 次调用的实验室，批次大小 = floor((上限 - 15) / 2)

### 子代理超时
- 症状：子代理在 600 秒后超时，部分批次未完成
- 解决：重新启动剩余批次的子代理，或改为当前会话直接处理

### 子代理达到迭代上限
- 症状：子代理报告 `max_iterations` 退出，部分人员未处理
- 解决：将剩余人员重新分成更小的批次（每批 10-15 人），再次启动子代理

### 浏览器服务中断
- 症状：子代理报告 CamoFox 连接失败
- 解决：在当前会话中重启服务，然后继续处理

### 子代理超时后的主会话恢复

当子代理超时（600s 限制）或未能生成输出文件时，主会话可以直接接管剩余批次：

1. **检测未完成的批次**：检查输出目录中缺失对应的 `bio_updates_batchN.jsonl` 文件
2. **静默 HTTP 提取（推荐）**：对提供静态 HTML 的实验室（Drupal 站如 MIT CSAIL），用 Python urllib/requests 并发抓取，无需启动浏览器：
   ```python
   from urllib.request import urlopen, Request
   import re, json, html as html_mod
   for person in batch:
       req = Request(person['source_detail_url'], headers={'User-Agent': 'Mozilla/5.0'})
       with urlopen(req, timeout=30) as resp:
           page = resp.read().decode('utf-8')
       m = re.search(r'field--name-field-title[^>]*>\s*(.*?)\s*</div>', page)
       if m: person['role_raw'] = html_mod.unescape(m.group(1)).strip()
   ```
3. **浏览器 fallback**：HTTP 超时（CSAIL 服务器有时很慢）时，对特定页面回退到 `browser_navigate`
4. **直接写输出**：结果写入 `bio_updates_batchN.jsonl`，继续合并流程
5. **无需重启子代理**：主会话直接处理比启动新子代理更省 LLM token（避免子代理的完整提示词开销）

## 最佳实践总结

1. **先批量提取列表页**：使用 JavaScript 从实验室人员页面一次性提取所有人员基础信息
2. **再跟进缺失字段**：对于列表页无法获取的字段（research_areas, email 等），再使用子代理并行跟进个人主页
3. **小批次并行**：每批 15-30 人，同时启动 3 个子代理
4. **全面搜索更新文件**：合并前搜索所有可能的文件路径
5. **增量合并**：每轮子代理完成后立即合并，避免重复工作
6. **API 限制 fallback**：当子代理遇到 API 限制时，切换到当前会话使用 JavaScript 批量提取
7. **工具调用预算**：预留 10-15 次调用给最终保存和报告；主会话接近上限时主动保存 checkpoint
8. **进度汇报**：每完成一个子实验室或每处理 50 人，向用户汇报当前进度
