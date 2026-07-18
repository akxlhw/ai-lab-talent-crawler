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

### Stanford AI Lab Faculty 页面 (https://ai.stanford.edu/faculty/)

- **结构**：WordPress 页面，核心教师姓名存放在 `<span class="name">` 中，后跟研究方向简短描述
- **采集策略**：
  - 遍历 `span.name` 提取姓名
  - 通过父容器中的 `<p>` 或后续兄弟节点获取研究方向
  - "Read More" 链接通常指向 `cs.stanford.edu/people/<slug>/` 或 `profiles.stanford.edu/<id>`
- **分区**：Faculty / Affiliated Faculty / Former & Emeritus Faculty

### Stanford SNAP (http://snap.stanford.edu/)

- **人员页面**：http://snap.stanford.edu/people.html
- **结构**：`<h3>` 标题后跟 `<table>`，分 Faculty / PhD Students / PostDocs / Research and Administrative Staff / Students / Visiting Scholars / Alumni
- **采集策略**：直接使用 BeautifulSoup 解析表格，第一个 td 通常为姓名，后续 td 为当前去向（Alumni）

### Stanford Ermon Group (https://cs.stanford.edu/~ermon/website/)

- **人员页面**：https://cs.stanford.edu/~ermon/website/people.html
- **结构**：`<div class="content">` 内部使用 `<h1>` 作为分区标题（Faculty / Postdocs and Ph.D. Students / Alumni），每个人员为 `<div class="column">` 包含 `<div class="desc">`
- **采集策略**：遍历 `div.column`，从 `div.desc` 中提取姓名；括号内容为当前去向（Alumni）或 co-advisor 信息

### Stanford ML Group

- **主页**：https://stanfordmlgroup.github.io/
- **特点**：主页以项目展示为主，没有独立的 people/team 页面
- **采集策略**：如需采集 Andrew Ng 及其学生，需从项目页面或其他渠道装载

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

### 2026-07-18 重采更新
- **NLP 学生卡片是简化变体**：`<a><b>姓名</b></a><br/>院系`，无 h4；只匹配 `.description a h4` 会丢一半学生。且分区标题与成员不在同一 `.row`，必须按 DOM 顺序流式遍历
- **NLP 校友有 34 行无链接纯文本**（"姓名, 院系"），旧流程漏采
- **主站 Faculty 详情在隐藏 lightbox**：`div.lightbox`（经 `#lightbox-*` 锚点关联）含 research category + bio 链接 + 照片 → research_areas 新来源
- nlp.stanford.edu 需显式 `r.encoding='utf-8'` 防乱码
- SVL 是 Vue 站但人员已 SSR，HTTP 直连可解析
- 重采结果：829 人（Alumni 434、PhD 208、Faculty 43 等；NLP 449 / statsml 187 / SNAP 85 / 主站 63 / Ermon 32 / SVL 13）

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

### 2026-07-18 重采更新：Solr JSON 端点（重大发现）
- Angular 列表页背后是 **Solr JSON**：`/api-proxy/angular-solr?_api_proxy_uri=people&q=*:*&rows=216&start=N`，直接返回全量人员（姓名/角色/头衔/邮箱/详情页/头像），彻底免除浏览器 "Load More"
- **深分页限制**：`start >= 1000` 返回 403 → 按 `fq[]=ss_name:"<role>"` 分区查询规避；带空格的角色名必须加双引号（否则 0 结果）
- `facet=true&facet.field=ss_name` 可先拿分区计数；`sitemap.xml` 含全部 /person/ URL 可作备用列表源
- 头像映射：`public://...` → `https://www.csail.mit.edu/sites/default/files/styles/headshot/public/...`
- 重采结果：1167 人（Grad Students 790、Researchers 173、Core/Dual 108、Visitors 70 等；Staff/UROPS 排除），email 100%（Solr 直出），bio 1167 页 0 失败

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

### 往届毕业生提取（Alumni）
- **页面**: `http://www.lamda.nju.edu.cn/CH.previous_people_alumni.ashx`
- **结构**: 每人三行文本：
  ```
  姓名
  YYYY博士/硕士毕业
  现在：当前去向
  ```
