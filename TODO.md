# TODO 清单

> 项目：Claim2Value（Evidence-Grounded Engineering-to-Finance Agent）
> 更新：2026-09-08（Phase 3D 完成，进入答辩待命）
> 当前结论：**Phase 3D 收尾完成**——演示脚本/路演大纲/终验清单/全局对账全部交付（PR #23–#26），回归 140 全绿 + 审校 issues=0。

## 当前基线

- `main` 当前基线：PR #26 已合并（Phase 3D 四模块全部完成）。
- 核心验证模块已存在：`evidence_ledger.py`、`state_verifier.py`、`claim_verifier.py`、`workflow.py`。
- benchmark 已生成 98 个测试用例；规则层 + LLM pipeline 在既有评估中为 Claude 83.7%、GPT 82.7%。这些是 benchmark 判别准确率，不是现实业务准确率。
- 当前数据：18 份 PDF、18 份 `.meta.json`、**51 条 Claim（36 已验证/15 待验证）**、30 条专利记录、14 条参数记录。
- Claim Bank 的 `evidence_list` 已回填：已验证条目带页码级定位 + 内容指纹 + 核验人；15 条待验证条目证据为研报口径，终验清单已备。
- `requirements.txt`、`tests/`（140 passed）、`app.py`、绿的谐波与双环传动双案例财务模型、全链路 workflow 均已实现。

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
- [x] 修复并回归 StateVerifier 已知的数值、时间和复合 Claim 误判；保留规则层与 LLM 层各自结果。（PR #4）
- [x] 为 pipeline 报告中的 6 次规则层误判建立可定位 fixture，不用整体准确率掩盖错误类型。（PR #4，11 项回归测试）

## P1：P0 完成后推进

- [x] 实现 `src/engineering_analyzer.py`：统一额定/峰值、连续/峰值工况及电机/模组口径。（PR #5 已合并）
- [x] 实现 `src/economic_mapper.py` 和 `tech_to_economics_ontology.json`：把工程结论映射为销量、ASP、单位成本、毛利等可审计假设。（PR #6 已合并；ontology 系数待经济金融成员复核）
- [x] 实现 `src/causal_critic.py`：输出替代解释、反事实证据需求和不能归因的部分。（PR #7 已合并）
- [x] 将 `workflow.py` 扩展为财务影响链路；是否引入 LangGraph 以本地可运行性和依赖成本为准，不作为首版 Demo 的前置条件。（PR #8 已合并，纯本地实现，未引入 LangGraph）
- [x] 将人工核验后的证据写回 Claim Bank；每条 Claim 至少保留来源、页码/定位、摘录、口径和核验人。—— 写回工具：`src/claim_bank_writer.py`（五必填字段校验、核验人空则硬拒绝、指纹幂等去重、原子写盘），PR #9；5 条已验证 Claim（GH_005/GH_006/BK_002/BK_005/SH_006）已于 P1.3 完成真实回填，证据定位到年报/半年报具体页码（PR #11）。
- [x] 增加财务模型、证据链、工程映射和 Demo 输出的端到端回归用例。—— `tests/test_e2e_regression.py` 9 项：财务可复算（2027 base revenue 重算=存储）、输入类型隔离（仅 historical/assumption）、证据链信任分有界性、Demo 五要素、workflow 本地无证据→abstain、有证据无 LLM 配置→rule_only_fallback 降级（适配 PR #8 契约）。

## P2：证据增强与扩展

- [ ] 手动补充官方 datasheet：绿的谐波 LCS/LHS/Y、步科 FMK、环动科技 RV 系列。
- [ ] 核对步科核心发明专利；复核现有专利号、来源和可引用性。
- [ ] 补充重大事项/客户合作/募投公告及 BOM 数据。
- [ ] 完善 `evidence_retriever.py`、Claim 自动提取和实时 Web Search；使用本地缓存，避免外部服务成为 Demo 单点依赖。
- [ ] 扩展步科、双环传动及其他行业案例。

