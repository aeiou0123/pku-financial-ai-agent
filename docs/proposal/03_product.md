# 第 3 章 产品方案与技术架构

> 本章描述的工程底座已在 P1 阶段实现并开源于 GitHub 仓库
> （github.com/aeiou0123/pku-financial-ai-agent），全部模块路径可点击验证。
> 当前 `python -m pytest tests -q` 全量 **140 项回归测试通过**（2026-09-08，PR #26 后基线）。
> 未实现的能力（LLM 实时检索、全行业覆盖等）在本章如实标注为"进行中"。

## 3.1 产品形态：对话式证据链分析智能体

Claim2Value 面向券商研究所、产业基金分析师，提供三种互相咬合的产品形态：

**（1）对话式分析入口（本地 Demo 已运行）**
分析师以自然语言提问或输入一条产业链 Claim（如"绿的谐波新一代关节模组减重 30% 以上"），
系统返回：验证结论（supported / partially_supported / abstain）、置信度、
证据清单、以及"证据不足以判定"时的明确 abstain 说明。
本地 Demo（`app.py`）默认不调用 LLM、不访问网络，只读本地 fixture 运行确定性规则，
保证可复现、可审计——这是刻意的产品决策：无证据时宁可不答，不输出黑盒结论。

**（2）Claim Bank（证据链资产库，已交付 51 条 Claim / 11 家公司）**
以结构化 JSON（`data/processed/claim_bank_filled.json`）管理产业链分析主张，
每条 Claim 挂接证据列表，证据含五必填字段：来源、页码/定位、原文摘录、口径说明、核验人。
目前 51 条 Claim 中 47 条已完成公告原文级核验（证据定位到年报/招股书/公告具体页码，
含 2026-09-09 机器预检+人工确认升级的 11 条），
4 条待验证（BK_001/BK_003 官方未披露数值、GH_007/SH_002 待厂商 datasheet，
均以低置信度+显式疑点标注呈现，见 3.3）。

**（3）报告生成（证据链 + 财务影响一体化输出）**
系统把"Claim 验证 → 证据账本 → 工程口径归一化 → 经济假设映射 → 因果批判 →
财务三情景"全链路结果组装为结构化报告，输出物同时落盘 JSON 与 Excel
（`data/processed/green_harmonic_model_results.json` / `.xlsx`），
供分析师直接嵌入研报底稿。

## 3.2 系统架构：四层流水线

```
┌────────────────────────────────────────────────────────────────┐
│ 采集层  data/raw/：18 份披露/研报 PDF + .meta.json 元数据        │
│          src/data_tools/：extract_claims / extract_patents /    │
│          extract_parameters（PDF → Claim / 30 条专利 / 14 条参数）│
└──────────────────────────┬─────────────────────────────────────┘
                           ▼
┌────────────────────────────────────────────────────────────────┐
│ Pipeline 层  src/workflow.py：run_verification 端到链 +          │
│   run_financial_chain 财务影响链路（LangGraph 可选，纯本地回退）  │
│   节点：证据账本 → 规则层 → LLM 语义层 → 报告组装               │
└──────────────────────────┬─────────────────────────────────────┘
                           ▼
┌────────────────────────────────────────────────────────────────┐
│ Claim Bank 层  data/processed/claim_bank_filled.json             │
│   写回工具 src/claim_bank_writer.py（五必填字段硬门控）           │
└──────────────────────────┬─────────────────────────────────────┘
                           ▼
┌────────────────────────────────────────────────────────────────┐
│ 输出层  验证报告 / 三情景财务模型（JSON + XLSX）/ 本地 Demo       │
└────────────────────────────────────────────────────────────────┘
```

架构的三个关键决策：

1. **规则层与 LLM 层分离**（`src/state_verifier.py` vs `src/claim_verifier.py`）：
   数值矛盾、时间错位、口径偷换、来源降级、限定词缺失等确定性检查由规则层执行，
   不依赖模型；LLM 只做语义判断，且两者结果**并列保留**，不互相覆盖。
2. **无 LLM 配置时保守降级**：`claim_verifier` 检测到无 API 配置时返回
   `rule_only_fallback` 降级标记（修复自 PR #8），系统绝不假装完成了语义验证。
3. **pipeline 开源可审计**：全链路代码开源，是回应竞品"黑盒结论"缺点的工程立场。

## 3.3 核心机制：四条产品主张的实现方式

