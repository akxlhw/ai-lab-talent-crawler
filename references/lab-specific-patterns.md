# 实验室特定采集模式

本文件记录各 AI 实验室的页面结构特点和最佳采集策略。

## Stanford AI Lab

### 主域名 (https://ai.stanford.edu)
- **结构**：导航菜单包含 Faculty, Research Groups, About 等
- **特点**：
  - Faculty 页面为纯文本列表，无个人链接 → 不适合直接采集
  - Postdoctoral Fellows 页面只有申请信息，无当前名单 → 跳过
  - Research Groups 页面列出子实验室链接 → 作为入口

### 子实验室

#### 1. Stanford NLP Group (https://nlp.stanford.edu/)
- **人员页面**：https://nlp.stanford.edu/people/
- **结构**：
  - 当前成员分区：`Professors`, `Affiliated Professors`, `Postdocs`, `PhD Students`, `Masters Students`, `Undergraduate Students`, `Visiting Scholars`, `Staff`
  - **Alumni 是主分水岭**：`Alumni` 之后是 `<u>` 包裹的子分类（如 Research Scientists, PhD Students, Master's Students, Undergraduate Alumni, PhD Alumni, Postdoctoral Fellows 等），**这些子分类全部属于校友，不是当前成员**
  - 人员分区使用 `.showroom-controls .links` 作为标题，但 `Alumni` 之后的标题应忽略
- **采集策略**：
  - 按 DOM 顺序解析，遇到 `Alumni` 标题立即停止当前成员采集
  - 使用 JavaScript 提取 `.showroom-controls .links` 标题，并对每个标题提取后续 `.row .team-member` 中的人员
  - 推荐脚本：`document.querySelectorAll('.showroom-controls')` 遍历标题，对每个标题收集下一个 `.row` 中所有 `.team-member a` 的 name/url，遇到 `Alumni` 停止
  - 不要简单按关键字匹配标题（会误把 Alumni 下的 PhD Students 当作当前成员）
  - 对于需要补充 bio 详情的人员，再逐个访问个人主页
  - 使用 LLM 从 accessibility tree 提取效果良好（适合小规模），但需先指示其忽略 Alumni 区域

#### 2. Stanford Vision and Learning Lab (https://svl.stanford.edu/)
- **人员页面**：https://svl.stanford.edu/people
- **结构**：按角色分区（Faculty, Postdocs, PhD Students, MS/BS Students, Visiting Researchers, Alumni）
- **采集策略**：
  - 列表页包含详细职位信息（如 "Assistant Professor"）
  - **优先使用 JavaScript 批量提取**：`document.querySelectorAll('article')` 提取所有人员，包含 advisor 和 email 信息
  - 部分人员有 Stanford CS 系个人页面链接
  - 可直接从列表页提取较多信息

#### 3. Stanford Statistical Machine Learning (https://statsml.stanford.edu/)
- **人员页面**：https://statsml.stanford.edu/students.html
- **结构**：表格形式，列包含 Name, Starting Year, Advisor, Department
- **采集策略**：
  - **必须使用 JavaScript 提取**：表格数据在 accessibility tree 中难以完整解析
  - 使用 `document.querySelectorAll('table tr')` 提取每行数据
  - 包含宝贵的 cohort_year 和 advisor 信息
  - 注意：URL 可能从 http 自动跳转到 https

### Stanford CS 系个人页面
- **模式**：`https://www.cs.stanford.edu/people/<name-slug>`
- **特点**：
  - 部分页面可直接访问（如 christopher-manning, fei-fei-li, serena-yeung）
  - 部分页面需要登录（如 andrew-ng）
  - 包含详细职位、教育背景、研究方向
  - 通常有 "View Full Stanford Profile" 链接到 profiles.stanford.edu

### Stanford Profiles (https://profiles.stanford.edu/)
- **模式**：`https://profiles.stanford.edu/<profile-id>` 或 `https://profiles.stanford.edu/<name-slug>`
- **特点**：
  - 最完整的个人信息来源
  - 包含：Bio, Academic Appointments, Honors, Publications, Contact
  - 可提取 role_raw, research_areas, department 等字段
  - 建议优先跟进此页面获取完整信息

### 通用策略

### 跨子实验室人员重复处理
- 同一人可能出现在多个子实验室（如教授同时指导 NLP 和 statsml 学生）
- 保留所有记录但确保 parent_lab 一致
- 去重时以 name 为键，合并信息最完整的记录

### 无 homepage 人员的处理策略
- 部分 PhD 学生（尤其是低年级）可能没有个人主页
- 处理优先级：
  1. 从实验室人员列表页提取基础信息（name, role_section, department, advisor）
  2. 通过实验室 profiles 系统搜索（如 profiles.stanford.edu）
  3. 通过 GitHub 搜索 `name + stanford + phd` 找到个人主页
  4. 如果仍无 homepage，在 role_raw 中标注 "PhD Student" 并记录 department
- 不要为空 homepage 的人员编造链接

### 页面层级解析：Alumni 不是当前成员
- 以 `https://nlp.stanford.edu/people/` 为例：
  - 第一层分类：`Professors` / `Affiliated Professors` / `Postdocs` / `PhD Students` / `Masters Students` / `Undergraduate Students` / `Visiting Scholars` / `Staff` / `Alumni`
  - `Alumni` 是独立的第一层主分类，其下第二层子分类（如 `Research Scientists`、`PhD Students`、`Master's Students`、`Undergraduate Alumni` 等）均属于校友，**不得混入当前成员**
- 必须先用 DOM 结构定位 `Alumni` 标题作为分水岭，再分别解析前后区域，避免把 Alumni 下的 "PhD Students" 子标题误当作当前 PhD Students
- 实现方式：使用 `browser_console` 查找 section 标题容器（如 `.showroom-controls .links`），按 DOM 顺序读取，遇到 `Alumni` 即停止当前成员解析，后续全部归入校友

### 结构化提取 vs 文本关键词匹配
- 不要仅依赖 `innerText` 关键词匹配来识别 section，因为 Alumni 下的子标题可能与当前成员分类同名（如 "PhD Students"）
- 优先使用 DOM 结构：标题容器的 class、顺序位置、`<u>`/`<b>`/`<h2>`/`<h3>` 标签；必要时直接查看页面 HTML 源码判断层级
- 对复杂页面，先保存一份原始 HTML 快照到本地，再离线解析

### 子代理 API 限制处理
- 子代理可能遇到 LLM API 限制（HTTP 429）
- 症状：子代理报告 "You've reached your usage limit"
- 解决：
  1. 在当前会话中直接处理剩余人员（而非继续启动子代理）
  2. 使用实验室人员列表页的 JavaScript 批量提取作为 fallback
  3. 对于无法通过 API 获取的页面，使用 browser_console 直接提取 DOM 内容

### 数据完整性优先级
1. **高优先级**：name, role_section, lab_name, parent_lab, source_url
2. **中优先级**：homepage, department, cohort_year, advisor
3. **低优先级**：email, research_areas, role_raw（需要跟进 bio 页）

### 大规模 Bio 跟进策略
当需要跟进 bio 详情的人员数量超过 50 人时：
- 优先使用 JavaScript 从实验室人员列表页批量提取基础信息
- 将剩余人员分成每批 15-30 人的小批次
- 使用多个子代理（delegate_task）并行处理
- 详细策略见 `references/large-scale-bio-followup.md`
