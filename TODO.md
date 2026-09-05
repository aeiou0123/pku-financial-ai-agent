# TODO 清单

> 项目：Claim2Value（Evidence-Grounded Engineering-to-Finance Agent）
> 更新：2026-09-05
> 当前结论：验证 MVP 已进入“简化财务模型 + 本地 Demo”阶段；首个本地可复现切片已实现，模型口径复核和 StateVerifier 修复仍在进行。

## 当前基线

- `main` 已合并 PR #2，当前基线：`42a2e3b`。
- 核心验证模块已存在：`evidence_ledger.py`、`state_verifier.py`、`claim_verifier.py`、`workflow.py`。
- benchmark 已生成 98 个测试用例；规则层 + LLM pipeline 在既有评估中为 Claude 83.7%、GPT 82.7%。这些是 benchmark 判别准确率，不是现实业务准确率。
- 当前数据：18 份 PDF、18 份 `.meta.json`、19 条 Claim、30 条专利记录、14 条参数记录。
- 19 条 Claim 中 5 条标记为已验证、14 条待验证；Claim Bank 的 `evidence_list` 尚未回填。
- `requirements.txt`、`tests/`、`app.py`、绿的谐波简化财务模型和本地 fixture 已实现；完整工程/经济映射模块仍未实现。

## P0：下一步必须完成（当前主线）

### P0.1 绿的谐波简化财务模型

- [ ] 先由经济金融成员确认输入口径、情景和公式：历史披露数据、人工假设、模型计算结果必须分栏保存。
- [x] Chen Luodi 实现 `src/financial_model.py`：Revenue → COGS → Gross Margin → EBITDA → FCF → 简化 DCF（原型）。
- [x] 形成 `data/processed/green_harmonic_model_inputs.csv`，区分历史锚点与人工假设并记录来源定位。
- [x] 输出 `data/processed/green_harmonic_model.xlsx` 和 JSON，包含 base/upside/downside 情景。
- [x] `tests/test_financial_model.py` 覆盖手算收入、可复现性、输入类型隔离和情景单调性。
- [ ] 由经济金融成员复核模型输入口径、BOM、税率、DCF 参数和历史财务字段；复核前不得作为正式估值结论。

### P0.2 本地可复现 Demo

- [x] 准备 `data/processed/local_demo_fixture.json`：脱离外部 API 的绿的谐波 Claim、证据、来源元数据和限制。
- [x] 实现 `app.py`：展示 Claim → 证据账本 → StateVerifier 结论 → 财务影响情景。
- [x] 首版 Demo 范围锁定为绿的谐波单案例、本地数据和可追溯输出；实时检索、全行业覆盖和全部 Claim 核验不作为首版验收条件。
- [x] 增加 Demo 启动说明和无 API key 的运行路径；`requirements.txt` 已包含 `openpyxl` 与可选 `streamlit`。

### P0.3 可靠性回归

- [x] 建立 `tests/`，覆盖本地 Demo、模型公式、输入溯源，以及证据缺失、限定词删除、口径偷换、数值篡改和来源降级规则；现有 benchmark 继续覆盖时间错位等路径。
- [ ] 修复并回归 StateVerifier 当前已知的数值、时间和复合 Claim 误判；保留规则层与 LLM 层各自结果。
- [ ] 为 pipeline 报告中的 6 次规则层误判建立可定位 fixture，不用整体准确率掩盖错误类型。

## P1：P0 完成后推进

- [ ] 实现 `src/engineering_analyzer.py`：统一额定/峰值、连续/峰值工况及电机/模组口径。
- [ ] 实现 `src/economic_mapper.py` 和 `tech_to_economics_ontology.json`：把工程结论映射为销量、ASP、单位成本、毛利等可审计假设。
- [ ] 实现 `src/causal_critic.py`：输出替代解释、反事实证据需求和不能归因的部分。
- [ ] 将 `workflow.py` 扩展为财务影响链路；是否引入 LangGraph 以本地可运行性和依赖成本为准，不作为首版 Demo 的前置条件。
- [ ] 将人工核验后的证据写回 Claim Bank；每条 Claim 至少保留来源、页码/定位、摘录、口径和核验人。
- [ ] 增加财务模型、证据链、工程映射和 Demo 输出的端到端回归用例。

## P2：证据增强与扩展

- [ ] 手动补充官方 datasheet：绿的谐波 LCS/LHS/Y、步科 FMK、环动科技 RV 系列。
- [ ] 核对步科核心发明专利；复核现有专利号、来源和可引用性。
- [ ] 补充重大事项/客户合作/募投公告及 BOM 数据。
- [ ] 完善 `evidence_retriever.py`、Claim 自动提取和实时 Web Search；使用本地缓存，避免外部服务成为 Demo 单点依赖。
- [ ] 扩展步科、双环传动及其他行业案例。

## 文档与交付

- [x] 已根据当前实现更新 `README.md`、`data/README.md`、本文件和 `SYNC_LOG.md`；后续功能变更仍需同步维护。
- [ ] 在模型与 Demo 完成后补充项目书/PPT、技术方案、演示脚本和可复现运行记录。
- [ ] 每次变更按功能拆分 commit；提交前执行 `git diff --check`、编译检查和本地单案例运行。

## 验收标准

1. `python -m src.workflow --single ...` 可在无外部 API 时运行验证路径。
2. 财务模型对固定 fixture 产生可复算的三情景结果，且每个输入可区分“披露/假设/计算”。
3. Demo 能展示 Claim、证据、验证结论、限制和财务影响，并能指出证据不足。
4. 测试覆盖核心规则和至少一个端到端案例；失败可定位到具体 fixture。
5. README、数据说明、TODO、SYNC_LOG 与实际文件状态一致。

## 当前不作为阻塞条件

- 全量官方 datasheet、全部专利二次核验、19 条 Claim 全部 evidence 回填。
- 实时 Web Search、多行业覆盖、完整 LangGraph 编排和生产级估值模型。

这些事项仍需完成，但应在首版本地 Demo 可复现之后推进。
