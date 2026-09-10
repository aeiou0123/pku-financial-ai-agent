# Claim2Value 项目 GitHub 同步记录

> **用途**：记录每次推送到 GitHub 的内容，方便团队随时回看"哪些传过了、新增了啥"。
> **仓库**：https://github.com/aeiou0123/pku-financial-ai-agent
> **维护方式**：每次 `git push` 成功后，在表首追加一行；详细变更见各次提交说明。

---

## 2026-09-10 说明文档 v3：按用户逐条反馈修订（K3）

- **删除**：合规边界章（内容并入反向 DCF 章末一句 + 附录免责声明）；路线图章只留图，删掉图后文字段。
- **真实性修正（重要）**：工程可信度章 benchmark 数字从"修复前 83.7%/82.7%"（只见于 SYNC_LOG 历史中间态）改为现报告口径——`benchmarks/pipeline_report.md`：裸 LLM 62.5%/65.3% → 规则层+LLM 91.8%/90.8%，规则层误伤 0。工程可信度表新增"来源"列，每个指标对应可实跑验证的文件/命令。
- **图修复**：TAM/SAM/SOM 重构（描述移到条带右侧，注释与条带分离，消除重叠）；反向 DCF 图从 pgfplots 改为 matplotlib 重画（原图 512.96 标签与边框重叠、市价行标签被裁）；RV 锚点图标签微调。
- **排版**：补 `indentfirst`（每章首段现在正确缩进）；正文去掉代码标识符（`python app.py`、`run_financial_chain` 等只留在附录运行方法）；减少防御性括号声明。
- **新增第 3 章"智能体本体"**：输入输出、双轨验证与降级路径、证据账本与人机分工（五字段硬门控）、能力边界，以及与赛事评分维度（技术创新 30%/落地价值 40%/商业潜力 30%）的对照表。
- **封面重设计**：编辑式左对齐排版 + 底部统计行，去掉链条 motif。
- PPT 本轮不动（用户改用网页端 AI 基于 PDF 制作）。

---

## 2026-09-10 提交文档深度去 AI 味重做（PDF v2 + PPT v3）

针对"文档/PPT AI 味重、图表错位重叠、图表数量不足"的反馈，按诊断清单重做：

- **7 张真实数据图**（`deliverables/latex/make_figs.py` 生成，PDF+PNG 双格式）：ASP 假设击穿（1500 vs 1293/1099）、11 家公司 Claim 验证堆叠图、因果批判前后置信度、RV 均价锚点（2533–3209 实际 vs 修正前 4300 vs 修正后 3100）、StateVerifier 修复前后准确率、TAM/SAM/SOM 示意带、路线图。每张单独视觉 review，修复了置信度图口径误导（宣称置信度与假设置信度混连）、TAM 图 SAM 无数字却满轴、路线图文字跨栏重叠、图例压柱四个问题。
- **说明文档 v2**（`claim2value_doc.tex`）：全文按"说人话"规则重写——删掉全部金句收尾、排比脚手架、粗体领起压缩句、"不是 X 是 Y"、插入式自诩；封面去掉链条 motif 改克制排版；语气改为分析师备忘录式平实陈述，事实与数字不动。
- **路演 PPT v3**（`claim2value_pitch.tex`）：去掉 chip 徽章、stat card 堆砌、金句 tagline、链条 motif、四象限卡片；每页一个核心信息 + 真实数据图；标题直陈事实。

---

## 2026-09-10 提交物质量重做：LaTeX 说明文档 + Beamer 路演 PPT（K3）

针对"PDF 简陋、PPT 渲染弱、AI 味重"的反馈，提交物整体升级为 LaTeX 原生排版：

- **说明文档**（`deliverables/latex/claim2value_doc.tex` → `Claim2Value_项目说明文档.pdf`）：ctexrep + 品牌定制样式（藏青/金/冰蓝），定制封面页、目录、TikZ 流水线图、pgfplots 反向 DCF 对照图、tcolorbox 要点框、14 页。内容从项目书 01–08 章扩写，写作按"说人话"规则去模板腔。编译零错误，逐页视觉 QA 一轮（修复大数字表格错位、柱状图标签裁切）。
- **路演 PPT**（`deliverables/beamer/claim2value_pitch.tex` → PDF + 图像版 PPTX）：Beamer metropolis 主题改品牌色，公式原生渲染，12 页结构与 `11_pitch_outline.md` 一致。
- **封面提示词**（`deliverables/cover_prompt.md`）：ChatGPT image 双版本提示词（含文字版 + 纯图形版），品牌色号与链条 motif 指定，供人工生成后替换 `cover_16x9.png`。
- `.gitignore` 补 LaTeX 中间文件与 QA 渲染图。

---

## 2026-09-10 BigQuant 提交材料分类定稿（K3）

按用户提供的「提交作品」表单截图，把提交素材重写为逐字段可复制版：

- `deliverables/submission_form.md` 重写：项目名称（28/30 字）、一句话摘要（45/60 字）、公开介绍（287/500 字）、核心创新点 5 条逐条可粘贴、封面/作品文件上传对照表、团队展示名称候选；保留团队成员信息表与评分维度展开段落备答辩用。
- `work/code_submission/`（不入库）：AIStudio 代码提交暂存包——app.py + src/ + tests/ + scripts/ + README/requirements + claim bank 与 ontology JSON + 模型输入，共 35 个文本文件 565K，附拟好的「提交描述.txt」（含 GitHub 链接）。
- 表单操作的剩余人工动作：粘贴各字段、上传封面/PPT/PDF、AIStudio 上传代码文件并勾选提交、决定团队展示名称、录屏后补传演示视频。

