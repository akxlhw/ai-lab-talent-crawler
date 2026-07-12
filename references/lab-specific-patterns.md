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

## MIT CSAIL

### People 页面 (https://www.csail.mit.edu/people/)

- **类型**: Angular 单页应用 (ng-version="12.1.2")，非传统 HTML 页面
- **分页机制**: "Load More" 按钮，每次点击加载约 216 条。共需点击约 5 次加载全部约 1080 人（含所有角色）
- **角色筛选**: 左侧面板有 Role 筛选复选框：Principal Investigators, Core/Dual, Associates, Emeritus, Researchers, Graduate Students, UROP, Staff, Administration, Alumni, Visitors
- **排序**: 默认按姓名首字母升序（A→Z）
- **JavaScript 提取**: 加载全部人员后，使用 `document.querySelectorAll('article')` 提取所有人员卡片。每张卡片包含姓名、角色文字、邮箱、房间号，约 50% 有研究关键词
- **输出截断注意**: 1080+ 条数据 JSON.stringify 输出可能被截断。解决：先单独提取 URLs 列表，再逐批处理；或分多次 `slice()` 提取

### 主域名 (https://www.csail.mit.edu)
- **People 页面**: https://www.csail.mit.edu/people/
- **人员详情页模式**: `https://www.csail.mit.edu/person/<name-slug>`
- **特点**: 所有页面可直接访问，无需登录

### 详情页 DOM 结构 (`/person/*`)

每个 bio 详情页的 `<article>` 包含 3 个主要 DIV：

1. **`.full-width.green-background`** — 照片、姓名 (`<h1>`)、简单位置文字（如 "Professor"、"Associate Professor"、"Visiting Scholar"）
2. **`.content-container.person-bottom`** — 邮箱、电话、房间、bio 段落、Research Areas、Impact Areas、Related Links
3. **`.content-container.page-resources`** — 项目、研究组、新闻

### Research Areas 常见标签值

CSAIL 页面上 "Research Areas" 标签（taxonomy term links）使用以下固定值：

- `AI & ML`
- `Graphics & Vision`
- `Computer Architecture`
- `Security & Cryptography`
- `Algorithms & Theory`
- `Systems & Networking`
- `Computational Biology`
- `Programming Languages & Software Engineering`

一个页面通常有 0-3 个标签。**约 50% 的页面完全没有 Research Areas 部分**，此时直接省略该字段，不要从文本推断。

### Impact Areas 常见标签值

出现频率低于 Research Areas，常见值：`Health Care`, `Cybersecurity`, `Big Data`, `Entertainment`, `Education`, `Transportation`

### 页面完整性波动

CSAIL 人物页面的字段齐全度差异很大。根据对 25 名人员的抽样（2026年7月）：

| 字段 | 存在率 | 备注 |
|------|--------|------|
| role_raw | ~100% | 始终存在，但"Professor"有时需结合段落中的 Chair 名称使用 |
| email | ~100% | 始终存在 |
| Bio/简介段落 | ~60% | 资深教授通常有详细生平 |
| Research Areas 标签 | ~50% | ~一半的页面完全没有 Research Areas 分区 |
| Homepage 链接 | ~40% | 更多出现在中青年教师页面 |
| Phone | ~50% | 随机出现，无规律 |
| Room | ~60% | 随机出现，无规律 |

通常更简短的页面（只有 email，无 bio、无 research areas）是**Adjunct Professor**、**Professor of the Practice** 或新入职的 Assistant Professor。这可能是正常现象——不是采集错误。

