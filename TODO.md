# TODO 清单

> 项目：Claim2Value — 北大金融 AI 智能体创新大赛
> 更新：2026-08-30

---

## 第一阶段：数据收集（Day 1-2，截止 8/31）

### P0 — 今晚必须完成
- [ ] 绿的谐波 2024 年报下载并放入 `data/raw/company_filings/`
- [ ] 绿的谐波 2025 半年报下载
- [ ] 步科股份 2024 年报或 2025 半年报下载
- [ ] 双环传动 2024 年报或 2025 半年报下载
- [ ] 每家公司至少 1 份 datasheet/参数资料
- [ ] 更新 `data/collection_checklist.md` 状态列

**负责人**：西交经济金融（年报）、机械+电气（datasheet）

### P1 — 明天完成
- [ ] 每家公司 2–3 份 datasheet
- [ ] 每家公司 3 个核心专利
- [ ] 每家公司 2 份券商研报
- [ ] 每家公司 5–7 个 claim 素材
- [ ] 1 份行业报告

**负责人**：西交经济金融（年报/研报/claim）、电气成员（专利）、机械成员（datasheet/ competitor）

---

## 第二阶段：核心模块开发（Day 3-7）

- [ ] `src/claim_extractor.py` — Claim 提取
- [ ] `src/evidence_retriever.py` — 证据检索（RAG + web search）
- [ ] `src/evidence_ledger.py` — 证据账本
- [ ] `src/claim_verifier.py` — Claim 验证
- [ ] `src/engineering_analyzer.py` — 工程分析
- [ ] `src/economic_mapper.py` — 经济机制映射
- [ ] `src/financial_model.py` — 财务模型（Excel 输出）

**负责人**：Chen Luodi（代码实现）+ 各专业成员（规则/ground truth）

---

## 第三阶段：Agent 集成与创新模块（Day 8-10）

- [ ] `src/workflow.py` — LangGraph 工作流
- [ ] `src/causal_critic.py` — Causal Financial Critic
- [ ] `src/state_verifier.py` — State-Aware Financial Agent
- [ ] 端到端案例跑通

**负责人**：Chen Luodi（LangGraph）+ 孙圣尧（state verification）+ 西交经济金融（causal critic）

---

## 第四阶段：Benchmark 与 Demo（Day 11-12）

- [ ] `benchmarks/claim_verification.json`
- [ ] `benchmarks/engineering_accuracy.json`
- [ ] `benchmarks/economic_reasoning.json`
- [ ] `benchmarks/financial_accuracy.json`
- [ ] `app.py` — Streamlit Demo

**负责人**：孙圣尧（benchmark）+ Chen Luodi（Demo）

---

## 第五阶段：项目材料（Day 13-14）

- [ ] 项目书/PPT
- [ ] 技术方案说明
- [ ] Benchmark 报告
- [ ] 演示视频（2–3 分钟）
- [ ] 9/10 前提交报名

**负责人**：西交经济金融（项目书主笔）+ 全员补充

---

## 阻塞问题

- [ ] Bash 安全分类器偶尔不稳定 — 已恢复，继续观察
- [ ] 部分 datasheet 可能需展会/公众号获取 — 备选方案：用研报参数表

---

## 每日站会

每晚 22:00，30 分钟：
1. 今天完成了什么？
2. 阻塞问题是什么？
3. 明天计划做什么？
4. 是否需要调整范围？