---

## 2026-09-09 大赛提交包：PPT + 封面 + 说明文档 PDF + 表单素材（K3）

按 BigQuant 提交要求（必填：项目名称/摘要/公开介绍/核心创新点/团队名称/16:9 封面；可选附件：Demo/核心代码/演示视频/PPT/PDF 说明文档）完成提交材料包，全部数字与 PR #28/#29 后口径一致：

- `deliverables/Claim2Value_pitch.pptx`：12 页路演 PPT（按 `11_pitch_outline.md` 用 pptxgenjs 生成，构建脚本 `deliverables/build_deck.js` 同仓可复现；经 PowerPoint→PDF→逐页视觉 QA，修复了 P9 漏斗文字遮挡问题）；
- `deliverables/cover_16x9.png`：1920×1080 项目封面（与 PPT 同一视觉语言）；
- `deliverables/Claim2Value_项目说明文档.pdf`：十章说明文档（pandoc + xelatex + 微软雅黑渲染）；
- `deliverables/submission_form.md`：BigQuant 网页表单可复制素材（按技术创新 30%/落地价值 40%/商业潜力 30% 评分维度组织）；
- `deliverables/team_and_sources.md`：团队成员与公开资料索引（团队名称留待人工填写）；
- `deliverables/SUBMISSION_PACKAGE_README.md`：提交包说明与运行指引；
- `work/Claim2Value_submission_staging_20260909/`：BigQuant 上传用暂存副本（`work/` 已加入 .gitignore，不入库）。
- 07 章团队页更新：Chen Luodi 角色描述补全（教育背景以正式报名材料为准）。
- 回归 `pytest` 140 passed、`audit_proposal.py` issues=0。

**剩余人工项**：① 团队名称填入表单并提交 BigQuant；② 演示视频真人彩排录屏（脚本 `docs/proposal/10_demo_script.md`）；③ 4 条待验证 Claim 的厂商 datasheet（绿的 LHS-32：leaderdrivecn.com/download/30.html 有官方样本下载页；环动 SHPR-20E：建议联系厂商索取选型手册）。

---

## 2026-09-09 15 条 Claim 官方来源机器预检 + 模型参数复核（K3）

本轮由 K3 把两项"人工待办"的检索与对照部分完成，产出两份报告，**不改动任何 claim 状态与模型数值**，确认动作留给人：

- **15 条待验证 Claim 预检**（`docs/proposal/appendix_precheck_report.md`）：自建巨潮资讯网（cninfo）公告检索/PDF 下载/文本比对管线，逐条核对官方原文。结果：**10 条数值与官方原文逐字一致（建议升级已验证）、1 条（SH_003）数值一致但研报把"2025H1 累计"误标为"Q2 单季"（建议修正口径后升级）、4 条维持待验证**（BK_001/BK_003/GH_007/SH_002，附已尝试路径与驳回理由）。亮点发现：SH_003 是"口径偷换检测"价值的现成案例；QC_004 在巨潮找到公司投资者关系活动记录表原文（编号 2023-02），证据等级可升。
- **模型参数复核**（`docs/proposal/model_param_review.md`）：以官方披露为锚点逐项对照两家模型输入与 ontology 弹性系数。关键锚点：绿的谐波系高新技术企业实际税率 15%（模型用 25%，偏保守）；绿的 2024 实际毛利率 36-37.5% vs 模型隐含 49.6%（偏乐观）；环动科技招股书 RV 实际均价 2,653-3,209 元/台 vs 双环模型 ASP 4300 元（偏高约 40%，RV 成本假设需同步下修）；weight→unit_cost 弹性 0.5 建议降至 0.2-0.3。WACC 10%、永续增长 3%、双环税率 15% 等通过。
- **后续人工动作**：① 抽读预检报告中的官方链接确认后，用 `claim_bank_writer.py` 升级 10+1 条（51 条将变为 46 已验证/4 待验证）；② 经济金融组按复核报告决定改数或仅补 Q&A 口径；③ 若改数需重跑回归并更新 `10_demo_script.md` 口播数字；来不及则按报告第五节"最小动作"只补 `09_qa_playbook.md`。

---

## 2026-09-09 15 条 Claim 终验确认写回（K3 预检 + 用户确认，47/4）

用户抽读预检报告并确认后，执行写回：

- **11 条升级"已验证"**（`claim_bank_writer.py` 写回官方证据 11 条，`evidence_level=official_filing`，来源全部为巨潮资讯网公告原文 PDF 直链）：WZX_002/003/004、BST_002/004、HLYY_002/003/004、GM_004、QC_004。
- **SH_003 口径修正后升级**：研报"2025Q2 单季 3.49 亿 +35.8%"实为 2025H1 半年累计误标，按双环 2025 半年报 p.14 修正为"2025H1 累计 3.49 亿、+35.66%"后升级——"口径偷换检测→官方原文纠偏"的完整实证案例。
- **4 条维持待验证**：BK_001/BK_003（官方从未披露该数值）、GH_007/SH_002（需厂商 datasheet，附录已写明下一步路径）。
- **口径同步**：51 条 = **47 已验证 / 4 待验证**；`appendix_pending_review.md` 重新生成；README、03/04/06 章、09/10 章、KIMICODE_PROGRESS、TODO 全部同步。
- 回归 `pytest` 140 passed、`audit_proposal.py` issues=0。

---

## 2026-09-09 模型参数修正落地与全仓数字重跑（K3，用户已确认"改参数重跑"）