| 字段 | DOM 位置 | 注意事项 |
|------|---------|---------|
| **name** | `document.querySelector('h1').textContent.trim()` | 始终存在 |
| **role_raw** | 优先从段落中提取详细角色 | 简单角色在 `<h1>` 的下一个兄弟元素（"Professor"），详细角色在段落文字中（如 "Professor of Computer Science and Engineering in the EECS department"）。优先取段落中的详细版本 |
| **email** | `a[href^="mailto:"]` | **陷阱**：页脚有一个通用的 `news@csail.mit.edu?subject=CSAIL%20Media%20Inquiry` mailto 链接。必须过滤掉含 `?` 的地址。建议遍历所有 mailto 链接，取第一个含 `@` 且不含 `?` 的 |
| **research_areas** | `<h4>Research Areas</h4>` 的 nextElementSibling 中的 `<a>` 链接 | 并非所有页面都有此部分（如 Eric Alm、Anant Agarwal 没有）。提取到空数组时直接省略 |
| **impact_areas** | `<h4>Impact Areas</h4>` 的 nextElementSibling 中的 `<a>` 链接 | 可选字段 |
| **homepage** | 查找文字"Website"的 `<a>` 链接 | 部分页面缺失（如 Eric Alm、Pulkit Agrawal） |
| **cohort_year** | 教授页面上通常不显示 | **不要从论文发表年份推断**。如果不显示，直接省略 |

### JavaScript 完全提取模板

```javascript
(function() {
  const allH4 = Array.from(document.querySelectorAll('h4'));
  const researchH4 = allH4.find(h => h.textContent.trim() === 'Research Areas');
  let researchAreas = [];
  if (researchH4 && researchH4.nextElementSibling) {
    const links = researchH4.nextElementSibling.querySelectorAll('a');
    researchAreas = Array.from(links).map(l => l.textContent.trim()).filter(Boolean);
  }
  const h1 = document.querySelector('h1');
  const name = h1 ? h1.textContent.trim() : '';
  const mailLinks = Array.from(document.querySelectorAll('a[href^="mailto:"]'));
  let email = '';
  for (const link of mailLinks) {
    const address = link.href.replace('mailto:', '');
    if (address.includes('@') && !address.includes('?')) {
      email = address;
      break;
    }
  }
  let roleRaw = '';
  if (h1 && h1.nextElementSibling) {
    roleRaw = h1.nextElementSibling.textContent.trim();
  }
  const paras = Array.from(document.querySelectorAll('p'));
  const profPara = paras.find(p => /(?:Professor of|Professor in|Associate Professor|Assistant Professor|Professor at|Professor Emeritus|X Consortium|John and Dorothy Wilson|School of Engineering Professor)/i.test(p.textContent));
  if (profPara) {
    const match = profPara.textContent.match(/(?:John and Dorothy Wilson Professor[^.,;]*|School of Engineering Professor[^.,;]*|X Consortium[^.,;]*|Professor of[^.,;]*|Professor in[^.,;]*|Associate Professor[^.,;]*|Assistant Professor[^.,;]*|Professor Emeritus[^.,;]*|Professor at[^.,;]*)/i);
    if (match) roleRaw = match[0].trim();
  }
  const websiteLinks = Array.from(document.querySelectorAll('a')).filter(l => l.textContent.trim() === 'Website');
  const homepage = websiteLinks.length > 0 ? websiteLinks[0].href : '';
  return {name, role_raw: roleRaw, email, research_areas: researchAreas, homepage};
})()
```

### 工具调用预算提示

MIT CSAIL 每个 bio 详情页约需 **2 次工具调用**（1× navigate + 1× console）。处理 25 人约需 50 次调用 + 10 次保存/报告 ≈ 60 次。预计一次 turn 可完成约 20-25 人；超出则需在每 10-15 人后保存 checkpoint。

### 已知页面特征

- **详细 BIO 页**: Hal Abelson、Ted Adelson、Saman Amarasinghe — 有详细生平段落和多个研究领域标签
- **精简页面**: Eric Alm、Anant Agarwal — 只有基本联系信息，无 Research Areas 分区
- **外部链接**: Naser AlDuaij (Visiting Scholar) — 有 LinkedIn 和个人网站
- **通过研究组归属**: Pulkit Agrawal、Jacob Andreas — 主要通过研究组页面间接展示领域（Embodied Intelligence、NLP Group）

