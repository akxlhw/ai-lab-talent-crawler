---
name: ai-lab-talent-crawler
description: |
  采集全球顶尖 AI 实验室的人才数据。用浏览器服务驱动自主探索实验室官网，
  找到人员页面并提取结构化数据，输出标准 JSONL，供 AI4Talent 导入。
  触发场景："采集 X 实验室人才" / "爬取 AI Lab 人员" / "crawl lab talent" /
  "更新某实验室的人才数据" / "批量采集多个实验室"。
---

# AI Lab 人才采集

本 skill 让 agent 自主探索 AI 实验室官网，提取教授/博士生/博后等人才数据，
输出标准 JSONL 文件。agent 从实验室主域名出发，自己发现人才入口和跳转路径
（不依赖硬编码 URL），适应各实验室不同的页面结构。

## 何时触发

- 用户要求采集/爬取某 AI 实验室的人员/人才/教授/学生
- 用户要求更新某实验室的人才数据
- 用户要求批量采集多个实验室

## 前置依赖（执行前检查）

执行前必须确认两项依赖可用：

1. **浏览器自动化服务**（二选一，用当前可用的）：
   - Camofox：`GET http://localhost:9377/tabs?userId=probe` 返回标签列表即存活
   - kimi-webbridge：`GET http://127.0.0.1:10086` 可达即存活
   - 都不可用 → 停止，提示用户："请先启动浏览器服务（Camofox: `cd camofox-browser && npm start`，或 kimi-webbridge）"
   - **注意**：如果服务在运行但请求超时，可能是服务假死，需要重启

2. **Skill 自身可用性**：
   - 本 skill 可能安装在用户目录 `~/.agents/skills/` 而非系统目录
   - 如果 `skill_view` 加载失败但文件存在，需手动复制到系统目录：`cp -r ~/.agents/skills/ai-lab-talent-crawler ~/AppData/Local/hermes/skills/`

3. **LLM**：当前 agent 运行时已具备 LLM 能力（用于页面理解和人员提取），无需额外配置。

## 执行流程

采集分三个阶段，全部由 agent 自主完成：

### 阶段一：入口发现
1. 从 `labs.yaml` 匹配目标实验室，获取其主域名
2. 浏览器 navigate → 主域名
3. 浏览器 snapshot → LLM 分析页面导航和链接
4. 目标：找到 People/Faculty/Team/Members/Research Groups 类页面入口
5. 详细的链接判定规则见 `references/entry-discovery.md`
6. 记录发现的入口 URL 和跳转路径（写入 `_crawl_path_*.md`）

### 阶段二：结构探索
1. 浏览器 navigate → 发现的人才入口
2. 浏览器 snapshot → LLM 识别页面结构：
   - 有角色分区吗？（Faculty/PhD Students/Postdocs/Staff/Alumni）
   - 有分页吗？
   - 每个人有 bio 详情页链接吗？
   - 有子实验室链接吗？（如 research-groups）
3. 基于结构形成采集计划（哪些页要采、跳转链路、预计人数）

### 阶段三：数据提取（循环每个目标页）
1. 浏览器 snapshot → LLM 按 `references/extraction-prompt.md` 提取人员 JSON
2. 每个人记录：name / role_section / homepage / department（列表页字段）
3. **bio 详情全量跟进**：每个人的 bio 链接都跟进，补充 role_raw / cohort_year / email / research_areas（详见 extraction-prompt.md 的 bio 提取部分）
   - 注意：部分教授页面（如 Andrew Ng）可能需要登录，遇到登录墙则跳过并记录
   - 部分页面（如 Stanford CS 系的 profiles）可直接访问，应优先跟进这些页面获取完整信息
   - 对于大量人员（>100人），使用批量脚本自动化跟进，优先处理有 homepage 的人员
   - 无 homepage 的人员可通过实验室 profiles 系统或 CS 系人员页面补充信息
   - **大规模 bio 跟进策略**：当剩余待跟进人数 >50 时，优先使用 `references/large-scale-bio-followup.md` 中的并行子代理方案，将人员分成每批 15-30 人的小批次并发处理，避免单会话和单子代理的工具调用上限
4. 有分页 → 浏览器翻页 → 继续
5. 有子实验室 → 跟进其 people 页 → 继续
6. 累积所有人员

### 阶段四：应对工具调用上限与断点续采

Hermes 单次用户消息（turn）有工具调用上限。为避免长采集任务被中断后数据丢失，执行中必须遵守：

1. **工具调用预算分配**：
   - 单次 turn 总工具调用上限约为 50-100 次（取决于平台配置）
   - 预留 10-15 次给最终验证、报告生成和文件保存
   - 实际可用于页面采集的调用约 35-85 次

2. **优先级策略**：
   - 优先使用 `browser_console` 执行 JavaScript 批量提取，而非多次 `browser_navigate` + LLM 解析
   - 一个实验室人员列表页尽可能在 3-5 次工具调用内完成提取（navigate + console + 保存）
   - 避免在当前会话中逐个访问 50+ 人员的 bio 详情页

3. **断点保存点**：
   - 每完成一个子实验室的数据提取，立即保存 JSONL 中间文件
   - 每完成一批子代理的 bio 跟进，立即合并并保存主 JSONL
   - 中间文件命名：`output/<lab_slug>/_checkpoint_YYYY-MM-DD_HH-MM.jsonl`

4. **被中断后的恢复**：
   - 如果主会话达到上限中断，读取最新的 checkpoint JSONL
   - 从上次完成的位置继续，不要重新采集已确认的数据
   - 在报告中标注中断和恢复情况