按 `docs/proposal/model_param_review.md`（PR #27）的建议，经用户确认后落地修正并重跑全链路：

- **参数修正**：① 双环 RV 线按环动科技招股书（2024-11 申报稿）实际均价锚定——ASP 4300→3100 元、单位成本 2900→2000 元（毛利率对齐 35-42% 实际区间下沿）、销量 19/24/30→22/27/33 万台（保持与 2025H1 收入年化口径一致）；② 绿的谐波税率 25%→15%（2024 年报"高新技术企业减按 15%"原文）；③ 绿的谐波单位成本 580→730 元（按 2024 年报谐波减速器及金属件毛利率 36.13% 锚定）；④ 两份 ontology 的 weight→unit_cost 弹性 0.5→0.25（招股书披露钢材 6-7 元/kg，材料成本占比低）。
- **重跑结果（新口径，全部实跑得出）**：绿的独立模型三情景 EV **0.94 / 30.78 / 58.50 亿**（悲观情景量价成本三向挤压下 FCF 转负、EV 趋零，为如实呈现）；绿的 Demo 链（含批判层调整）**15.77 / 43.42 / 69.36 亿**；双环链 **19.04 / 72.66 / 122.89 亿**；反向 DCF 市价 512.96 亿隐含销量倍数 **16.66×**（三情景 gap -94.00% / -88.60% / -99.82%）。差距拉大而非缩小——说明修正前假设偏乐观，证据锚定的修正方向正确。
- **回归与审校**：`python -m pytest tests -q` 140 passed（修正了 golden file `green_harmonic_model_results.json` 重生成）；`audit_proposal.py` issues=0（KEY_FIGURES 锚点同步更新）；演示脚本/路演大纲/04/05 章/Q&A 预案/README 的口播数字全部同步为新口径。
- **注意**：`10_demo_script.md` 的录屏清单与台词数字已更新，彩排前仍需按 checklist 实跑核对一次。

---

## 2026-09-08 本地终验与说明文件对账（`b188c33`，已推送到 fork）

本轮按 Phase 3D 收尾顺序完成了本地复核，未改变合作者已合并的核心代码：

- **测试基线恢复**：`requirements.txt` 补充 `pytest`；`python -m pytest tests -q` 为 **140 passed**。
- **模型链路复核**：UTF-8 文件方式验证双环传动显式 `target_company="双环传动/环动科技"`，产生 3 条定量经济假设，产品线为 `gear/rv`，无 errors；三情景 EV 为 **5.8755 / 10.9412 / 0.4410 bn**（base/upside/downside）。此前 `n_quantitative=0` 是 PowerShell 中文内联输入编码造成的假象，未发现需要修改映射逻辑的代码缺陷。
- **Demo 与工程校验**：绿的谐波 `python app.py` 离线 Demo、双环传动本地全链路、`python -m compileall -q src benchmarks scripts app.py`、`python scripts/audit_proposal.py`（`issues=0`）和 `git diff --check` 均通过。
- **Claim 证据口径**：15 条待验证 Claim 仍保持待验证；本轮复核确认 WZX_002/WZX_003/HLYY_002 的媒体转述证据不应标作 `official_filing`，已降为 `news_media`，没有擅自升级任何 Claim。
- **说明文件对账**：README、TODO、`data/README.md`、数据收集/搜索说明、项目书 03/06/07 章、终验附录和 Kimi Code 进度入口已统一为 51 条 Claim（36 已验证/15 待验证）、140 项测试、Phase 3D 完成/答辩待命；历史提交记录保留原始日期与当时数字。

**仍待人工处理**：15 条 Claim 的原始官方证据终验；经济金融组对销量、ASP、BOM、税率、WACC、永续增长率及 RV ontology 弹性系数的复核；按 `10_demo_script.md` 完成真人彩排和录屏。上述事项不阻塞当前离线 Demo 与原型链路。

本条记录随本轮说明/证据口径修改一并提交，已推送到 fork 的 `main`。

---

## Phase 3D 收尾——演示作战包 + 终验清单 + 全局对账（2026-09-07，PR #23–#26）

### 总览（4 个模块，分 PR 合并保证质量）

| PR | 模块 | 内容 | 验证 |
|---|---|---|---|
| #23 | README 现状重写 | "当前进展"重写为 Phase 3C 五块现状；公司表扩至 11 家（含环动科技并入双环的口径说明）；"当前任务"指向待办 | 140 passed |
| #24 | 演示作战包 | `10_demo_script.md`（3 分钟口播 + 1 分钟 fallback + 录屏清单，全部基于 `python app.py` 与双环链路 2026-09-07 实跑）；`11_pitch_outline.md`（12 页路演大纲）；**修复 latency_report 被 smoke test 覆盖的根因**（`benchmark_latency.py` 加 `--out`、测试改 tempfile），C7 口径统一 N=30 p50 4.3ms/p95 5.0ms | 140 passed |
| #25 | 终验清单 | `appendix_pending_review.md`：15 条待验证 Claim 按公司分组（绿的1/步科2/双环2/五洲3/贝斯特2/恒立3/国茂1/秦川1）+ 终验操作指引（通过→改已验证补官方来源；驳回→notes 写理由） | 140 passed |
| #26 | 全局终检 | 六模块一致性 review（README↔04 章数字、05/09 章引用、PR 表对账 git log）；06 章 PR 表补 #22–#26；SYNC_LOG/KIMICODE_PROGRESS/TODO 三处进度同步 | 140 passed + 审校 0 |

### 当前状态快照