- **采集方法**: 使用 BeautifulSoup `get_text('\n', strip=True)` 得到行列表，遍历匹配 `^\d{4}(博士|硕士)毕业$` 的行，前一行是姓名，后一行是当前去向（若以 "现在：" 开头）
- **主页链接**: 同页中的 `<a>` 标签以姓名为文字指向个人主页，建立 name → homepage 映射
- **输出字段**: `role_section="Alumni"`, `role_raw="YYYY 博士/硕士 毕业"`, `cohort_year=YYYY`, `current_position="..."`
- **重叠处理**: 部分现任教师/即将毕业博士同时出现在 Alumni 列表中（如 2025/2026 应届生）。保留多条记录，分别标记 `Faculty`/`PhD Students` 和 `Alumni`，导入时可按名字合并

#### 8. 师生关系（advisor）提取
- **优先使用 `teachers_students` / `faculty_students` JS 数组**：
  - LAMDA 主页 `CH.People.ashx` 内嵌 `teachers_students` 数组，含每位教师并其博士、硕士学生列表
  - 必须解析此数组，将 "学生 → 教师" 写入所有人员记录的 `advisor` 字段（包括 Alumni、在读博士生、在读硕士）
  - 如果 bio 页面的 Supervisor 与此映射不同，将少的那⸭放入 `co_advisor`
- **次要方法：从个人主页渲染后的纯文本提取**：
  - LAMDA 部分博士生页面使用 table+`<a>` 标签分割 "Supervisor" 和导师姓名，`BeautifulSoup.get_text()` 会将它们分成两行
  - HTTP 直接提取失败时（如只拿到 "essor" 碎片），用 Camofox `/evaluate` 运行 `document.body.innerText` 获取渲染后的纯文本，再用正则提取
  - 典型正则：`re.search(r'(?:under\s+the\s+supervision|supervised\s+by|Supervisor:)\s*(?:Prof\.?\s*)?([A-Z][a-zA-Z\s.-]+?)(?:\s*[.,;]|\s*$)', text)`

### 9. 研究方向清洗
- LAMDA 个人页面的 `About Me` / `Main Research Interests` 内 HTML 可能含有 `&nbsp;`、`<strong>`、`<em>` 等实体和标签
- 必须先用 `html.unescape()` 解码，再用 BeautifulSoup `get_text('\n', strip=True)` 去除标签
- 删除过渡性短语（"More specifically", "More generally", "I am interested in", "such as" 等）
- 最后按逗号/分号拆分成 research_areas 数组

### 10. 个人主页 URL 纠正
- 初始采集时不能用中文姓名作为 URL slug（如 `/李岚/` 是无效的）
- 必须从 `CH.PhD_student.ashx` / `CH.MSc_students.ashx` 的 `<a href>` 中直接读取拼音 slug（如 `/lil/`, `/shaojj/`, `/shiy/`）
- 已毕业学生如果不在当前学生列表中，但在 alumni 列表有个人主页，可以从 alumni 记录拷贝 URL 修复

## 验证记录
2026-07 从 LAMDA 校友页提取了 445 位毕业生（博士 87 + 硕士 358），覆盖 2004-2026 年。从 `teachers_students` 数组中建立了 251 条学生-导师映射，应用后 94/94 在读博士生和 73/445 校友拥有 advisor 字段。

### 2026-07-18 重采更新
- **MSc 学生页（CH.MSc_students.ashx）与 PhD 页结构完全相同**，同一 td 表格解析即可（上次漏采 116 人，是最大缺口）
- Director 锚点是 `<a id="director">`（id 非 name）
- 列表页全站 UTF-8（旧文档 GB2312 疑虑不实）；**个人主页仍有 GBK**，需回退解码
- `teachers_students` 数组映射从 251 缩到 198 条（毕业生被移除），Alumni advisor 覆盖随数据源下降
- 重采结果：656 人（新增 MSc 116；PhD 81、Alumni 445），cohort_year 98%、homepage 98%

## Berkeley AI Research (BAIR)

### 主域与人员入口
- **主域**: https://bair.berkeley.edu/
- **People 下拉**: Faculty (`/people/faculty`), Staff (`/people/staff`), Students & Alumni (`/people/students`)
- **Logo**: `<img alt="BAIR">` → `https://bair.berkeley.edu/logos/BAIR_Logo_Blue_BearOnly.svg`
- **简介**: `/about` 页
- **技术栈**: Next.js + MUI (Material UI) Chips

### 关键结构

