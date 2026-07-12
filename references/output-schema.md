# JSONL 输出 Schema

采集的最终产物是 JSONL 文件（第一行是实验室元数据记录，后续每行一个 JSON 对象代表一个人）。本文件定义字段。

## 文件位置

```
output/<lab_slug>/_YYYY-MM-DD.jsonl
```

`lab_slug` 是 labs.yaml 里 lab name 的 slug 化（小写+下划线，如 "Stanford AI Lab" → `stanford_ai_lab`）。

## 字段定义

| 字段 | 必填 | 类型 | 说明 |
|------|------|------|------|
| `type` | ✅ | string | 固定为 `"person"` |
| `name` | ✅ | string | 姓名 |
| `role_section` | ✅ | string | 页面分区原始标签（Faculty/PhD Students/Postdocs/Staff/Alumni）；无分区填 "Unknown" |
| `role_raw` | 可选 | string | bio 详情页的完整头衔原文（如 "Associate Professor of Computer Science"） |
| `homepage` | 可选 | string | 个人主页 URL |
| `email` | 可选 | string | 邮箱（从 bio 详情页提取） |
| `department` | 可选 | string | 院系/专业（如 "Computer Science"） |
| `research_areas` | 可选 | array[string] | 研究方向列表 |
| `cohort_year` | 可选 | integer | PhD 入学/加入年份（如 2020） |
| `cohort_source` | 可选 | string | 届别推断来源，格式 `<来源类型>:<原文片段>`（如 `bio_detail:"PhD since 2021"`） |
| `lab_name` | ✅ | string | 所属子实验室/研究组（如 "Stanford NLP Group"） |
| `parent_lab` | ✅ | string | 所属顶层实验室（对应 labs.yaml 的 name，如 "Stanford AI Lab"） |
| `source_url` | ✅ | string | 采集该人员的列表页 URL |
| `source_detail_url` | 可选 | string | bio 详情页 URL（若 agent 进了详情页） |
| `photo_url` | 可选 | string | 个人主页头像照片URL（从bio详情页或列表页提取） |
| `current_position` | 可选 | string | Alumni 专用：当前工作/去向（如 "腾讯，北京" 或 "后续深造"） |
| `collected_at` | ✅ | string | ISO8601 采集时间戳（如 "2026-06-29T11:04:00Z"） |

### `lab` 类型记录字段

| 字段 | 必填 | 类型 | 说明 |
|------|------|------|------|
| `type` | ✅ | string | 固定为 `"lab"` |
| `lab_name` | ✅ | string | 实验室中文/英文名 |
| `lab_slug` | ✅ | string | labs.yaml 中的 slug |
| `homepage` | ✅ | string | 实验室官网 |
| `description` | 可选 | string | 实验室简介（从首页 About/Intro 区块提取） |
| `research_focus` | 可选 | string | 实验室核心研究方向概述（如 "机器学习、数据挖掘、模式识别"） |
| `current_research_directions` | 可选 | array[string] | 当前具体研究方向的列表（如 ["集成学习", "半监督与主动学习"]） |
| `logo_url` | 可选 | string | 实验室 logo URL（供实验室卡片展示） |
| `collected_at` | ✅ | string | ISO8601 采集时间戳 |

## 关键规则

1. **提取不到的字段直接省略**——不写 `null`、不写空字符串、不猜测。
2. **name 必填**——缺 name 的条目必须丢弃。
3. **role_section + role_raw 双轨**：
   - `role_section` 来自页面分区（粗分类，用于 role_type 映射）
   - `role_raw` 来自 bio 详情页（精确头衔，用于展示）
   - 两者独立，列表页只有 role_section，进了 bio 才有 role_raw
4. **photo_url 默认收录**：从每个人员的 bio 详情页/个人主页提取头像照片URL，使用浏览器或HTTP请求找到页面上第一个非Logo/非导航的图片（尺寸>80px），记录其完整URL。不下载图片本身。
5. **lab_logo_url 不写入人员记录**：实验室 logo 是实验室级字段，不属于个人。为了让人才库导入时只需要一个 JSONL 文件，实验室级字段（`lab_logo_url`, `lab_homepage`, `lab_slug` 等）放在 JSONL 的第一行，记录类型为 `"type": "lab"`。人员记录保留 `lab_name`/`parent_lab` 作为外键关联，类型为 `"type": "person"`。
6. **cohort_year 只从明确表述提取**（"PhD since 2020"/"joined in 2021"），禁止从论文年份推断。提取到 cohort_year 必须同时填 cohort_source。
7. **lab_name vs parent_lab**：一个 SAIL 下有多个子实验室（NLP/SNAP/Ermon），parent_lab 始终是顶层实验室名；对于没有子实验室的单一实验室，`lab_name` 与 `parent_lab` 相同。

## 示例（一行 JSONL）

单个 JSONL 文件以 `"type": "lab"` 记录开头，后跟多个 `"type": "person"` 记录：

```json
{"type":"lab","lab_name":"Stanford AI Lab","lab_slug":"stanford_ai_lab","homepage":"https://ai.stanford.edu/","description":"Stanford AI Lab is...","research_focus":"Machine Learning, Computer Vision, NLP, Robotics","current_research_directions":["Reinforcement Learning","Graph Neural Networks","Foundation Models"],"logo_url":"https://ai.stanford.edu/static/logo.png","collected_at":"2026-06-29T11:04:00Z"}
{"type":"person","name":"Aryaman Arora","role_section":"PhD Students","role_raw":"PhD Candidate","homepage":"https://aryaman.io/","department":"Computer Science","cohort_year":2020,"cohort_source":"bio_detail:\"PhD since 2020\"","lab_name":"Stanford NLP Group","parent_lab":"Stanford AI Lab","source_url":"https://nlp.stanford.edu/people/","source_detail_url":"https://aryaman.io/","photo_url":"https://aryaman.io/photo.jpg","collected_at":"2026-06-29T11:04:00Z"}
```

## 输出文件

**仅输出一个 JSONL 文件**供人才库导入：`output/<lab_slug>/_YYYY-MM-DD.jsonl`。
文件第一行是实验室元数据记录，后续每行是一个人员记录。

## 质量校验（写完 JSONL 后自检）

- 第一行是 `"type": "lab"` 记录，必含 `logo_url` 和 `homepage`
- 后续每行是 `"type": "person"` 记录，每行是合法 JSON
- 每个 person 记录含 `name` 字段且非空
- 总人数 > 0

（用 `python -c "import json; [json.loads(l) for l in open('file.jsonl')]"` 检查 JSON 合法性）