- Claim Bank：51 条 / 11 家公司 / 36 已验证 / 15 待验证（终验清单已备）
- 测试：140 passed；项目书审校：issues=0
- 估值链：2 家公司全链路实证（绿的、双环）；反向 DCF implied 8.54×
- **Phase 3D 完成，进入答辩待命**：剩余人工项 = ①15 条终验 ②演示彩排（脚本已备）③赛后实时检索
- 远程过时分支建议删除（需合作者确认）：`feat/workflow-financial-chain`、`fix/state-verifier-false-positives`

---

## Phase 3C 多公司扩展 + 答辩作战包（2026-09-07，PR #18–#22）

### 总览（4 个模块，分 PR 合并保证质量）

| PR | 模块 | 内容 | 验证 |
|---|---|---|---|
| #18 | 延迟基准 | `scripts/benchmark_latency.py` N=30 实测：p50 3.9ms/p95 4.6ms（无 LLM/无网络，AMD 台式机）；回填 05 章 [C7]（与合作者 880ms 双机并列） | 132 passed |
| #19 | 反向 DCF | `reverse_dcf()`：市价 512.96 亿隐含销量预期 ≈ base 假设 **8.5 倍**，三情景距目标 -88.3/-83.1/-93.7%；EV 与市值差距从软肋变成产品输出 | 136 passed |
| #20 | 双环全链路 | 估值链移植第二家公司：`financial_model` 多产品线泛化（自动识别 product lines）+ 规则级 `product_line_scope` + 双环 ontology 变体 + e2e 测试；三情景 EV 5.88/10.94/0.44 亿元；纳博 RV-20E 行因 PDF 列错位降级移出基准池 | 140 passed |
| #21 | Claim Bank 扩展 | 19→**51 条**（+8 家公司 32 条：中大力德/鸣志/柯力/五洲新春/贝斯特/恒立/国茂/秦川），36 已验证/15 待验证；年报逐字核对的标已验证，媒体转述标待人工终验 | 140 passed |
| #22 | 文档汇总 | 04 章（51/36 更新+第二案例+反向 DCF 进摘要）、06 章 PR 表补 #16–#21、03/01/08 章过期数字修正、新增 `09_qa_playbook.md`（8 题答辩预案） | 140 passed + 审校 0 |

### 过程中抓到并修掉的真实问题（答辩可讲）

1. 纳博特斯克 RV-20E 抽取错位行污染同业基准 → 降级 not_comparable，宁可缺样本不污染基准；
2. RV 重量劣势曾跨产品线把齿轮成本上调 24.6% → 规则级 product_line_scope 修复；
3. scope 被同变量复合增量绕过的二阶 bug → 增量按生效规则逐指标复合。

### 当前状态快照

- Claim Bank：51 条 / 11 家公司 / 36 已验证 / 15 待验证
- 测试：140 passed；项目书审校：issues=0
- 估值链：2 家公司全链路实证（绿的、双环）
- 下一步遗留：演示脚本/PPT 大纲（10/11 章未写）、15 条待验证人工终验、live 检索

---

## 项目书 Phase 3A 提质（2026-09-06，PR #16）

### 新增/变更

| 文件 | 内容 |
|---|---|
| `scripts/audit_proposal.py` | 新增项目书机械审校脚本：10 个关键锚点数字跨章比对、[C1]–[C8] 溯源标签正文引用 vs 章末索引比对、PR 引用扫描、过时表述扫描；输出 `docs/proposal/audit_report.md`，当前 issues=0 |
| `docs/proposal/04_case_study.md` | 重心章升级：摘要/诚实说明 5→**14 条已验证**（按公司分组列 Claim ID：绿的 6 + 步科 3 + 双环 4 + 行业 1）；新增示例三（GH_002 双源互证）、示例四（BK_004 双源逐字）、示例五（SH_005 产能利用率 101.30% 呼应 4.3.2）；StateVerifier 结论同步为 14 已验证/5 待验证；附录新增 [C1]/[C2] 两行索引 |
| `docs/proposal/06_roadmap.md` | PR 表补 #14/#15 行；M1 改"5 条待验证补验"；未完成项如实标注；基线更新 `c2df0f4` |
| `docs/proposal/03_product.md` | 产品状态表述同步 14 条已验证 Claim（PR #11/#15） |
| `docs/proposal/05_business_case.md` | 附录索引补 [C7] 占位行（效率实测，待人工采集），消除索引缺口 |
| `docs/proposal/01/02/06/08` | 各章末加溯源标签全局索引指引行（指向第 4 章章末 C1–C5 与第 5 章附录 C6–C8） |
| `data/processed/claim_bank_filled.json` | SH_003 notes 补复核结论：项目书未引用该数字，无正文风险；后续引用一律以官方半年报 H1 累计口径为准，不采用研报"Q2 单季 +35.8%"标注 |

### 纠错说明（重要）

- 此前 SYNC_LOG PR #15 节与 `docs/KIMICODE_PROGRESS.md` 误写"12 条已验证"，**实为 14 条**（PR #15 合并时实测 claim_bank_filled.json：GH_001–006 + BK_002/004/005 + SH_001/004/005/006 + IND_001）。本次已一并修正，审校脚本新增"12 条已验证"过时表述扫描防复发。

### 验证

- `python scripts/audit_proposal.py` → issues=0（锚点数字 10 项跨章全部一致；溯源标签索引无缺失）
- `python -m pytest tests/ -q` → **129 passed**

---

## Kimi Code 任务进度记录文档（2026-09-06，直接推送 main）

### 新增