#### 角色筛选器
- 元素不是传统 `<button>`，而是 MUI Chip 组件：`<div role="button">`
- 顺序：Current, All, Postdoc, PhD, Masters, Undergraduate, Visiting Scholar, Visiting Researcher, Alumni, Other
- **重要**: 默认为 "Current" （仅在读学生），必须点击 "All" 才能包含 Alumni
- 选择器: `document.querySelectorAll("[role='button']")` 而非 `document.querySelectorAll("button")`

#### 字母筛选器
- 元素：`<a class="cursor-pointer no-underline">` 和 `<a class="text-blue-800 no-underline">`
- 顺序：All, A, B, C, ..., Z
- 默认似乎不为 "All" 而是 "A" 字母，需遍历 A-Z 才能获取所有人员

#### 学生/校友卡片
每个 `<li>` 包含：
1. **姓名**: `<h2>`
2. **主页**: 外部 `<a href>`（可能为 `http://` 空链接）
3. **学位/role**: `<p>`之一（Alumni/PhD/Postdoc/Masters/Undergraduate/Visiting Scholar/Visiting Researcher）
4. **研究方向**: `<p>`，多个关键词通常以逗号分隔
5. **导师**: `<p>Advisors: X, Y, ...</p>`

### 采集策略

1. 使用 Camofox/类似浏览器服务渲染 Next.js 页面
2. 先点击 "All" 角色筛选器（使用 `[role="button"]` 选择器）
3. 遍历 A-Z 字母筛选器，每个字母提取卡片
4. 不需跟进个人主页，列表页已包含足够字段
5. 导师从 "Advisors: X, Y" 解析，第一个为 `advisor`，第二个为 `co_advisor`

### 字段映射
- Faculty → `role_section="Faculty"`
- Staff → `role_section="Staff"`
- PhD → `role_section="PhD Student"`
- Postdoc → `role_section="Postdoc"`
- Masters → `role_section="Master Student"`
- Undergraduate → `role_section="Undergraduate"`
- Alumni → `role_section="Alumni"`
- Visiting Scholar / Visiting Researcher → `role_section="Visitor"`

### 照片采集
- BAIR 的人员列表页（Faculty/Staff/Students）不显示头像照片
- Faculty 和 Students 通常有个人主页链接
- 如需 `photo_url`，必须在主页提取阶段完成后，批量跟进个人主页
- 提取策略：
  1. `img[alt*="姓名"]`
  2. `<main>` 内第一张尺寸 ≥ 80px 的非 Logo 图片
  3. 页面上最大的非 Logo/图标图片
- 预期命中率：Faculty 个人主页 60-80%（官方 people.eecs.berkeley.edu 页面模板不统一），学生个人主页 40-60%。
- 去向等信息未在列表页展示，如需应在报告中注明并录入未知字段等级。

### 已知异常
- 部分主页为 `http://` 空字符串，应当置为 `null` 而非空主页
- 部分 Undergraduate "Advisors:" 字段为空
- 校友当前去向（`current_position`）未在列表页展示
- 部分 Staff 姓名和职位紧凑在一起，需正则分离
- 列表页不含照片，需跟进个人主页补 `photo_url`

### 验证记录
2026-07 采集 645 位人员（Alumni 305, PhD Student 181, Faculty 91, Postdoc 29, Undergraduate 22, Master Student 10, Staff 5, Visitor 2），homepage 覆盖 87%，research_areas 898, advisor 74%, co_advisor 14%。

### 2026-07-18 重采更新
- 站点结构无变化（Next.js 必须浏览器渲染，点 "All" + 遍历 A-Z 一次成功）
- **照片复用提速**：重采时同名同 homepage 的人可继承上次已验证的 photo_url，只对新的人抓照片（本次复用 319 张、新抓 177 张）
- 站点更新频繁：6 天净增 188 人（+29%），重采价值高
- 重采结果：833 人（Alumni 407、PhD 254、Faculty 91 等），advisor 77%+15%、research_areas 82%、homepage 87%

## Princeton CS / ML

### 主域与人员入口
- **主域**：https://cs.princeton.edu（301 → `www.cs.princeton.edu`）
- **注意**：`/people` 是 **404**，入口是带参数的 faculty 页
- **六大分区**（People 菜单）：
  - Faculty `/people/faculty?facultyType=faculty`
  - Researchers `/people/research`
  - Technical Staff `/people/restech`
  - Administrative Staff `/people/admins`
  - Graduate Students `/people/grad`
  - Graduate Alumni `/people/gradalumni`
