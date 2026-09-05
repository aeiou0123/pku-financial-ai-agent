# Claim2Value 项目 GitHub 同步记录

> **用途**：记录每次推送到 GitHub 的内容，方便团队随时回看"哪些传过了、新增了啥"。
> **仓库**：https://github.com/aeiou0123/pku-financial-ai-agent
> **维护方式**：每次 `git push` 成功后，在表首追加一行；详细变更见各次提交说明。

---

## 同步总览表

| 日期 | 提交哈希 | 类型 | 一句话说明 | 推送状态 |
|---|---|---|---|---|
| 2026-09-05 | `cbc0f1d` | feat | 核心验证引擎：state_verifier + evidence_ledger + claim_verifier + workflow + pipeline 评估报告 | ✅ 已推送 |
| 2026-09-04 | `360f68c` | benchmark | Claim 验证 benchmark 全套：mutation 考卷 98 用例 + 双模型评估 + Oracle 自我修正 + 判别力报告 | ✅ 已推送 |
| 2026-09-01 | `1b13e10` | team | 新增协作者 FeishengLuo（write 权限），团队表更新为 3 人 | ✅ 已推送 |
| 2026-09-01 | `026afca` | team | 新增协作者 shushuyang231（write 权限）+ 更新 README 协作指南 | ✅ 已推送 |
| 2026-08-30 | `0e72f01` | init | 项目初始化：README、TODO、研究报告、setup 脚本 | ✅ 已推送 |
| 2026-08-30 | `ca0b44a` | docs | 数据收集指南、清单、空白模板（主案例阶段） | ✅ 已推送 |
| 2026-09-01 | `0ef790e` | data | 三公司年报/招股书 7 份 PDF + 券商研报 11 份 PDF + 搜索报告 | ✅ 已推送 |
| 2026-09-01 | `76e1118` | data | 自动提取成果：专利 30 条、参数表、18 条 claim、行业/竞争数据 + 提取脚本 | ✅ 已推送 |
| 2026-09-01 | `cbff862` | docs | 更新收集清单状态和搜索报告（记录已完成替代方案） | ✅ 已推送 |

---

## 各次同步明细

### 2026-09-04 `360f68c` benchmark: Claim 验证 benchmark 框架（孙圣尧）

这是**代码层的第一次实质提交**。此前仓库只有数据，没有任何可执行代码；本次建立了
「用 mutation testing 检验 claim verifier 判别力」的完整评测链路。

**新增目录 `benchmarks/`（9 个文件）：**

| 文件 | 说明 |
|---|---|
| `mutate.py` | 6 类扰动生成器：19 条真实 claim → 98 个测试用例 |
| `fix_oracle.py` | Oracle 修正：从参数表提取真实数值注入 evidence，修正 expected_verdict |
| `evaluate.py` | LLM-as-judge 评估器：多模型对比、断点续传、超时不计失败 |
| `report.py` | 报告生成器：判别准确率、按扰动类型分解、失败模式拆解、v1/v2 对比 |
| `claim_verification.json` | 原始考卷（98 用例） |
| `claim_verification_v2.json` | Oracle 修正后考卷（推荐用这份） |
| `report.md` | **判别力评估报告，可直接用于比赛材料** |
| `results/evaluation_results_v1.jsonl` | 首轮评估结果（69 用例，修正前，作为对照） |
| `results/evaluation_results_v2.jsonl` | 扩充后双模型评估原始数据（196 次调用） |

#### 核心结果（98 用例 × 2 模型）

| 指标 | claude-sonnet-5 | gpt-5.5 |
|---|---|---|
| 判别准确率 | 62.5% | 65.3% |
| 被骗过（太轻信） | 17 | 17 |
| 过度拒答（太保守） | 3 | 5 |
| 错且自信率 | 35% | 35% |

按扰动类型的判别准确率：

| 扰动类型 | sonnet5 | gpt5.5 | 判断 |
|---|---|---|---|
| 证据缺失 | 100% (19题) | 100% (19题) | 诚实性满分 |
| 数值篡改 | 93% (15题) | 88% (16题) | 较强 |
| 来源降级 | 71% (17题) | 59% (17题) | 中等 |
| 时间错位 | 70% (10题) | 70% (10题) | 中等 |
| 限定词删除 | 32% (19题) | 42% (19题) | **系统性盲区** |
| 口径偷换 | 12% (16题) | 35% (17题) | **系统性盲区** |

#### 三个可直接用于比赛材料的结论

1. **当前最强 LLM 做金融 claim 验证仍不可靠**：能抓明显的假（数值篡改 93%）、
   能在无证据时拒答（100%），但对**精细的假**几乎无抵抗力——口径偷换只有 12-35%，
   限定词删除只有 32-42%。
2. **失败模式以「被骗过」为主而非「过度拒答」**：两个模型各被骗过 17 条，
   过度拒答仅 3-5 条。模型偏轻信，且判错时置信度仍很高（错且自信率 35%）。
3. **「口径偷换」是最危险的盲区**：模型分不清额定扭矩/峰值扭矩、毛利率/净利率、
   归母净利润/扣非净利润。这在金融场景会导致估值量级错误——
   这正是 Claim2Value 需要独立验证层的理由。

#### Oracle 自我修正（方法论亮点）

首轮评估发现 benchmark 自身的 oracle 存在缺陷：部分用例的 expected_verdict
假设了模型不可见的证据（只给来源名未给原始数值），导致模型合理拒答被误判为 miss。
修正后过度拒答从 11-12 条降到 3-5 条。

**这是 Oracle Mutation Testing 方法论的自我应验——benchmark 的评判标准本身也需要被验证。**
建议在项目书中作为「评测可信度」的论据展示。

#### 给队友的使用方式

- **Chen Luodi**：`claim_verification_v2.json` 可直接当 verifier 模块的验收考卷。
  跑法：`python benchmarks/evaluate.py --cases benchmarks/claim_verification_v2.json --models <你的verifier>`
  分数就是代码质量的客观度量，不用等人工评审。
- **西交经济/金融成员**：`report.md` 里的数字是「落地价值 40%」的弹药，
  尤其是口径偷换 12-35% 这条——建议配一个真实的财务口径混淆导致估值错误的案例。
- **电气/机械成员**：请核对工程类用例（额定/峰值扭矩、扭矩密度、LHS-32/SHPR-20E 参数）
  的 expected_verdict 是否符合工程常识。你们是 ground truth 的裁判。

#### 运行方式

```bash
# 1. 生成考卷（不需要 API）
python benchmarks/mutate.py          # 19 claim -> 98 用例
python benchmarks/fix_oracle.py      # 注入真实参数，修正 oracle

# 2. 跑评估（需要 Prism 网关 key）
python benchmarks/evaluate.py --models claude-sonnet-5 gpt-5.5

# 3. 出报告（不需要 API）
python benchmarks/report.py
```

**注意**：`evaluate.py` 不硬编码任何 API key，运行时从 `~/.workbuddy/models.json`
或工作区 `prism_config.json` 读取。**密钥不入库**，请勿提交带 key 的配置文件。

---

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