| 文件 | 内容 |
|---|---|
| `docs/KIMICODE_PROGRESS.md` | K3 全部任务进度记录：当前状态 30 秒快照、PR #2–#15 历史表、待办与风险（C7 实测/SH_003 口径疑点/5 条待验证 Claim）、K3↔K2.7↔团队协作工作流图、快速验证入口。供团队成员随时确认进度。 |

---

## 14 条 Claim 核验回填（2026-09-06，PR #15）

### 变更（`data/processed/claim_bank_filled.json`，19 条 Claim 中 17 条现带证据）

4 个并行核验代理对剩余 14 条 Claim 逐条溯源（官方年报/招股书/半年报原文 txt 逐字命中 + 券商研报互证），写回 17 条证据记录（含 source/locator/excerpt/caliber/verified_at/fingerprint），主代理质检全部数值连续串命中验证。

### 逐条结论

| claim_id | 结论 | 来源 + 页码 | 差异/口径说明 |
|---|---|---|---|
| GH_001 | 已验证 (0.9) | 绿的 2024 年报 p10 | 原文主体为谐波减速器非关节模组，caliber 已注明 |
| GH_002 | 已验证 (0.85) | 年报 p39 表 + 国信研报互证 | 246,501 台/16.56%；PDF 表格列错位已在 caliber 说明 |
| GH_003 | 已验证 (0.95) | 年报 p11 | 达产口径 |
| GH_004 | 已验证 (0.9) | 年报 p21 | — |
| GH_007 | 待验证 (0.7) | 仅国金研报图表 46 | 待官方 datasheet |
| BK_001 | 待验证 (0.7) | 仅群益研报引蓝皮书 | 待官方 datasheet |
| BK_003 | 待验证 (0.7) | 半年报 p16 证实第四代 FMK 存在 | "22%" 全文本地文本不存在，待官方 datasheet |
| BK_004 | 已验证 (0.95) | 年报 p14 + 半年报 p15 双源逐字 | — |
| SH_001 | 已验证 (0.9) | 招股书 1-1-22 页 GGII 转引 | 10.11%→18.89% |
| SH_002 | 待验证 (0.65) | 仅国金研报图表 65 | PDF 抽取列错位，待复核 |
| SH_003 | 待验证 (0.5) | 民生研报 vs 双环 2025 半年报 p14 | **口径疑点**：研报称 2025Q2 单季 3.49 亿/+35.8%，但半年报 p14 显示 H1 半年累计 = 348,990,082.38 元 ≈ 3.49 亿，疑研报把累计数标成单季，交付报告需重点提示 |
| SH_004 | 已验证 (0.9) | 招股书 1-1-108 客户名单 | — |
| SH_005 | 已验证 (0.9) | 招股书 1-1-115 | 产能利用率 101.30% |
| IND_001 | 已验证 (0.9) | 招股书 p95 GGII 转引 | CAGR 数值自洽 |

### 说明

- verifier 字段统一"经济金融组复核"；人工终验机制 = 用户 review PR 时逐条核对 excerpt 与源文件。
- 回归测试 129 passed（`test_claim_count_unchanged_on_real_bank` 适配真实 bank 已带证据的状态，断言改为"只新增 1 条"）。
- 04 章可引用的已验证 Claim 从 3 条扩到 14 条（绿的 6 + 步科 3 + 双环 4 + 行业 1），产业链维度更完整。
- 剩 5 条待验证：GH_007/BK_001/BK_003/SH_002 待官方 datasheet，SH_003 待口径复核。

---

## 项目书七章正文展开（2026-09-06，PR #14）

### 变更（`docs/proposal/`，七章 stub → 正文初稿）

| 文件 | 内容 | 行数 |
|---|---|---|
| `01_overview.md` | 第 1 章概述：一句话定位、痛点-方案-证据三幕结构、全书导航，数字与第 5 章同源 | 97 |
| `02_problem.md` | 第 2 章问题定义：三类用户画像（卖方/买方/产业分析师）、四步痛点实例化、四大缺口详述、SAM 需求侧论证 | 121 |
| `03_product.md` | 第 3 章产品方案：三种产品形态、四层流水线架构图（采集→Pipeline→Claim Bank→输出）、规则层/LLM 层分离决策、19 条 Claim 状态如实标注 | 116 |
| `04_case_study.md` | **第 4 章案例研究（重心章）**：绿的谐波全链路演示——12 条 Claim 分组验证（GH_005/GH_006/BK_002 已验证条目页码级引用）、证据链推理展示、"券商 1500 元 ASP 假设 vs 实际 1293 元"击穿洞察、三情景估值对照市值 | 216 |
| `06_roadmap.md` | 第 6 章路线图：当前状态盘点（PR #5–#13 真实提交史）、0–6/6–18/18–36 月里程碑表、风险与未完成项如实标注 | 109 |
| `07_team.md` | 第 7 章团队：能力画像修正版（"验证派"定位）、成员分工与 PR 对应、协作机制（GitHub 实时共享） | 117 |
| `08_compliance.md` | 第 8 章合规：不触碰投顾红线（输出证据对照而非建议）、数据合规、可审计设计即伦理、AI 幻觉与人工复核纪律 | 107 |
| `README.md` | 章节表与实际文件名对齐（原 02_technical/07_financials/08_risk_compliance 旧命名已更正），状态改为"初稿完成" | — |

### 说明

