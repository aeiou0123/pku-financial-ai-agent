# 项目书一致性审校报告

> 生成：`python scripts/audit_proposal.py`（机械审校，标红项需人工裁定）

## 1. 关键锚点数字跨章出现表

| 数字 | 含义 | 出现章节 | 状态 |
|---|---|---|---|
| 14.13 | 定增总额 | 04_case_study×2、05_business_case×1 | ✅ |
| 14.02 | 定增净额 | 04_case_study×2 | ✅ |
| 0.94 | 悲观EV | 03_product×1、04_case_study×5、05_business_case×1 | ✅ |
| 30.78 | 基准EV | 03_product×1、04_case_study×4、05_business_case×1 | ✅ |
| 58.50 | 乐观EV | 03_product×1、04_case_study×4、05_business_case×1 | ✅ |
| 512.96 | 市值 | 01_overview×1、04_case_study×6、05_business_case×2、08_compliance×1 | ✅ |
| 46.25 | base 2027营收 | 04_case_study×3、05_business_case×1 | ✅ |
| 1,293 | ASP2024 | 04_case_study×3 | ✅ |
| 1,099 | ASP2025 | 04_case_study×2 | ✅ |
| 1,500 | 券商ASP假设 | 04_case_study×5 | ✅ |

## 2. 溯源标签完整性（正文引用 vs 章末附录索引）

| 章节 | 正文引用标签 | 索引缺失 | 索引有而正文未引用 |
|---|---|---|---|
| 01_overview.md | C1, C2, C3, C4, C5, C6, C8 | — | — |
| 02_problem.md | C1, C2, C3, C4, C5, C6, C8 | — | — |
| 03_product.md | C— | — | — |
| 04_case_study.md | C1, C2, C3, C4, C5 | — | — |
| 05_business_case.md | C1, C2, C3, C4, C5, C6, C7, C8 | — | — |
| 06_roadmap.md | C2 | — | — |
| 07_team.md | C— | — | — |
| 08_compliance.md | C1, C2, C3, C4, C5, C6, C8 | — | — |
| 09_qa_playbook.md | C8 | — | — |

## 3. PR 编号引用

- `03_product.md` 引用 PR：[4, 8, 11, 15, 21, 26, 29]
- `04_case_study.md` 引用 PR：[15, 19, 20, 21, 28, 29]
- `05_business_case.md` 引用 PR：[28]
- `06_roadmap.md` 引用 PR：[4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 29]
- `07_team.md` 引用 PR：[2, 3, 4, 5, 6, 8, 9, 10, 11, 12, 13, 18, 26]
- `09_qa_playbook.md` 引用 PR：[17, 19, 20, 28]

## 4. 过时表述扫描


## 总结

- 机械审校标红/警告项共 **0** 处（含表格状态列 ⚠️）。
- 本报告只列疑点，逐项修改需人工确认后执行。
