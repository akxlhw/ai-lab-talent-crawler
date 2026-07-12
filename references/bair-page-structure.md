# Berkeley AI Research (BAIR) 页面结构

**网站**：https://bair.berkeley.edu/  
**框架**：Next.js (React Server Components + 客户端渲染)  
**人员入口**：
- Faculty: `/people/faculty`
- Staff: `/people/staff`
- Students & Alumni: `/people/students`

## 首页与 Lab 信息

- **Logo**: `<img alt="BAIR">` → `https://bair.berkeley.edu/logos/BAIR_Logo_Blue_BearOnly.svg`
- **简介**：`/about` 页
- **研究方向**：在简介中第一段列出：computer vision, machine learning, natural language processing, planning, control, robotics, multi-modal deep learning, human-compatible AI, responsible AI

## 教职员页面 (`/people/faculty`)

- 单一无序列表 `<main>` > `<ul>` > `<li>`
- 每个 `<li>` 包含：
  - 外部主页链接 `<a href>`
  - 姓名 `<h2>`
- 部分教职员文本结尾含 "Steering Committee"
- 没有个人主页的不应编造，留空

## Staff 页面 (`/people/staff`)

- 同教职员页面结构
- 每个 `<li>` 文本为 "姓名职位" 紧凑在一起，需正则拆分
- 部分链接为 `mailto:`，可作为 email 字段

## 学生/校友页面 (`/people/students`)

### 角色筛选器

- 元素：MUI Chip 组件，实际为 `<div role="button">` 而非 `<button>`
- 顺序：Current, All, Postdoc, PhD, Masters, Undergraduate, Visiting Scholar, Visiting Researcher, Alumni, Other
- **重要**：要采集校友，必须点击 "All" 筛选器，否则默认仅显示 "Current" 在读学生
- 使用 `document.querySelectorAll("[role='button']")` 查找，不能用 `document.querySelectorAll("button")`

### 字母筛选器

- 元素：`<a class="cursor-pointer no-underline">` 和 `<a class="text-blue-800 no-underline">`
- 顺序：All, A, B, C, ..., Z
- 默认似乎展示 A 字母，需遍历 A-Z 获取所有人员

### 人员卡片结构

每个 `<li>` 包含：

1. **姓名**：`<h2>`
2. **主页**：外部 `<a href>`
3. **学位/role**：`<p>`之一（Alumni/PhD/Postdoc/Masters/Undergraduate/Visiting Scholar/Visiting Researcher）
4. **研究方向**：`<p>`，多个关键词通常以逗号分隔
5. **导师**：`<p>Advisors: X, Y, ...</p>`

### 导师提取

- 格式："Advisors: Advisor1, Advisor2, ..."
- 多导师时用逗号分隔，第一个写入 `advisor`，第二个写入 `co_advisor`
- 可能存在多空格或中英文标点，需清洗

## 采集建议

1. 使用 Camofox/类似浏览器服务渲染 Next.js 页面
2. 使用 `browser_console` 等 JavaScript API 批量提取，少用 Hermes 工具解析
3. 教职员/Staff 可一次性提取
4. 学生需要遍历 A-Z 字母筛选，每个字母提取后保存 checkpoint
5. 若服务不稳定，重启后从已保存的 checkpoint 续采