- 全部数字跨章一致：定增总额 14.13 亿/净额 14.02 亿（两口径并列透明）、销量 25.17万→43.37万台（产量口径 [C5]）与 42.5万台（销量口径 [C4]）双口径并列、三情景 EV 32.16/60.06/86.50 亿与模型 JSON 一致。
- 04 章为重心章，Claim 引用全部来自 Claim Bank 已验证条目（含页码与指纹）；引用已验证条目标 [C4]/[C5] 为溯源笔记标签。
- 未竟事项不变：C7 效率实测（需人工）、剩余 14 条 Claim 核验回填（Phase 2）。

---

## 项目书骨架 + 第 5 章商业潜力初稿（2026-09-06，PR #13）

### 新增

| 文件 | 内容 |
|---|---|
| `docs/proposal/README.md` | 项目书 8 章骨架表 + 素材地图 + 写作纪律 |
| `docs/proposal/05_business_case.md` | **第 5 章完整初稿**（约 400 行）：摘要 / 5.1 TAM-SAM-SOM 三层漏斗（SAM 主推研究佣金比例法 = 198.65 亿 × 1–3% ≈ 2–6 亿/年，人头法/机构法交叉验证）/ 5.2 行业驱动力 / 5.3 竞争格局（含"券商降价假设已被实际 ASP 击穿"洞察）/ 5.4 客户与产能硬证据（含扩产延期 6.08% 风险）/ 5.5 估值对照（三情景原型 EV 32–86 亿 vs 市值 513 亿的诚实差距处理）/ 5.6 竞品定价与四大缺口 / 5.7 商业模式与定价建议（个人 1.2 万/团队 6–10 万/机构 20 万+三档，毛利 85%+ 假设）/ 5.8 风险对冲表 / 5.9 产品能力衔接 / 附录数据来源索引。所有数字标 [C1]–[C8] 溯源标签 |
| `docs/proposal/01–04、06–08` | 七章骨架 stub（每章 10–15 行：任务 + 建议结构 + 素材指针），待按本框架展开 |
| `research_materials/notes/commercial/sam_sizing.md` | C8 SAM 测算（上轮搜集完成、当时未推送）：分析师 5,776 人、券商研究佣金 198.65 亿元（-22.48%）、研报年产约 14 万份；SAM 主推佣金比例法 2–6 亿元/年 + 人头法/机构法交叉验证 |

### 说明

- 第 5 章所有数字全部来自已验收的 C1–C6、C8 搜集笔记，可直接溯源到本地 PDF 页码或网络来源。
- 未竟事项：C7 效率实测（需人工）；剩余 14 条 claim 核验；01–04/06–08 章节展开。

---

## Phase 2 商业素材搜集 C1–C6（2026-09-06，PR #12）

### 新增（全部位于 `research_materials/notes/commercial/`）

| 文件 | 任务 | 核心内容 |
|---|---|---|
| `market_size_extracts.md` | C1 本地PDF市场规模 | 环动招股书+国金+源达三份文本提取：工业机器人减速器中国市场 45.6 亿元/年（2023）、人形减速器百亿级增量（123-275 亿三档）、行星减速机全球 7.5→9.2 亿美元；每条带页码+原文摘录 |
| `humanoid_tam.md` | C2 人形TAM测算 | GGII/高盛/大摩出货锚点；三档测算：2030 年全球减速器 TAM 保守 71 亿/中性 356 亿/乐观 603 亿元，2035 年 1050-4394 亿元 |
| `valuation_anchor.md` | C3 估值锚 | 绿的谐波市值 512.96 亿、PE(TTM) 365.8、2026E 净利 1.92 亿（14 家机构一致预期）；EV↔市值对照方法 |
| `capacity_evidence.md` | C4 产能/客户证据 | 定增 20.27 亿募投"年产 100 万台谐波+20 万套执行器"一手公告锁定；IPO 5.46 亿投 50 万台项目；13 家客户名单（含优必选）；扩产进度 6.08% 延期至 2028（风险对冲素材） |
| `asp_analysis.md` | C5 ASP与价差 | 绿的谐波 ASP 1293→1099 元/台（连续两年 -15%）以价换量；环动 RV ASP 2533-3209 元序列；国产 RV 较品类价差低约 39% |
| `competitor_pricing.md` | C6 竞品定价 | Wind ~4万/账号/年（询价制）、慧博 8980-19980 元/年（唯一明码标价）、AlphaSense/Tegus 万美元级席位、LLM API 成本低 3-4 个数量级 |

### 说明

- 所有数字带来源（本地txt页码 / 网络链接+日期），未取得项与低可信度项均已明确标注，可直接供项目书"商业潜力"章引用。
- C7（效率实测）需人工参与，待团队安排；C8（SAM 测算）列入下一步。

---

## P1.3 Claim Bank 真实回填（2026-09-06，PR #11）

### 变更

- `data/processed/claim_bank_filled.json` — 5 条已验证 Claim（GH_005、GH_006、BK_002、BK_005、SH_006）完成真实证据回填，每条含来源文件+URL、页码定位、原文摘录、口径说明、核验人、evidence_level=official_filing、幂等指纹。
- `data/processed/evidence_records/p1_backfill_records.json` — 本次回填的 5 条证据原始记录（可复现、可审计，作为写回输入）。
- `benchmarks/pipeline_report.md` — 行尾统一 LF（原 CRLF）。

### 证据定位（全部官方披露原文）

| Claim | 来源 | 定位 | 关键数据 |
|---|---|---|---|
| GH_005 | 绿的谐波 2024 年报（巨潮） | 第 37 页 | 三年毛利率 48.69%/41.14%/37.54% |
| GH_006 | 绿的谐波 2025 年报（巨潮） | 第 7 页 | 营收 +47.31%、归母净利 +121.42% |
| BK_002 | 步科 2024 年报（上交所） | 第 14 页 | 机器人行业收入 21,242.55 万元，+12.26% |
| BK_005 | 步科 2025 半年报（上交所） | 第 13 页 | 归母净利 2,611.01 万元 +13.58%；扣股份支付后 3,602.56 万元 +42.27% |
| SH_006 | 双环传动 2024 年报（深交所） | 第 7 页 | 归母净利 1,023,911,091.96 元，+25.42% |