## P3：项目书与商业潜力（当前主线，70% 分值载体）

- [x] 搭 `docs/proposal/` 骨架：README（8 章骨架 + 素材地图）+ 01–04/06–08 七章 stub。（PR #13）
- [x] 第 5 章"商业潜力"完整初稿：TAM/SAM/SOM 三层漏斗（SAM 2–6 亿/年）、竞争格局、产能证据、估值对照、竞品定价、商业模式与三档定价、风险对冲，全部数字带 [C1]–[C8] 溯源。（PR #13）
- [x] 展开 01–04、06–08 七章（按各 stub 内的建议结构与素材指针写）。（PR #14）
- [x] Phase 3A 提质：机械审校脚本（锚点数字/溯源标签/PR 引用/过时表述，issues=0）；04 章升级 5→14 条已验证 + 3 个新示例（双源互证/双源逐字/产能利用率）；01/02/06/08 章末全局索引指引；SH_003 复核结论入 Claim Bank notes（项目书未引用，无正文风险）。（PR #16）
- [x] C7 效率实测：`scripts/benchmark_latency.py` N=30 自动化基准，p50 4.3ms/p95 5.0ms（PR #18 首测、PR #24 修复被 smoke test 覆盖的根因并统一全仓口径）。
- [ ] 15 条待验证 claim 人工终验：核对清单（`docs/proposal/appendix_pending_review.md`，PR #25）+ **K3 机器预检报告（`docs/proposal/appendix_precheck_report.md`）已备**——10 条官方原文一致建议升级、1 条口径修正后升级、4 条维持待验证；人工抽读确认后用 `claim_bank_writer.py` 写回。
- [ ] 经济金融组复核模型输入：**K3 复核报告（`docs/proposal/model_param_review.md`）已备**——RV ASP/成本偏离现实锚点（环动招股书）建议修正，weight 弹性 0.5 建议降 0.25，绿的税率/毛利率建议注明口径；改数则重跑回归并更新演示数字，否则按报告补 Q&A 口径。
- [x] Phase 3C 模块 1-4：延迟基准 N=30（PR #18）、反向 DCF（PR #19）、双环全链路移植（PR #20）、Claim Bank 扩至 51 条/11 家（PR #21）。（2026-09-07）
- [x] 答辩问答预案 `09_qa_playbook.md`（PR #22）。
- [x] Phase 3D 模块 1-4：README 现状重写（PR #23）、演示脚本+路演大纲（PR #24）、15 条终验清单（PR #25）、全局终检+进度同步（PR #26）。
- [ ] 演示彩排：真人按 `10_demo_script.md` 走一遍并录屏（脚本已备）。

## 文档与交付

- [x] 已根据当前实现更新 `README.md`、`data/README.md`、本文件和 `SYNC_LOG.md`；后续功能变更仍需同步维护。
- [ ] 在模型与 Demo 完成后补充项目书/PPT、技术方案、演示脚本和可复现运行记录。—— 项目书已启动，见 P3。
- [x] 本轮变更按文档/数据口径集中提交；提交前执行 `git diff --check`、编译检查和本地单案例运行。

## 验收标准

1. `python -m src.workflow --single ...` 可在无外部 API 时运行验证路径。
2. 财务模型对固定 fixture 产生可复算的三情景结果，且每个输入可区分“披露/假设/计算”。
3. Demo 能展示 Claim、证据、验证结论、限制和财务影响，并能指出证据不足。
4. 测试覆盖核心规则和至少一个端到端案例；失败可定位到具体 fixture。
5. README、数据说明、TODO、SYNC_LOG 与实际文件状态一致。

## 当前不作为阻塞条件

- 全量官方 datasheet、全部专利二次核验、51 条 Claim 全部达到官方一手证据标准。
- 实时 Web Search、多行业覆盖、完整 LangGraph 编排和生产级估值模型。

这些事项仍需完成，但应在首版本地 Demo 可复现之后推进。