### 提取后去重注意事项

同一人的 email 字段可能在列表页和 bio 页都有记录。以 bio 页为准（更准确）。如果同一人出现在 batch JSON 中多次（如跨角色采集），以 name 为键去重，取信息最完整的记录。

## 南京大学 LAMDA 实验室

### 主域名 (http://www.lamda.nju.edu.cn)

- **类型**: ASP.NET WebForms + ScrewTurn Wiki
- **导航**: 图片式表格导航，通过 `onclick="window.location='CH.People.ashx'"` 跳转
- **Robots.txt**: 无 robots.txt 限制，可直接爬取
- **特点**: 中国高校实验室典型结构，教师数据通过 JavaScript 数组 `teachers_students` 动态渲染，博士生通过独立表格页面展示
- **Logo**: 主页图片式导航中的 `images/pub/lamda.png` 即为实验室 logo

### 人员入口

- **主页面**: `http://www.lamda.nju.edu.cn/CH.People.ashx`
  - 锚点导航: `#director`(负责人) / `#faculty`(教师) / `#visitprof`(访问教授)
  - **关键**: 教师列表数据存储在 JS 变量 `teachers_students` 中，通过 `let teachers_students = [...]` 内联在 HTML `<script>` 标签内
- **博士生**: `CH.PhD_student.ashx`
- **硕士生**: `CH.MSc_students.ashx`
- **博士后**: `CH.postdoctoral_fellow.ashx` 通常为空，快速跳过
- **校友**: `CH.previous_people_alumni.ashx`

### 采集策略

#### 1. 教师数据提取（JS 数组）
教师/学生关系数据存储在 HTML 的 JavaScript 数组中，不渲染在 DOM 中：
```javascript
// teachers_students 数组结构
[
  {
    name: "高尉",
    link: "http://www.lamda.nju.edu.cn/gaow",
    introduction: "博士, 教授, 博导",
    students: {
      doctors: [{name: "钱梦瑄", link: "...", year: "2022"}, ...],
      masters: [{name: "白雪童", link: "...", year: "2023"}, ...],
    }
  },
  ...
]
```
**采集方法**:
1. 获取页面 HTML 源码（curl 或 urllib，**不要**用 browser_navigate + snapshot）
2. 用正则 `let teachers_students\s*=\s*(\[[\s\S]*?\])\s*;` 提取 JS 数组
3. 用 Python 解析 JS 对象语法（key 无引号，字符串用双引号）
4. 如果直接用 `json.loads()` 失败，是因为 JS 对象 key 缺少引号，需手动转换

#### 2. 博士生数据提取（表格）
`CH.PhD_student.ashx` 是二维表格，每格包含姓名链接 + 入学年份。**采集方法**：使用 `browser_console` 执行 JavaScript 一次性提取：
```javascript
const allLinks = document.querySelectorAll('td a');
const data = [];
allLinks.forEach(a => {
  const text = a.textContent.trim();
  const href = a.href || '';
  if (href.includes('lamda.nju.edu.cn') && text && text.length < 20 
      && !href.includes('CH.') && !href.includes('Edit.aspx')
      && !href.includes('MainPage')) {
    const td = a.closest('td');
    const tdText = td ? td.textContent.trim() : '';
    const yearMatch = tdText.match(/(\d{4})\s*-/);
    const cohortYear = yearMatch ? parseInt(yearMatch[1]) : null;
    data.push({name: text, homepage: href, cohort_year: cohortYear});
  }
});
JSON.stringify(data);
```
注意过滤掉 `[English]` 导航链接（指向 `MainPage.ashx`）。