### 说明

- 核验人字段暂写团队角色"经济金融组复核"，团队可在复核后替换为真实姓名。
- 其余 14 条 Claim 仍为待验证状态，回填需先经人工核验。

---

## P1 收尾：claim_bank_writer 证据写回 + 端到端回归（2026-09-06，PR #9）

### 新增

- `src/claim_bank_writer.py` — 人工核验证据写回 Claim Bank 工具：每条证据强制五必填字段（claim_id/source/locator/excerpt/caliber + verifier），核验人字段为空即拒绝写入（`SKIP_EMPTY_VERIFIER` 硬门控）；指纹 `sha256(excerpt||source)[:16]` 幂等去重；先写临时文件再 `os.replace` 原子替换，写前自动 `.bak` 备份不覆盖旧备份；来源分类复用 `evidence_ledger.SOURCE_KEYWORDS`；CLI 支持 `--evidence/--bank/--dry-run`。
- `tests/test_claim_bank_writer.py` — 25 项测试（字段校验/写回/分类/CLI）。
- `tests/test_e2e_regression.py` — 9 项端到端回归：财务模型对固定 fixture 可复算（2027 base revenue 重算 = 存储值 4.625）、输入类型隔离（CSV 仅 historical/assumption，无 calculated）、证据链信任分有界性与重复证据不加分、本地 Demo 五要素齐全、workflow 本地路径（空证据→abstain；有证据无 LLM 配置→保守降级 `rule_only_fallback`，已按 PR #8 新契约改写原 RuntimeError 断言）。

### 测试

- 全量 `python -m pytest tests/ -q`：**129 passed**（#5–#8 合并内容 + 本 PR）。

### 待团队复核

1. 写回工具需团队提供**核验后**的真实证据才能回填 Claim Bank（工具就绪 ≠ 已回填）。
2. ontology 系数复核仍在等待团队结论。

---

## P1 财务影响链路四模块（2026-09-06，PR #5–#8，已合并；经 PR #10 恢复）

按 TODO P1 实现完整财务影响链路，4 个堆叠 PR（每个只含自己的 diff，按序合并，GitHub 会自动把后续 PR 基址改回 main）：

| PR | 分支 | 内容 | 测试 |
|---|---|---|---|
| #5 | feat/engineering-analyzer | `src/engineering_analyzer.py` 工况/口径归一化（额定vs峰值、电机vs模组） | +21 用例 |
| #6 | feat/economic-mapper | `src/economic_mapper.py` + `data/processed/tech_to_economics_ontology.json` 工程→经济假设可审计映射 | +11 用例 |
| #7 | feat/causal-critic | `src/causal_critic.py` 因果批判层（替代解释/反事实需求/不可归因/置信度下调） | +28 用例 |
| #8 | feat/workflow-financial-chain | `run_financial_chain` 全链路（验证门控→工程→经济→批判→财务三情景）+ `claim_verifier` 无 LLM 配置时保守降级修复（原直接崩溃） | +15 用例 |

- 全量 `pytest tests/ -q`：**95 passed**。
- 待复核：ontology 弹性系数/单位成本初值为估计值，需经济金融成员把关后再用于正式财务模型；数据质量问题（纳博 RV-20E 行疑似填数错误、步科 FMK 缺重量、Y 系列待补充）已在 PR #5 标注。
- 注：因本机 git 协议连接 GitHub 受限，本次经 GitHub Git Data API 推送。
- 恢复记录：main 曾意外回退至 #5 合并点（f97537b），导致 #6–#8 内容不在 main 中（PR 状态仍显示 MERGED）；经 **PR #10** 将 #8 合并点（24ad46e，含全部 #5–#8 内容）重新合入，现已恢复，合并后全量 **129 passed**。

---

## 当前工作区同步记录（2026-09-06，StateVerifier 误报修复）

由孙圣尧完成 TODO P0.3（PR #3 review 中认领）：StateVerifier 六条规则层误伤全部归零。

### 修复内容（src/state_verifier.py 五处）

1. **数值归属三值齐全原则**：`source_same_val` 提取不到时不做归属判定（宁缺毋滥）——修复列举式证据（「A、B、C 分别增长 x%、y%、z%」）的系统性口径误报
2. **数值提取窗口截断保护**：数值被 30 字符窗口切成半截（如「47.31」→「47」）时丢弃，不返回半个数值
3. **口径词对豁免**：claim 含对立口径词之一（如「额定扭矩」）即不再要求包含另一个（「峰值扭矩」）
4. **检测优先级重排**：口径偷换 > 数值矛盾 > 时间错位 > 来源降级 > 限定词缺失——限定词是弱信号，不再抢来源降级的 low_confidence
5. **约数感知匹配**：精确数值严格 float 匹配（消除跨指标交叉匹配，172 vs 164.8）；约数表述（「超过100%」vs 101.30%）用 ±10% 容差（表述粒度差异≠篡改）

### 修复效果（98 用例 × 2 模型，详见 benchmarks/pipeline_report.md）

