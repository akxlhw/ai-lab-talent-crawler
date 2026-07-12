# 师生关系网络提取

本文件记录从实验室人员页面提取 "导师 → 学生" 关系的策略。索引关系是人才库网络分析的重要边，不应只依赖于通用的 bio 文本提取，而应该先利用网站内部已有的结构化数据。

## 优先级（按可靠性高低）

### 1. 结构化 JS 数组（最优）

很多实验室的人员页面会内嵌一个导师-学生映射的 JavaScript 数组，如 LAMDA 的 `teachers_students`:

```javascript
let teachers_students = [
  {
    name: "导师姓名",
    link: "http://...",
    introduction: "...教授, 博导",
    students: {
      doctors: [{name: "学生A", link: "...", year: "2022"}, ...],
      masters: [{name: "学生B", link: "...", year: "2023"}, ...]
    }
  },
  ...
];
```

**必须解析**：
- 从 HTML 中正则提取 `teachers_students\s*=\s*([\s\S]*?);\s*`
- 将 JS 对象转为 JSON/JSON5（给无引号的 key 加引号，删除尾随逗号）
- 建立 `student_name → advisor_name` 映射
- 将 `advisor` 写入该学生的所有记录（在读博士、在读硕士、Alumni 等）

### 2. 表格中的 Advisor 列（如 statsml）

某些实验室人员使用表格展示学生，其中有明确的 `Advisor` 列：

| Name | Year | Advisor | Department |
|------|------|---------|------------|
| Alice | 2020 | Prof. X | CS |

**提取方法**：
- 使用 `document.querySelectorAll('table tr')` 一次性提取
- 第一行通常是表头，应跳过

```javascript
Array.from(document.querySelectorAll('table tr')).slice(1).map(row => {
  const cells = row.querySelectorAll('td');
  return {
    name: cells[0]?.textContent.trim(),
    year: cells[1]?.textContent.trim(),
    advisor: cells[2]?.textContent.trim()
  };
});
```

### 3. 个人主页 bio 文本（最低优先级）

当结构化数据不存在时，从个人主页提取。常见表述：

- `Supervisor: Prof. Yang Yu`
- `under the supervision of Prof. De-Chuan Zhan`
- `advised by Prof. Zhi-Hua Zhou`
- `导师：周志华教授`

**常见困难和解决**：
- 姓名被 `<a>` 标签分割成多行：用 `document.body.innerText` 获取渲染后的纯文本，而不是 BeautifulSoup 的 `get_text()`
- 只拿到 "Professor" 碎片：设置清洁规则：
  1. 移除 "Professor" / "Prof." / "Associate Professor" 等称号
  2. 如果仅拿到称号无姓名，检查下一行
  3. 删除 "Major:", "Laboratory:", "Email:" 等后续增量文本
- 多个导师：分为 `advisor` 和 `co_advisor`

## 验证与合并

1. 结构化数组和 bio 文本同时提取时，如果出现冲突：
   - 结构化数组一般更可靠，作为主要值
   - bio 文本的不同名称作为 `co_advisor`
2. 同一导师不同形式的名字需要标准化（如 "Zhi-Hua Zhou" 和 "周志华" 应该保持页面原文，不强求统一）
3. 预置 advisor 字段不应出现在 Faculty/Director 记录上，除非他们也是当前学生的 advisor 映射（此时 role_section 也是 Faculty，但导师字段记录他们自己的博士导师，需牵东处理）

## 工具选择

| 场景 | 推荐工具 |
|------|---------|
| 结构化 JS/JSON | `curl` + Python regex + json/json5 |
| 表格 | `browser_console` JavaScript |
| 静态 bio 页 | `requests` + BeautifulSoup |
| 渲染后才有的 bio | Camofox `/evaluate` |
| 大规模个人页 | `ThreadPoolExecutor` + requests/urllib |