#### 3. Bio 并发 HTTP 提取
LAMDA 个人主页是**静态 HTML**，适合用 ThreadPoolExecutor 并发 HTTP 提取（比逐个浏览器导航快 20-30 倍）：
```python
from urllib.request import urlopen, Request
import concurrent.futures

def fetch(url):
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urlopen(req, timeout=12) as resp:
        return resp.read().decode('utf-8', errors='replace')

with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
    futures = {ex.submit(fetch, url): name for name, url in url_map.items()}
    for f in concurrent.futures.as_completed(futures):
        html = f.result()
        # 用正则或 BeautifulSoup 解析
```
- 94 人约 30 秒完成并发提取
- 邮箱：PhD 页面使用直接邮箱格式 `xxx@lamda.nju.edu.cn`，教工页面使用混淆格式 `xxx(at)nju(dot)edu(dot)cn`
- 研究方向：在 `About Me` 段落中，通过 `include` / `focus on` / `interested in` 等关键词定位

#### 4. Logo 提取
LAMDA logo 位于主页图片式导航中：
```
http://www.lamda.nju.edu.cn/images/pub/lamda.png
```
也可以从 `<link rel="icon">` 获取 favicon `Themes/chDefault/Icon.ico`。导出时将其作为 JSONL 第一行 `type=lab` 记录的 `logo_url`。

### 个人主页 URL 模式
- **教师**: `http://www.lamda.nju.edu.cn/<pinyin>`（无尾部斜杠），少数在 `cs.nju.edu.cn/xxx` 或 `ai.nju.edu.cn/xxx`
- **博士生**: `http://www.lamda.nju.edu.cn/<pinyin-slug>/`（有尾部斜杠，如 `liuyr/`)
- **注意**: URL 使用英文缩写/拼音路径，**不是中文拼音全称**。必须从页面提取链接，不能根据中文名猜 URL

### 个人页面结构（博士生示例）
```
<h1>Yu-Ren Liu @ LAMDA, NJU-CS</h1>
[Name: 刘驭壬 / Yu-Ren Liu]
[Role: Ph.D. student]
[Advisor: Prof. Yang Yu]
[Email: liuyr@lamda.nju.edu.cn]
[About Me section - contains research interests]
[Education section - contains cohort year info]
[Publication section]
```

**提取正则**:
- role_raw: `(Ph\.D\.\s+(?:student|Student|candidate|Candidate))`
- email（直接）: `Email:\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})`
- email（混淆）: `([\w.-]+)\(at\)([\w.-]+)\(dot\)([\w.-]+)` → 拼接为 `{1}@{2}.{3}`
- cohort_year: 从 Education 段或 `admitted/enrolled/started/joined in YYYY` 提取
- research_areas: 从 `About Me` 段 `include/focus on/interested in` 后提取逗号分隔的内容
- advisor: `Supervisor:\s*(?:Prof\.?\s*)?([^<\n]+?)(?:Co-supervisor|Email|$)`

### 注意事页
1. **JS 数组解析陷阱**: `teachers_students` 使用 JS 对象语法（key 无引号），不能直接用 `json.loads()`。需自行编写解析器将 JS 对象转 Python dict
2. **外部域名教师**: 部分教师主页在 `cs.nju.edu.cn` 或 `ai.nju.edu.cn` 下，HTML 结构不同，需独立处理或用浏览器查看
3. **空角色页面**: 博士后页面和访问教授页面可能完全为空，快速跳过
4. **LAMDA-RL 小组**: 作为独立小组列出，其博士生包含在主博士生列表中，避免重复
5. **Faculty 页面 URL 无斜杠**: 教师主页如 `gaow` 可能重定向到 `gaow/`，两种形式都试
6. **邮件混淆**: 教工页面使用 `(at)` 和 `(dot)` 混淆，需要还原；PhD 页面通常直接显示
7. **输出格式**: 单一 JSONL 文件，第一行 `type=lab` 记录包含 logo_url，后续每行 `type=person` 人员记录
