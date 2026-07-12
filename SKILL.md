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
3. **同步提取实验室 logo**：使用 `references/lab-logo-extraction.md` 中的优先级策略，从主页提取 `logo_url`
4. 浏览器 snapshot → LLM 分析页面导航和链接
5. 目标：找到 People/Faculty/Team/Members/Research Groups 类页面入口
6. 详细的链接判定规则见 `references/entry-discovery.md`
7. 记录发现的入口 URL 和跳转路径（写入 `_crawl_path_*.md`）

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
2. 每个人记录：name / role_section / homepage / department / **photo_url**（列表页字段）
3. **bio 详情全量跟进**：每个人的 bio 链接都跟进，补充 role_raw / cohort_year / email / research_areas（详见 extraction-prompt.md 的 bio 提取部分）
   - 同时提取 **photo_url**：从个人主页找到头像照片URL（第一个非Logo、尺寸>80px的图片）
4. **往届毕业生采集**：主动寻找 `Previous People / Alumni / 往届研究生` 类页面，一律采集：
   - 记录姓名、毕业年份、学位（博士/硕士）、当前去向、个人主页
   - `role_section` 填 `"Alumni"`，`role_raw` 填 `YYYY 博士/硕士 毕业`
   - 与当前教师/学生重叠时保留多条记录（同一人可同时是 Alumnus 和 Faculty），在报告中标注重叠数量
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
**仅输出一个 JSONL 文件**供人才库导入：`output/<lab_slug>/_YYYY-MM-DD.jsonl`
- 第一行为 `"type": "lab"` 记录，包含 `lab_name`, `lab_slug`, `homepage`, `logo_url` 等实验室级字段
- 后续每行为 `"type": "person"` 记录，不输出单独的 `_lab_info.json`
- 标准格式见 `templates/import-jsonl.jsonl`
- 写完成报告：`<cwd>/output/<lab_slug>/_report_YYYY-MM-DD.md`（人数/角色分布/质量提示/异常）
- 写探索路径：`<cwd>/output/<lab_slug>/_crawl_path_YYYY-MM-DD.md`（入口/跳转链/跳过决策）
- 主动同步 Skill 修改：如果本次采集改变了 skill 本身（如 labs.yaml、schema、采集策略），最后必须按 `references/github-skill-sync.md` 将 skill 文件推送到远端 GitHub 仓库（保留 `output/` 在本地，不上传），并在报告中注明 commit hash

其中 `<cwd>` 是启动 Hermes 时的当前工作目录。这样每次项目的数据都保存在项目自己的目录下，不会和 skill 代码混在一起。脚本 `scripts/crawl.py` 中的 `resolve_output_dir` 函数已封装该逻辑：显式传入 `output_dir` 时使用该值，否则使用 `Path.cwd() / "output"`。

## 完成标准

一次采集视为成功，需满足：
- 总人数 > 0
- 输出 JSONL 文件已生成且每行可被 JSON 解析
- 每行必含 name 字段
- 完成报告已生成

未满足 → 在报告中标注 "needs review" 并列出原因。**部分成功优于完全失败**：单个子站失败时，已采的数据正常输出，失败的子站记入报告。

### CSAIL-Specific Efficiency: Static HTML Scraping

For **MIT CSAIL** (and other labs serving clean server-rendered HTML like Drupal sites), the browser-driven approach can be replaced with **concurrent HTTP scraping** for large batches:

1. **Fetch with requests or urllib** — Instead of `browser_navigate(url)` for each person, use `requests` (preferred — `pip install requests`) or `urllib.request` (stdlib fallback) with `concurrent.futures.ThreadPoolExecutor(max_workers=5)` to fetch 25+ pages in parallel. `requests` has significantly better timeout handling and error reporting than `urllib`.

2. **Parse with BeautifulSoup** — Use BeautifulSoup (+ lxml parser) instead of regex or LLM from accessibility tree. The HTML structure is consistent (field classes like `field--name-field-title`, `field--name-field-research-area`). BeautifulSoup is more reliable than raw regex on Drupal HTML (whitespace variations, entity encoding). Use regex only for year/number extraction from free-text bio paragraphs.

3. **Key HTML patterns to look for**:
   - `field--name-field-title` → role text
   - `field--name-field-research-area` (person-level, Format B) → research areas
   - `<h4>Research Areas</h4>` in group cards (Format A fallback) → group-level areas
   - `<h4>Related Links</h4>` → homepage under "Personal Website" or direct link
   - Bio paragraph text → cohort year from education history (e.g., "BS in ... in 2018") or from "since YYYY" / "joined ... YYYY" / "started/began ... YYYY" patterns

4. **Exclude footer/social media links** from homepage matching (facebook.com, twitter.com, youtube.com, instagram.com, linkedin.com, computing.mit.edu, web.mit.edu).

5. **This approach is 5-10x faster** than browser navigation for 25+ pages — the entire batch completes in ~30 seconds instead of several minutes.

6. **Fallback to browser** when the page requires JavaScript rendering or when regex parsing fails.

## 约束（硬边界，必须遵守）

| 约束 | 说明 |
|------|------|
| 探索深度上限 5 跳 | 从主域名最多跟随 5 层链接，防止无限爬 |
| 单次时间预算 30min | 超限时停止，已采集的数据正常输出 |
| 跳过非人员页面 | twitter/github/会议/PDF/新闻/博客 → LLM 判定后跳过 |
| bio 详情全量跟进 | 列表页每个人都跟进其 bio 详情页；不采样、不限制；用户明确有充足 API 额度时，应完整跟进所有人员 |
| photo_url 默认收录 | 从每个人员的个人主页提取头像照片URL（第一个非Logo图片），写入 photo_url 字段，不下载图片 |
| lab_logo_url 默认收录 | 从实验室主域名提取 logo URL，写入 JSONL 第一行 `type=lab` 记录，供实验室卡片展示 |
| 往届毕业生默认采集 | 主动寻找 `Alumni / 往届研究生` 页面，一律采集往届博士/硕士毕业生，`role_section="Alumni"`，与当前身份重叠时保留多条记录 |
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
- `references/photo-extraction.md` — 从个人主页提取成员头像照片URL（默认字段，非可选）
- `references/lab-logo-extraction.md` — 从实验室主页提取 logo URL（供实验室卡片展示）
- `references/mit-csail-page-structure.md` — MIT CSAIL 人物详情页面结构，含角色提取规则和研究领域标签处理
- `references/batch-bio-extraction.md` — 大规模 bio 详情页批量提取：Python + requests/BeautifulSoup 方案，比逐个浏览器导航快 5-10 倍，含 DOM 选择器参考表和服务超时处理
- `references/github-skill-sync.md` — 将本 skill 同步到 GitHub 而不泄露 `output/` 数据
- `labs.yaml` — 目标实验室清单
- `scripts/crawl.py` — 辅助脚本（探活/写 JSONL/写报告/读 labs.yaml）