- **技术栈**：Drupal 服务端渲染 → **可全量 HTTP 采集**（requests + BeautifulSoup），浏览器仅用于入口发现

### 关键结构

#### Faculty 类型过滤器
- `select[name=facultyType]`：`faculty` / `associatedFaculty` / `visitors` / `emeritus`（空=All）
- GET query 参数直接生效；**按 4 类分别抓取**以保证 role_section 精确（All 页不标类型）
- 另有 `select[name=research]` 研究方向过滤器（采集时不需要，列表已全量）

#### 卡片结构 A（faculty/research/restech/admins 页）
`li.custom_card`：
- 姓名 + bio 链接：`a.custom_card__heading-link[href^="/people/profile/"]`
- 头衔：`div.position`
- 研究方向：`div.research_areas a`
- 照片：`div.custom_card__image img`（src 去 query 即原图）

#### 卡片结构 B（grad 页，207 人）
`li.custom_card` 变体，**姓名无链接（无 bio 页）**：
- 姓名：`h3.custom_card__heading` 纯文本
- 头衔：`div.position`（"Graduate Student"）
- 邮箱：`a[href^="mailto:"]`（直出！）
- **导师：`div.advisors a`**（直出！第一人 advisor，其余 co_advisor）
- 照片：同结构 A

#### Alumni 结构 C（gradalumni 页）
扁平结构，非卡片：`h2`=毕业年份，`h3`=姓名，随后文本含 `Adviser(s):` + `<a>` 导师链接 + `Degree: PhD, 2025`
- **GET `?year=YYYY` 过滤有效**（2026 回溯至 1960，每年约 25 人）
- 按范围约束默认只采最近 10 届；Degree 年份是毕业年 ≠ cohort_year，不写入

#### bio 详情页（/people/profile/<id>）
- 头衔：`div.profile__person--title`
- 邮箱：`div.profile__person--email a[href^="mailto:"]`
- 个人主页：`a.button__homepage`
- 研究方向：`div.profile__person--research_areas a`

### 已知异常
- **跨院系 Associated Faculty 的 bio 403**：约 13 人的 profile_url 指向 `ece/mae/soa/orfe.princeton.edu`，裸 requests 换完整浏览器头仍 403（反爬）。保留列表页字段记入报告，必要时用 Camofox 浏览器补
- 同名跨分区重复（Faculty/Associated Faculty、Alumni 跨年）→ 按 name 去重保留信息最全记录

### 验证记录
2026-07-17 全量 HTTP 采集 603 人（Graduate Students 207、Alumni 233（2017–2026 十届，含当日补采）、Faculty 74、Researchers 29、Associated Faculty 20、Admin Staff 17、Emeritus 12、Tech Staff 10、Visitors 1），email 350、advisor 444+25、photo 214，约 25 分钟完成（含 bio 跟进 150/163）。

## Mila (Quebec AI Institute)

### 主域与人员入口
- **主域**：https://mila.quebec
- **人员目录**：`/en/directory`（labs.yaml hint 的 `/en/people` 过期）
- **技术栈**：Drupal 服务端渲染 → **可全量 HTTP 采集**
- **WAF 实测**（2026-07-18）：旧报告记录的 cyberdefense.ai 拦截对带完整 Chrome UA +
  Accept-Language 的 `requests` 不生效，5500+ 请求零失败零 403，无需浏览器

### 关键结构

#### 目录分页与过滤器
- 分页 `?page=0..N`（103 页 × 36 卡片，约 3700 人含校友），服务端直出
- **仅 `mila-membership=<tid>` URL 过滤有效**：36 Core Academic / 32 Associate Academic /
  31 Core Industry / 33 Associate Industry / 34 Affiliate（合计约 270 人）
- `mila-member-type`（81 Students/45 Staff/368 Alumni/47 Lab Rep/46 Board）与
  `mila-team-type`（71 Leadership）的 URL 参数**无效**——checkbox 只被前端 JS 使用，
  加参数返回全量 103 页。要全量就直接翻 103 页，别走过滤器

#### 卡片（`.node--type-member`）
- 姓名 + 详情链接：`a[href*="/en/directory/"]`
- 角色文本：`.group-titles`（如 "PhD - Université de Montréal"、"Communications Lead, Executive Office"、"Alumni"）
- 头像：`img`，`no-picture` 占位图需排除
- 角色文本可直接粗分 role_section：PhD/Master/Postdoctorate/Professor/Alumni/
  Undergraduate/DESS/Intern/visiting·collaborating/scientist/行政关键词