5. **何时必须分 turn**：
   - 预计需要 >50 次工具调用才能完成时，提前告知用户将分多个 turn 执行
   - 每个 turn 结束时保存进度并给出阶段性报告

### 输出
1. 写 JSONL：`output/<lab_slug>/_YYYY-MM-DD.jsonl`（schema 见 `references/output-schema.md`）
2. 写完成报告：`output/<lab_slug>/_report_YYYY-MM-DD.md`（人数/角色分布/质量提示/异常）
3. 写探索路径：`output/<lab_slug>/_crawl_path_YYYY-MM-DD.md`（入口/跳转链/跳过决策）

## 完成标准

一次采集视为成功，需满足：
- 总人数 > 0
- 输出 JSONL 文件已生成且每行可被 JSON 解析
- 每行必含 name 字段
- 完成报告已生成

未满足 → 在报告中标注 "needs review" 并列出原因。**部分成功优于完全失败**：单个子站失败时，已采的数据正常输出，失败的子站记入报告。

## 约束（硬边界，必须遵守）

| 约束 | 说明 |
|------|------|
| 探索深度上限 5 跳 | 从主域名最多跟随 5 层链接，防止无限爬 |
| 单次时间预算 30min | 超限时停止，已采集的数据正常输出 |
| 跳过非人员页面 | twitter/github/会议/PDF/新闻/博客 → LLM 判定后跳过 |
| bio 详情全量跟进 | 列表页每个人都跟进其 bio 详情页；不采样、不限制；用户明确有充足 API 额度时，应完整跟进所有人员 |
| 不伪造字段 | 提取不到的字段直接省略（不写 null/空串/猜测值） |
| 每页提取校验 | LLM 输出的每人 JSON 必须含 name 字段，否则丢弃该条 |
| robots.txt 遵守 | 访问前检查，disallow 则跳过该路径 |
| 不登录/不绕验证码 | 遇到登录墙或验证码 → 跳过，记入报告 |
| 批量 bio 跟进 | 对于大量人员（>100人），使用批量脚本自动化跟进 bio 详情页，优先处理有 homepage 的人员，无 homepage 的通过 profiles 系统补充 |
| 大规模 bio 跟进并行化 | 当待跟进人数 >50 时，将人员分成每批 15-30 人的小批次，使用多个子代理（delegate_task）并行处理，避免单会话/单子代理的工具调用上限 |
| 子代理输出归集 | 子代理可能将更新文件写入非预期路径（如当前工作目录而非系统输出目录），合并前必须搜索所有可能的 `bio_updates_*.jsonl` 文件位置 |
| 实验室页面批量提取 | 对于人员列表页结构清晰的实验室（如 NLP Group、SVL），优先使用 `browser_console` 执行 JavaScript 一次性提取所有人员信息，而非逐个访问个人主页 |
| 表格数据提取 | 对于表格结构（如 statsml 的 Post-Docs 列表），优先使用 JavaScript 提取而非 LLM 解析 |
| 服务超时处理 | 浏览器服务超时假死时，检查进程状态并重启服务 |
| 子代理 API 限制 fallback | 子代理遇到 LLM API 限制（HTTP 429）时，切换到当前会话使用 `browser_console` 直接提取 DOM 内容，避免继续消耗子代理 API 额度 |
| 无 homepage 人员兜底 | 无 homepage 的 PhD 学生可从实验室人员列表页提取基础信息，并在 role_raw 中标注 "PhD Student"，不编造 |
| 主会话工具调用预算 | 单次 turn 预留 10-15 次工具调用给最终验证、报告和文件保存 |
| 断点续采 | 每完成重要阶段立即保存 JSONL checkpoint 文件 |
| 进度主动汇报 | 长任务中每完成一个子实验室或每 50 人向用户汇报进度 |
| 页面层级优先解析 | 人员页面必须先识别 **第一层分类**（如 Professors / Postdocs / PhD Students / Alumni），再判断第二层是否属于 Alumni 子分类。Alumni 下所有子分类（包括 "PhD Students"、"Research Scientists" 等）都属于校友，不得混入当前成员 |
| 结构化提取优先 | 优先用 `browser_console` + DOM 结构提取（如 `.showroom-controls .links`、`<h2>`、`<u>` 等），而非依赖纯文本关键词匹配，避免把 Alumni 子标题误当作当前成员分类 |
## 参考文件

执行时按需查阅：
- `references/output-schema.md` — JSONL 输出字段定义
- `references/extraction-prompt.md` — LLM 提取提示词（列表页 + bio 详情页）
- `references/entry-discovery.md` — 入口发现判定规则
- `references/importer-contract.md` — 与 AI4Talent importer 的接口契约
- `references/browser-service-management.md` — Camofox/kimi-webbridge 服务启动、探活、故障处理
- `references/lab-specific-patterns.md` — 各实验室页面结构特点和最佳采集策略（含 Stanford AI Lab 子实验室详细模式）
- `references/large-scale-bio-followup.md` — 大规模 bio 详情页跟进策略和子代理并行方案
- `references/photo-extraction.md` — 教授/学生照片提取（可选后处理）
- `references/github-skill-sync.md` — 将本 skill 同步到 GitHub 而不泄露 `output/` 数据
- `labs.yaml` — 目标实验室清单
- `scripts/crawl.py` — 辅助脚本（探活/写 JSONL/写报告/读 labs.yaml）