**（1）Claim 溯源——证据五必填字段 + 幂等指纹**
`claim_bank_writer.py` 把人工核验后的证据写回 Claim Bank：核验人字段为空即硬拒绝
（`SKIP_EMPTY_VERIFIER`）；每条证据按 `sha256(excerpt||source)[:16]` 指纹幂等去重；
写入采用临时文件 + `os.replace` 原子替换并自动备份。任何一条进入 Claim Bank 的证据
都可定位到原始 PDF 的具体页码（当前 47 条已验证 Claim 均定位到公告原文页码，PR #11/#15/#21/#29）。

**（2）置信度分级——来源等级客观化**
`src/evidence_ledger.py` 按 年报 > 研报 > 新闻 > 传闻 的客观等级给证据打分
（trust_score ∈ [0,1]），不依赖 LLM 判断；多条证据的交叉验证状态单独记录，
重复证据不重复加分（有界性由端到端测试保证）。

**（3）推理留痕——财务模型输入三分法**
`src/financial_model.py` 对绿的谐波的三情景模型中，每条输入强制标注
`historical`（披露锚点）/ `assumption`（人工假设）/ `calculated`（计算结果，
不可写回输入表），输出文件带 `model_status =
prototype_scenario_not_investment_recommendation` 限定，任何引用须携带该限定。

**（4）多口径并列——不替用户做取舍**
工程侧由 `src/engineering_analyzer.py` 归一化额定/峰值、电机/模组等口径差异；
经济侧由 `src/economic_mapper.py` + `data/processed/tech_to_economics_ontology.json`
把工程结论映射为可审计的销量/ASP/单位成本假设；`src/causal_critic.py` 输出
替代解释、反事实证据需求与不可归因部分，主动下调置信度。冲突口径（如 GGII vs 高盛
销量预测）在产品中并列呈现，这与第 5 章的写作纪律一致。

## 3.4 关键实现与仓库路径对照

| 产品能力 | 实现模块 | 测试覆盖 |
|---|---|---|
| 端到端验证流水线 | `src/workflow.py` | `tests/test_workflow_financial_chain.py` |
| 规则层（五类硬错误） | `src/state_verifier.py` | `tests/test_state_verifier.py`、`test_state_verifier_fixes.py` |
| LLM 语义层 + 无配置降级 | `src/claim_verifier.py` | `tests/test_claim_verifier_fallback.py` |
| 证据账本与信任分 | `src/evidence_ledger.py` | `tests/test_e2e_regression.py` |
| 工程口径归一化 | `src/engineering_analyzer.py` | `tests/test_engineering_analyzer.py` |
| 工程→经济假设映射 | `src/economic_mapper.py` + ontology JSON | `tests/test_economic_mapper.py` |
| 因果批判层 | `src/causal_critic.py` | `tests/test_causal_critic.py` |
| 三情景财务模型 | `src/financial_model.py` | `tests/test_financial_model.py` |
| Claim Bank 写回 | `src/claim_bank_writer.py` | `tests/test_claim_bank_writer.py`（25 项） |
| 本地 Demo 五要素 | `app.py` + `local_demo_fixture.json` | `tests/test_local_demo.py` |
| PDF 数据提取 | `src/data_tools/extract_*.py` | —（提取产物已由人工抽查） |

**质量证据**：全量 `python -m pytest tests -q` **140 passed**（约 6 秒），
含 9 项端到端回归（财务可复算、输入类型隔离、Demo 五要素、无证据 abstain、
降级路径契约）。另有自建 benchmark 98 个判别用例，规则层 + LLM pipeline
对 Claude **91.8%**、GPT **90.8%**（StateVerifier 误报修复后；修复前为 83.7%/82.7%，
见 PR #4 及 `benchmarks/pipeline_report.md`；为 benchmark 判别准确率，非业务准确率）。
产出物示例：三情景估值原型 EV 悲观 0.94 亿 / 基准 30.78 亿 / 乐观 58.50 亿元
（`data/processed/green_harmonic_model_results.json`；2026-09-09 参数复核后口径：
税率改 15% 高新口径、谐波单位成本按 2024 年报毛利率 36.13% 锚定，悲观情景 FCF 转负故 EV 趋零）。

**诚实边界**：实时 Web 检索与 Claim 自动提取（`evidence_retriever.py`）、
全量官方 datasheet、4 条待验证 Claim 的厂商 datasheet 终验、生产级估值模型均未完成，
按 TODO P2/P3 排期推进，不作为当前验收条件。