| 指标 | 修复前 | 修复后 |
|---|---|---|
| 误伤（LLM 判对被覆盖成错） | 6 + 6 | **0 + 0** |
| claude-sonnet-5 合并准确率 | 83.7% | **91.8%**（裸 LLM 62.5%，+29.3pts） |
| gpt-5.5 合并准确率 | 82.7% | **90.8%**（裸 LLM 65.3%，+25.5pts） |
| 数值篡改（此前误伤重灾区） | 75.0% | **93.8%**（≥裸 LLM 水平） |
| 来源降级 | 76.5% | **100%** |
| 规则层单独准确率 | 80.6% | **88.8%**（无 API 调用） |

### 新增文件

- `benchmarks/find_false_positives.py` — 误伤定位工具（LLM 判对但被规则层覆盖后判错的用例明细）
- `tests/test_state_verifier_fixes.py` — 11 项 fixture 回归测试，每条对应一个真实误伤用例；与 PR #3 的 5 项测试合并后 `unittest` 共 16 项全过

### 遗留（TODO P1 口径偷换 70.6% 仍为最弱项）

- 口径词对注册表可扩充（当前 14 对）；列举式证据的数值-指标对应关系解析（「分别增长」句式）暂由「三值齐全」原则回避，后续可做结构化解析

---

## 当前工作区同步记录（2026-09-05，PR #3）

本次由 Chen Luodi 基于 `main` 的 `42a2e3b` 完成项目状态审计、说明文件同步和 P0 首个开发切片。内容已提交为 `c58a7fc`，推送至 `FeishengLuo/pku-financial-ai-agent` 的 `feat/financial-model-local-demo` 分支，并向上游提交 PR #3；本次没有直接推送 `aeiou0123` 的 `main`。

### 审计结论

- benchmark、四个核心验证模块和 pipeline 结果已经进入 `main`，可以开始绿的谐波简化财务模型、本地可复现 Demo，以及 StateVerifier 的误判修复。
- pipeline 的 Claude 83.7%、GPT 82.7% 是 98 个 benchmark 用例上的规则层 + LLM 判别准确率，不应表述为真实业务最终准确率。
- 财务模型必须区分历史披露数据、人工假设和模型计算结果；首版 Demo 只覆盖绿的谐波单案例和本地 fixture。
- 官方 datasheet、专利复核、Claim evidence 回填和实时检索属于后续证据增强任务，不阻塞首版 Demo，但不能被标记为已完成。

### 本次修改

- 更新 `README.md`、`data/README.md`、`research_materials/README.md`：同步当前阶段、运行边界和数据事实。
- 重写 `TODO.md`：以 P0/P1/P2 划分财务模型、Demo、可靠性回归、工程/经济扩展和证据增强任务，并补充验收标准。
- 更新 `data/collection_checklist.md`、`data/search_guide.md`、`data/search_report.md`：区分已完成资料、待人工补充资料与当前不阻塞项。
- 更新 `research_materials/notes/feasibility_analysis_and_plan.md`：保留早期研究规划，同时附加当前执行基线，避免过期日期被当作现状。
- 在仓库外的 `杂项/pku_fin_ai_local.md` 记录本次审计、修改范围、验证结果和 PR 状态；该文件不加入项目仓库。

### 后续提交建议

本次财务模型、Demo、fixture、测试及说明文件作为一个 PR 提交，便于一次性审阅；后续功能建议按模型、验证规则和文档分别提交。

### 2026-09-05 开发更新（`c58a7fc`，PR #3）

- 新增 `src/financial_model.py`：带来源和输入类型隔离的绿的谐波简化财务模型，输出三情景 DCF 原型。
- 新增 `data/processed/green_harmonic_model_inputs.csv`、`local_demo_fixture.json` 及模型运行结果文件。
- 新增 `app.py`：默认无 API 的本地单案例 Demo；规则层无法确定时保守返回 `abstain`。
- 新增 `tests/`、`requirements.txt`，当前 `unittest` 9 项测试通过。
- 基准运行结果：base EV `6.0056 bn CNY`、2027 revenue `4.6250 bn CNY`、2027 FCF `0.4703 bn CNY`；这些是原型假设下的计算结果，不是披露事实或投资建议。
- 已运行：compileall、9 项 unittest、模型 CLI、Demo CLI 和 Excel 工作表核验；均通过。已提交并推送到 fork，等待上游审阅。

---

## 同步总览表

| 日期 | 提交哈希 | 类型 | 一句话说明 | 推送状态 |
|---|---|---|---|---|
| 2026-09-07 | `feat/demo-serialized-chain` | fix/test | Demo 从并联改为串联全链路：`app.py` 调 `run_financial_chain(local_only=True)`，验证结论真实传导进财务假设与 EV（7.74/10.27/5.11，工程参数调整后）；更新 test_local_demo/test_e2e_regression 断言，新增工程→经济传导回归，全量 127 测试全绿 | ⏳ PR 待合并 |
| 2026-09-07 | `fix/proposal-number` | docs | 评估层验收后修正：03_product 的 benchmark 数字 83.7%/82.7% → **91.8%/90.8%**（含修复前对照），消除与 07_team 的跨章不一致 | ✅ 直接推 main |
| 2026-09-06 | `fix/verifier` | fix/test | StateVerifier 误报修复：误伤 6→0，合并准确率 83.7%/82.7% → **91.8%/90.8%**；新增 11 项 fixture 回归测试 | ✅ 已合并（0449d77，PR #4） |
| 2026-09-05 | `c58a7fc` | feat/test/docs | Feisheng：审计状态并新增绿的谐波简化财务模型、本地无 API Demo、输入 fixture、结果文件、9 项回归测试和说明同步；PR #3 | ✅ 已合并（e157ee3） |
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
