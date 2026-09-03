# Claim2Value 项目 GitHub 同步记录

> **用途**：记录每次推送到 GitHub 的内容，方便团队随时回看"哪些传过了、新增了啥"。
> **仓库**：https://github.com/aeiou0123/pku-financial-ai-agent
> **维护方式**：每次 `git push` 成功后，在表首追加一行；详细变更见各次提交说明。

---

## 同步总览表

| 日期 | 提交哈希 | 类型 | 一句话说明 | 推送状态 |
|---|---|---|---|---|
| 2026-08-30 | `0e72f01` | init | 项目初始化：README、TODO、研究报告、setup 脚本 | ✅ 已推送 |
| 2026-08-30 | `ca0b44a` | docs | 数据收集指南、清单、空白模板（主案例阶段） | ✅ 已推送 |
| 2026-09-01 | `0ef790e` | data | 三公司年报/招股书 7 份 PDF + 券商研报 11 份 PDF + 搜索报告 | ✅ 已推送 |
| 2026-09-01 | `76e1118` | data | 自动提取成果：专利 30 条、参数表、18 条 claim、行业/竞争数据 + 提取脚本 | ✅ 已推送 |
| 2026-09-01 | `cbff862` | docs | 更新收集清单状态和搜索报告（记录已完成替代方案） | ✅ 已推送 |

---

## 各次同步明细

### 2026-09-01 `cbff862` docs: 更新清单与搜索报告

**相对上一次新增/变更：**
- 更新 `data/collection_checklist.md`：专利/参数/claim 状态改为完成或部分完成
- 更新 `data/search_report.md`：新增"六、已完成替代方案"和"七、仍建议手动补充"

**未变化**：代码、PDF、processed 数据文件均未动。

---

### 2026-09-01 `76e1118` data: 自动提取专利、参数、claim、行业基准

**这是目前内容最充实的一次提交。新增文件：**

| 类别 | 文件 | 说明 |
|---|---|---|
| 专利 | `data/processed/patent_collection.json` | 三家公司 30 条专利（绿的 7 / 环动 15 / 步科 8） |
| 专利 | `data/processed/patent_collection.csv` | 同上，CSV 版 |
| 参数 | `data/processed/parameter_table_filled.csv` | 三公司+竞争对手参数对比（含来源标注） |
| 参数 | `data/processed/parameter_table_template.csv` | 由 filled 版覆盖更新 |
| Claim | `data/processed/claim_bank_filled.json` | 18 条结构化 claim（绿的 7 / 步科 5 / 双环 5 / 行业 1） |
| Claim | `data/processed/claim_bank_template.json` | 由 filled 版覆盖更新 |
| 行业 | `data/processed/industry_data_summary.csv` | 工业机器人销量、减速器需求、国产化率 |
| 行业 | `data/processed/competitor_market_share.csv` | 谐波/RV 减速器市占率 |
| 工具 | `src/data_tools/extract_patents.py` | 专利提取脚本（PDF 乱码时备用） |
| 工具 | `src/data_tools/extract_parameters.py` | 参数候选扫描脚本 |
| 工具 | `src/data_tools/extract_claims.py` | claim 候选扫描脚本 |

**同时更新**：`.gitignore`（忽略可再生的 txt 提取文件和中间候选文件）

**本地有但未上传**（gitignore 排除，可重新生成）：
- `data/raw/**/*.txt` — PDF 提取的文本
- `data/processed/*_candidates*.csv` — 421 条原始 claim/参数候选
- `data/processed/huandong_patents.*` — 招股书乱码导致为空的提取结果

---

### 2026-09-01 `0ef790e` data: 三公司年报与研报 PDF

**新增 PDF（7 份公司文件 + 11 份研报，共 18 份）：**

公司公告（`data/raw/company_filings/`）：
- 绿的谐波 2024 年报、2025 年报
- 步科股份 2024 年报、2025 半年报
- 双环传动 2024 年报、2025 半年报
- 环动科技科创板 IPO 招股书

券商研报（`data/raw/analyst_reports/`）：
- 绿的谐波 4 份（2025Q1×2、2024&2025Q1、2025 半年报）
- 步科股份 2 份（2025Q2、2025Q3）
- 双环传动 3 份（2025-01、2025-05、2025Q2）
- 行业研报 2 份（精密减速器专题、人形机器人关节设计）

**同时新增**：
- `data/search_report.md` — 如实记录找到/未找到的资料及技术限制
- `data/processed/buke_fmk_parameters.csv` — 步科 FMK 系列 10 个型号参数
- 每份 PDF 配套的 `.meta.json` 来源文件

---

### 2026-08-30 `ca0b44a` docs: 数据收集指南与模板（主案例阶段）

**新增**：
- `data/collection_checklist.md` — 数据收集总清单
- `data/search_guide.md` — 搜索策略指南
- `data/processed/` 下 4 个空白模板（claim_bank / parameter_table / bom / financial_model_inputs）

> 注：当时还是"绿的谐波单案例"阶段，后升级为三案例策略，清单已更新。

---

### 2026-08-30 `0e72f01` init: 项目初始化

**新增**：
- `README.md` — 项目介绍与克隆指引
- `TODO.md` — 五阶段任务列表
- `research_notes/` — 研究笔记
- `setup_research_env.bat` — 队友一键下载论文+参考仓库的脚本
- `.gitignore`

---

## 当前仓库结构快照（截至 2026-09-01）

```
pku-financial-ai-agent/
├── README.md                  ← 项目说明（队友先看这个）
├── TODO.md                    ← 任务清单
├── SYNC_LOG.md                ← 本文件
├── setup_research_env.bat     ← 环境初始化脚本
├── data/
│   ├── collection_checklist.md    ← 数据清单（含状态列）
│   ├── search_guide.md            ← 搜索指南
│   ├── search_report.md           ← 搜索报告（找到/未找到）
│   ├── raw/
│   │   ├── company_filings/       ← 7 份公司公告 PDF + meta
│   │   └── analyst_reports/       ← 11 份研报 PDF + meta
│   └── processed/
│       ├── claim_bank_filled.json     ← 18 条 claim
│       ├── parameter_table_filled.csv ← 参数对比表
│       ├── patent_collection.csv/json ← 30 条专利
│       ├── industry_data_summary.csv  ← 行业数据
│       ├── competitor_market_share.csv← 竞争格局
│       ├── buke_fmk_parameters.csv    ← 步科 FMK 参数
│       └── *_template.csv/json        ← 模板（部分已被 filled 覆盖）
├── src/
│   ├── case.py                ← 三案例抽象层
│   └── data_tools/            ← PDF 提取脚本×3
└── research_materials/        ← 论文/参考仓库（PDF 被 gitignore，脚本下载）
```

---

## 给团队的说明

1. **clone 后第一件事**：运行 `setup_research_env.bat` 下载论文和参考仓库（这两类文件不进 Git，因为太大）。
2. **PDF 都在仓库里**：年报和研报直接随仓库分发，clone 即可用。
3. **每次有新数据/代码提交**：我会在这个文件顶部追加一行记录，你们 `git pull` 后看这里就知道新增了什么。
4. **手动待补清单**：见 `data/search_report.md` 第七节，主要是官方 datasheet 和步科发明专利。