#### 详情页（`/en/directory/<slug>`）
- 邮箱：`[class*=field-name-field-email1]`
- 头衔：`field-text4`（faculty）/ `field-text5`（学生，含 "PhD - 学校"）/ `field-text11`（staff）
- membership：`field-taxonomy-reference1`（"Core Academic Member" 等，可兜底修正 Unknown → Faculty）
- 研究方向：`field-taxonomy-references4` 的 `.field-item` 逐项（去掉 "Research Topics" 标签）
- 个人主页：`field-link4 a[href]`（link1=Scholar / link2=LinkedIn / link3=X / link5=GitHub）
- **导师**：`field-entity-reference1`（"Supervisor X"/"Principal supervisor : X"）、
  `field-entity-reference2`（Co-supervisor），正则去前缀
- 所属机构：从 "PhD - Université de Montréal" 的 ` - ` 后段解析 department

### 已知异常
- 校友详情页约 7 成稀疏（仅 name+角色文本），属数据源情况
- 6 对同名不同 slug 记录（疑同名不同人或重复建档）
- 目录无入学/毕业年份 → cohort_year 全员缺失；校友无法按年份裁剪，只能全量

### 验证记录
2026-07-18 全量 HTTP 采集 3700 人（Alumni 2055、PhD 562、Masters 345、Faculty 184、
Staff 172、Collaborators 151、Postdocs 82、Interns 69、Research Staff 34 等），
research_areas 1356、advisor 1266+252、department 1223、homepage 890、photo 995、
email 246。列表 32s + 详情两轮 19 min（首轮 12min 预算 3288/3700，resume 标记补完）。

## CMU Machine Learning Department

### 主域与人员入口（2026-07-18 验证）
- **主域**：https://ml.cmu.edu
- **列表页 JS 渲染，但数据直出 JSON 索引**：`https://ml.cmu.edu/peopleindexes/<slug>-index.v1.json`
  - 7 个分区索引（含 bio/title/rsrc/advisor/social/img 全字段，无需逐页跟进 bio）
  - **slug 与 URL path 不一致**：`/people/adjunct` → `adjunct-faculty-index`；`/people/phd-alumni` → `alumni-phd-index`（注意不是 phd-alumni-index）
- **email 来源**：`https://www.cs.cmu.edu/directory/api/v1/all.json`（SCS 全员名录，按 andrew id 匹配；由站点 `/js/main-people-*.js` 发现）
  - 禁止用 `id@andrew.cmu.edu` 拼接猜测（2026-07-16 采集的错误，已修正为仅名录真实值）
- 全程 2 类请求搞定，无需浏览器
- 重采结果：451 人（PhD Alumni 227、PhD Students 97、Core Faculty 42、Affiliated Faculty 39、Staff 31、Postdocs 13、Adjunct 2）

## 清华大学交叉信息研究院 (IIIS)

> 注：IIIS 已从 labs.yaml 官方清单移除（交叉学科机构非纯 AI 实验室），以下为历史采集经验存档。

### 主域与人员入口（2026-07-18 验证）
- **主域**：https://iiis.tsinghua.edu.cn（中文站，静态可解析，无需浏览器；robots.txt 404 无限制）
- 人员分散在各课题组页面（kaifeng.ac、weebly 站、DI Lab、ljktz 等）
- **email 全站不公开**（教师详情页仅公共邮箱），email 0% 非采集遗漏

### 关键结构
- **kaifeng.ac（React 站但 SSR 完整）**：react-aria tab 的所有 tabpane 都在初始 HTML，HTTP 直连即可
- **weebly 站（高阳组）**：人员列表是单 paragraph + `<br/>` 分隔，必须按 br 切分；逐 child 遍历会丢 cohort 并误吞 `<font>` 内联文本
- **ljktz 校友格式随年份漂移**（逗号/句号/括号/空格分隔姓名与学位），需多模式姓名正则
- DI Lab 头像 img 的 alt 恒为 "alt text"，占位图判定不能依赖 alt
- 校友 "Ph.D. 2023" 是毕业年，不得填 cohort_year

### 验证记录
2026-07-18 重采 255 人（Alumni 112、PhD 57、Faculty 32、Postdocs 14 等），advisor 71%、photo 44%、cohort_year 12%（含 cohort_source）。
