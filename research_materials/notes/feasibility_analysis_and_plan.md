# Claim2Value 深度可行性分析与执行规划

> 项目：北京大学金融 AI 智能体创新大赛
> 方向：赛道一 — 金融 AI 智能体算法与应用创新
> 整理时间：2026-08-29
> 规划周期：2 周（至 2026-09-10 报名截止）

---

# 第一部分：深度可行性分析

## 1. 项目定位最终确认

### 1.1 推荐项目

**Claim2Value：工业技术 Claim 验证与金融影响智能体**

一句话定位：
> 别人让 AI 看懂财报，我们让 AI 验证技术、理解工程、识别经济机制，并算清楚它到底值多少钱。

英文：
> Evidence-Grounded Engineering-to-Finance Agent

### 1.2 推荐垂直行业

**人形/工业机器人关节模组**

首选案例公司：**绿的谐波（688017）**

理由：
- 上市公司，财务数据完整
- 2025 世界机器人大会发布人形机器人专用谐波减速器
- 行业扭矩密度从 4.5 → 6.2 Nm/kg 提升，目标 >8 Nm/kg
- 已进入天工、智元等头部厂商，据传进入特斯拉 Optimus 供应链
- 市场关注度高，公开资料丰富

备选案例：
- 步科股份：FMK 系列无框力矩电机功率密度提升 20%
- 禾川科技：高功率密度无框力矩电机扭矩密度 4.5 Nm/kg

### 1.3 赛道选择

**赛道一：金融 AI 智能体算法与应用创新**

理由：
1. 核心创新在 Agent 架构与跨域推理，不是交易策略
2. 输出是“估值/财务影响”，不是可回测的买卖信号
3. 目前无落地背书，不适合赛道三

---

## 2. 技术可行性分析

### 2.1 核心技术链路

```
用户输入：一则技术 Claim（如"绿的谐波新关节扭矩密度提升 30%"）
    ↓
[Claim Extractor] 提取 claim、主体、数值、比较基准
    ↓
[Evidence Retriever] 检索公告、 datasheet、专利、研报、竞争对手资料
    ↓
[Claim Verifier] 验证 claim 是否成立、definition 是否一致、证据强度
    ↓
[Engineering Analyzer] 拆解技术来源（电机/减速器/材料/热设计）、trade-offs
    ↓
[Economic Mechanism Mapper] 映射到 cost/ASP/demand/capacity/yield
    ↓
[Financial Model Engine] 计算 Revenue → COGS → Margin → EBITDA → FCF → Valuation
    ↓
[Causal Financial Critic] 质疑因果链、提出替代解释、要求反事实证据
    ↓
[State Verifier] 验证 Excel/数据库/tool 调用后的状态是否正确
    ↓
输出：Research Memo + Evidence Ledger + Updated Financial Model + Risk Register
```

### 2.2 每个模块的技术成熟度

| 模块 | 技术成熟度 | 风险 | 备注 |
|---|---|---|---|
| Claim Extraction | 高 | 低 | LLM + prompt 即可 |
| Evidence Retrieval | 中高 | 中 | 需要 RAG + 多源搜索 |
| Claim Verification | 中 | 中 | 有学术基础，需适配金融场景 |
| Engineering Analysis | 中 | 中 | 需要机械/电气成员提供 ground truth |
| Economic Mechanism | 中 | 中 | 西交经济成员强项 |
| Financial Modeling | 高 | 低 | Python + Excel 即可 |
| Causal Critic | 中 | 中 | 创新点，需设计特定 prompt/Agent |
| State Verification | 中 | 中 | 孙圣尧研究背景直接对口 |
| Report Generation | 高 | 低 | 模板化输出 |

### 2.3 技术可行性结论

**可行**。2 周内可以做出一个功能完整的 MVP，但需要聚焦：
- 只做 1 个垂直行业（机器人关节）
- 只做 1 个核心案例（绿的谐波）
- 先手工标注 ground truth，再逐步自动化

---

## 3. 数据可行性分析

### 3.1 可获取数据

| 数据类型 | 获取难度 | 来源 | 质量 |
|---|---|---|---|
| A 股行情/财务 | 低 | AKShare / Tushare | 高 |
| 公司公告/年报 | 低 | CNINFO 巨潮资讯 | 高 |
| 产品 datasheet | 中 | 公司官网/展会/供应商 | 中 |
| 专利数据 | 中 | Google Patents / CNIPA | 中 |
| 竞争对手参数 | 中 | 官网/行业报告 | 中 |
| 券商研报 | 中 | Wind/同花顺/东方财富 | 中 |
| 行业报告 | 低 | IIM/高工机器人/OFweek | 中 |

### 3.2 数据风险

1. **专利数据自动化难**：Google Patents 无免费批量 API，CNIPA 无官方 API
2. **参数口径不一致**：不同厂商 torque density 定义可能不同
3. **研报获取不稳定**：需要学校账号或手动收集

### 3.3 应对策略

1. **手工准备核心数据集**：5–10 个关键专利、3–5 份 datasheet、5–10 份公告
2. **参数标准化**：在 Claim Verification 层显式处理 mass definition、peak vs continuous torque
3. **数据兜底**：每个外部 API 加 try/except + fallback 到本地缓存

### 3.4 数据可行性结论

**可行**。不需要大规模实时数据，核心依靠公开资料 + 手工标注即可支撑 MVP。

---

## 4. 团队能力匹配分析

### 4.1 能力链与项目需求映射

```
项目需求                    团队成员
─────────────────────────────────────────────
Agent 系统工程     →      Chen Luodi
Agent 可靠性验证   →      孙圣尧
工程 ground truth  →      电气 + 机械成员
经济机制/因果推断  →      西交经济金融成员
金融建模/估值      →      西交经济金融成员
产品叙事/benchmark →      西交经济金融 + 孙圣尧
```

### 4.2 关键匹配点

| 团队能力 | 项目应用 |
|---|---|
| 孙圣尧：Agent state verification | State-Aware Financial Agent 模块 |
| 孙圣尧：benchmark oracle design | 整体 benchmark 设计 |
| 西交成员：causal inference | Causal Financial Critic 模块 |
| 西交成员：DID/event study | 反事实设计、趋势控制 |
| 电气成员：电机/电驱 | Engineering Analyzer 电气部分 |
| 机械成员：机器人/BOM/减速器 | Engineering Analyzer 机械部分 |
| Chen Luodi：Agent Engineering | 整体 orchestration + backend |

### 4.3 团队缺口

| 缺口 | 影响 | 应对 |
|---|---|---|
| 缺少专职前端工程师 | Demo UI 不够精美 | 用 Streamlit/Gradio 快速搭建 |
| 缺少金融数据工程经验 | 数据 pipeline 可能不稳定 | 用本地缓存 + 手工数据集兜底 |
| 缺少真实机构用户背书 | 赛道三竞争力不足 | 主报赛道一，弱化落地背书 |

### 4.4 团队匹配结论

**高度匹配**。这是少数能同时覆盖 Agent 可靠性、经济因果推断、工程 ground truth、金融建模的团队配置。

---

## 5. 时间可行性分析

### 5.1 时间约束

- 当前：2026-08-29
- 报名截止：2026-09-10
- 可用时间：约 12 天

### 5.2 关键路径

```
Day 1-2:  数据收集 + 案例确定
Day 3-4:  Claim Verification 模块
Day 5-6:  Engineering Analysis 模块
Day 7:    Economic Mechanism + Financial Model
Day 8-9:  Agent Orchestration
Day 10-11: Causal Critic + State Verification
Day 12:   Benchmark + 测试
Day 13-14: Demo + 项目材料
```

### 5.3 时间风险

| 风险 | 概率 | 影响 | 应对 |
|---|---|---|---|
| 数据收集超预期 | 中 | 延误 1–2 天 | 提前锁定绿的谐波案例，减少搜索 |
| Agent orchestration 调试 | 中高 | 延误 2–3 天 | 先用硬编码 workflow，再逐步抽象 |
| 财务模型复杂化 | 中 | 延误 1–2 天 | 先做简化版 DCF/相对估值 |
| 模型 API 不稳定 | 中 | 延误 1 天 | 准备多个模型端点 fallback |

### 5.4 时间可行性结论

**紧张但可行**。需要严格执行范围控制，避免过度工程化。

---

## 6. 创新性评估

### 6.1 与现有项目的差异

| 维度 | TradingAgents/FinRobot | DisruptIQ | ModelForge | Claim2Value（我们） |
|---|---|---|---|---|
| 输入 | 财报/新闻/行情 | 供应链事件 | 财务假设 | 工业技术 claim |
| 核心能力 | 多 Agent 炒股 | 风险传播 | Excel 建模 | Claim 验证 + 工程理解 + 经济机制 + 金融映射 |
| 输出 | BUY/HOLD/SELL | 风险分数 | Excel 模型 | 可追溯的估值影响 + Critic |
| 验证 | 弱 | 中 | 强（财务） | 强（跨层 evidence） |
| 团队要求 | CS/金融 | CS/供应链 | 金融/工程 | CS/Agent/工程/经济/金融 |

### 6.2 真正的创新点

1. **跨域证据链**：把技术 claim、工程参数、经济机制、金融估值串成可追溯链条
2. **Causal Financial Critic**：系统性质疑“技术升级→盈利提升”的因果链
3. **State-Aware Financial Agent**：金融 tool 调用后的状态验证
4. **工程金融 ontology**：定义技术参数到财务参数的映射规则

### 6.3 创新性结论

**创新性强，且有护城河**。核心壁垒在于团队跨学科能力，不是单一技术点。

---

## 7. 风险与应对总表

| 风险 | 概率 | 影响 | 应对策略 |
|---|---|---|---|
| 撞题（其他团队也做工业金融 Agent） | 中 | 高 | 强调 Causal Critic + State Verification 差异化 |
| 评委质疑商业价值 | 中 | 中 | 明确目标用户（券商研究所/PE/VC），给出效率提升数据 |
| Demo 效果不佳 | 中 | 高 | 提前准备 2–3 个典型 case，现场演示 |
| 模型幻觉导致错误结论 | 高 | 高 | 多层 verification + 确定性财务计算 |
| 时间不足 | 中 | 高 | 严格 MVP 范围，先做端到端再走通 |
| 网络/API 不稳定 | 中 | 中 | 本地缓存 + fallback |

---

# 第二部分：完整执行规划

## 8. 项目规格定义

### 8.1 项目名

**Claim2Value**（中文可称“技证通”或保留英文）

### 8.2 一句话定位

> 验证工业技术 Claim，量化金融价值。

### 8.3 目标用户

- 券商研究所工业组分析师
- PE/VC 技术投资团队
- 产业投资部门

### 8.4 核心场景

用户输入：
> "绿的谐波 2025 年发布的新一代谐波减速器关节模组，扭矩密度较上一代提升 30%，这是否支撑我们上调 2027 年盈利预测？"

系统输出：
1. Claim 验证结果（Partially supported，置信度 0.81）
2. 技术来源分析（电机/减速器/材料贡献）
3. 竞争对手对比
4. 对 BOM、成本、毛利率的影响
5. 对 2027 EPS/FCF/估值的量化影响
6. Causal Critic 的反方质疑
7. Evidence Ledger（每个结论可追溯）

---

## 9. 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                        User Interface                        │
│                    (Streamlit / Gradio)                     │
└───────────────────────┬─────────────────────────────────────┘
                        │
                ┌───────▼────────┐
                │ Master Planner │
                └───────┬────────┘
                        │
    ┌───────────────────┼───────────────────┐
    │                   │                   │
    ▼                   ▼                   ▼
┌──────────┐     ┌────────────┐     ┌──────────────┐
│ Claim    │     │ Evidence   │     │ Engineering  │
│ Extractor│     │ Retriever  │     │ Analyzer     │
└────┬─────┘     └──────┬─────┘     └──────┬───────┘
     │                  │                   │
     └──────────────────┼───────────────────┘
                        │
              ┌─────────▼──────────┐
              │ Claim Verifier     │
              └─────────┬──────────┘
                        │
              ┌─────────▼──────────┐
              │ Economic Mechanism │
              │ Mapper             │
              └─────────┬──────────┘
                        │
              ┌─────────▼──────────┐
              │ Financial Model    │
              │ Engine             │
              └─────────┬──────────┘
                        │
     ┌──────────────────┼──────────────────┐
     │                  │                  │
     ▼                  ▼                  ▼
┌──────────┐    ┌─────────────┐    ┌────────────┐
│ Causal   │    │ State       │    │ Evidence   │
│ Critic   │    │ Verifier    │    │ Ledger     │
└────┬─────┘    └──────┬──────┘    └─────┬──────┘
     │                 │                  │
     └─────────────────┼──────────────────┘
                       │
            ┌──────────▼──────────┐
            │ Final Output        │
            │ (Memo + Model +     │
            │  Risk Register)     │
            └─────────────────────┘
```

---

## 10. 两周详细执行计划

### Week 1：核心链路搭建

#### Day 1 (8/29 Sat)：项目启动 + 数据收集

**全员任务：**
- [ ] 确认最终项目名和定位
- [ ] 确认案例：绿的谐波
- [ ] 建立 GitHub 仓库（或本地目录）
- [ ] 创建数据目录结构

**具体分工：**
- Chen Luodi：初始化项目 repo，搭建 Python 环境，安装依赖
- 西交经济金融：收集绿的谐波年报、公告、研报
- 机械成员：搜索绿的谐波产品 datasheet、展会资料
- 电气成员：搜索电机/减速器技术参数、竞争对手资料
- 孙圣尧：设计 benchmark 框架初稿

**当日交付：**
- `data/raw/company_filings/` 至少 3 份 PDF
- `data/raw/datasheets/` 至少 2 份 PDF
- 项目初始化完成

#### Day 2 (8/30 Sun)：案例深度理解 + 手工标注

**目标：** 手工走一遍完整链路，形成 ground truth。

**任务：**
- [ ] 提取绿的谐波的关键技术 claim（ torque density 提升、产能扩张、客户进展）
- [ ] 手工标注每个 claim 的证据来源
- [ ] 手工推导技术→成本→毛利率→估值的影响
- [ ] 形成 1 页案例分析模板

**分工：**
- 西交经济金融：主导案例分析，输出财务影响估算
- 机械+电气：验证技术参数的 engineering interpretation
- 孙圣尧：记录 claim → evidence → verification 的 trace
- Chen Luodi：把手工案例结构化到 JSON

**当日交付：**
- `data/processed/green_harmonic_case_study.json`
- 手写财务影响计算 Excel

#### Day 3 (8/31 Mon)：Claim Extraction + Evidence Retrieval 模块

**任务：**
- [ ] 实现 Claim Extractor（从文本提取 claim、主体、数值、比较基准）
- [ ] 实现 Evidence Retriever（RAG + web search 模拟）
- [ ] 实现 Evidence Ledger 数据结构

**分工：**
- Chen Luodi：实现 extractor 和 retriever 的 scaffold
- 孙圣尧：设计 evidence trace 数据模型
- 西交经济金融：提供 5–10 个测试 claim

**当日交付：**
- `src/claim_extractor.py`
- `src/evidence_retriever.py`
- `src/evidence_ledger.py`

#### Day 4 (9/1 Tue)：Claim Verification 模块

**任务：**
- [ ] 实现 Claim Verifier（验证 claim 是否成立、definition mismatch、证据强度）
- [ ] 实现 numerical claim verification 的基础逻辑
- [ ] 跑通 3–5 个测试 case

**分工：**
- 孙圣尧：主导 verification logic，参考 DebateCV / Multi-Tool Verifiable Misinformation
- Chen Luodi：接入 LLM API
- 机械+电气：提供参数口径判断规则

**当日交付：**
- `src/claim_verifier.py`
- 3–5 个验证测试通过

#### Day 5 (9/2 Wed)：Engineering Analyzer 模块

**任务：**
- [ ] 实现 Engineering Analyzer（拆解 torque density 来源、trade-offs）
- [ ] 构建技术参数对比表
- [ ] 实现竞争对手参数匹配

**分工：**
- 机械成员：减速器/结构部分
- 电气成员：电机/驱动部分
- Chen Luodi：把规则代码化
- 西交经济金融：把 engineering output 映射到经济参数

**当日交付：**
- `src/engineering_analyzer.py`
- `data/processed/parameter_comparison.csv`

#### Day 6 (9/3 Thu)：Economic Mechanism Mapper

**任务：**
- [ ] 实现技术参数 → 单位经济参数的映射规则
- [ ] 定义 mapping ontology
- [ ] 输出 economic impact 假设

**分工：**
- 西交经济金融：主导 economic mechanism 设计
- 机械+电气：验证 mapping 的工程合理性
- Chen Luodi：把规则结构化

**当日交付：**
- `src/economic_mapper.py`
- `data/processed/tech_to_economics_ontology.json`

#### Day 7 (9/4 Fri)：Financial Model Engine

**任务：**
- [ ] 实现简化财务模型（Revenue → COGS → Gross Margin → EBITDA → FCF → Valuation）
- [ ] 输出 Excel 模型
- [ ] 实现 sensitivity analysis

**分工：**
- 西交经济金融：设计模型公式和假设
- Chen Luodi：用 Python/openpyxl 实现
- 孙圣尧：做 state verification 的初步接入

**当日交付：**
- `src/financial_model.py`
- `data/processed/green_harmonic_model.xlsx`

### Week 2：Agent 集成 + Demo + 材料

#### Day 8 (9/5 Sat)：Agent Orchestration（LangGraph）

**任务：**
- [ ] 用 LangGraph 把各模块串成 workflow
- [ ] 实现状态管理
- [ ] 跑通端到端一个案例

**分工：**
- Chen Luodi：主导 LangGraph 实现
- 孙圣尧：设计 state schema
- 其他成员：准备测试输入

**当日交付：**
- `src/agent_workflow.py`
- 端到端案例跑通

#### Day 9 (9/6 Sun)：Causal Financial Critic 模块

**任务：**
- [ ] 实现 Causal Critic Agent
- [ ] 输出替代解释清单
- [ ] 设计反事实证据需求

**分工：**
- 西交经济金融：主导 causal criticism 逻辑
- 孙圣尧：把 critic 接入 workflow
- Chen Luodi：实现输出格式

**当日交付：**
- `src/causal_critic.py`
- Critic 输出示例 3 个

#### Day 10 (9/7 Mon)：State-Aware Financial Agent 模块

**任务：**
- [ ] 实现 tool call 后的 expected vs observed state 检查
- [ ] 实现 clarify/retry/rollback 逻辑
- [ ] 在 Excel 更新场景中测试

**分工：**
- 孙圣尧：主导 state verification 逻辑
- Chen Luodi：接入 financial model tool
- 西交经济金融：定义 expected state

**当日交付：**
- `src/state_verifier.py`
- Excel 更新验证测试通过

#### Day 11 (9/8 Tue)：Benchmark 构建 + 测试

**任务：**
- [ ] 构建 5 层 benchmark（claim/Agent reliability/engineering/economic/financial）
- [ ] 手工标注 5–10 个 test cases
- [ ] 与 baseline（GPT direct, Ling-Fin direct）对比

**分工：**
- 孙圣尧：主导 benchmark 设计
- 西交经济金融：提供金融/经济 ground truth
- 机械+电气：提供工程 ground truth
- Chen Luodi：跑 benchmark 脚本

**当日交付：**
- `benchmarks/` 目录下的测试集
- benchmark 结果报告

#### Day 12 (9/9 Wed)：Demo 开发 + Bug 修复

**任务：**
- [ ] 用 Streamlit/Gradio 做 Web Demo
- [ ] 美化输出：证据链、工程分析、财务影响、Critic
- [ ] 修复主要 bug

**分工：**
- Chen Luodi：前端实现
- 孙圣尧：验证 state verification 在 Demo 中的表现
- 西交经济金融：验证输出金融逻辑

**当日交付：**
- `app.py`
- 可运行的 Demo

#### Day 13 (9/10 Thu)：项目材料 + 提交

**任务：**
- [ ] 准备项目书/PPT（PDF/Word/PPT，<5MB）
- [ ] 准备演示视频（可选）
- [ ] 提交报名
- [ ] 整理代码仓库

**分工：**
- 西交经济金融：项目书/PPT 主笔
- 孙圣尧：整理 benchmark 和 verification 亮点
- Chen Luodi：整理代码和 README
- 机械+电气：提供技术参数说明

**当日交付：**
- 项目提交材料
- GitHub README

---

## 11. 成员分工矩阵

| 成员 | 主要职责 | Week 1 重点 | Week 2 重点 |
|---|---|---|---|
| **西交经济金融** | Economic & Financial Intelligence Lead | 案例分析、economic mechanism、财务模型 | Causal Critic、项目书、benchmark ground truth |
| **孙圣尧** | Agent Reliability & Evaluation Lead | Claim Verification、evidence trace、benchmark 设计 | State Verification、benchmark 执行、Demo 验证 |
| **Chen Luodi** | AI Systems & Agent Engineering Lead | 项目搭建、extractor/retriever/verifier、orchestration | LangGraph、前端 Demo、bug 修复 |
| **电气成员** | Electrical Engineering Ground Truth | 电机/电驱参数、竞争对手电气参数 | Engineering Analyzer 电气规则验证 |
| **机械成员** | Mechanical / Manufacturing Ground Truth | 减速器/机器人结构、BOM | Engineering Analyzer 机械规则验证 |

---

## 12. 代码目录结构

```
claim2value/
├── README.md
├── requirements.txt
├── app.py                      # Streamlit/Gradio Demo
├── src/
│   ├── __init__.py
│   ├── config.py              # API keys, model endpoints
│   ├── models.py              # LLM router
│   ├── claim_extractor.py     # Claim 提取
│   ├── evidence_retriever.py  # 证据检索
│   ├── evidence_ledger.py     # 证据账本
│   ├── claim_verifier.py      # Claim 验证
│   ├── engineering_analyzer.py # 工程分析
│   ├── economic_mapper.py     # 经济机制映射
│   ├── financial_model.py     # 财务模型
│   ├── causal_critic.py       # 因果批判
│   ├── state_verifier.py      # 状态验证
│   ├── workflow.py            # LangGraph workflow
│   └── utils.py               # 工具函数
├── data/
│   ├── raw/                   # PDF/原始资料
│   └── processed/             # 结构化数据
├── benchmarks/
│   ├── claim_verification.json
│   ├── engineering_accuracy.json
│   ├── economic_reasoning.json
│   └── financial_accuracy.json
└── notebooks/
    └── case_study.ipynb       # 案例分析笔记本
```

---

## 13. Benchmark 设计

### 13.1 五层 Benchmark

| 层级 | 指标 | 测试方法 |
|---|---|---|
| **L1 Claim Verification** | claim accuracy, source correctness, contradiction detection, definition mismatch | 10 个 claim，人工标注 truth |
| **L2 Agent Reliability** | tool success rate, state mismatch detection, recovery success | 注入 5 种 tool failure |
| **L3 Engineering Accuracy** | parameter extraction accuracy, trade-off recognition, comparison correctness | 5 组 datasheet 对比 |
| **L4 Economic Reasoning** | mechanism validity, alternative explanation coverage, counterfactual quality | 3 个 case 的人工评分 |
| **L5 Financial Accuracy** | unit economics, margin, FCF, valuation calculation accuracy | 与手工 Excel 对比 |

### 13.2 Baseline 对比

- **Baseline 1**: GPT-4o direct（直接问技术升级对估值的影响）
- **Baseline 2**: Ling-3.0-flash-Fin direct（如果可用）
- **Baseline 3**: Generic RAG（只检索财报和新闻）
- **Our System**: Claim2Value

### 13.3 关键评估问题

1. 系统是否比直接问 LLM 更准确？
2. 每个金融结论是否都能追溯到证据？
3. 系统能否识别 definition mismatch？
4. Critic 是否能发现合理的替代解释？
5. State Verifier 能否捕获 Excel 更新失败？

---

## 14. 关键设计决策

### 14.1 用 LangGraph 而非纯 LangChain

理由：
- 需要显式 state management
- 适合 verification loop 和 retry 逻辑
- 孙圣尧的 state verification 研究容易落地

### 14.2 不做自己训练模型

理由：
- 时间不够
- 赛道一不要求 foundation model
- 用模型 router 即可体现创新

### 14.3 先做机器人关节，不做多行业

理由：
- 2 周必须聚焦
- 团队机械/电气背景最匹配
- 案例数据最丰富

### 14.4 Excel + Python 混合财务模型

理由：
- Excel 是金融从业者熟悉格式
- Python 保证计算可复现
- 符合 ModelForge 的可审计思想

---

## 15. 备选方案

### 15.1 如果 Claim2Value 进度不及预期

**Plan B：强化 State-Aware Financial Agent 模块**
- 弱化 engineering 层
-  focus 在 Excel/数据库 tool 调用后的状态验证
-  still 报赛道一，但场景改为 generic financial workflow

### 15.2 如果数据获取困难

**Plan C：用合成数据 + 手工标注**
- 构造 10 个 synthetic claim cases
- 手工标注所有 ground truth
- 重点展示 system architecture 和 verification

### 15.3 如果评委质疑商业价值

**Plan D：强调 efficiency gain**
- 人工分析师：50 min/task
- Claim2Value：8 min/task
- 准确率从 75% 提升到 90%（预估，需 benchmark 支撑）

---

## 16. 提交材料清单

### 16.1 代码

- [ ] GitHub 仓库链接
- [ ] README.md（包含安装、运行、案例说明）
- [ ] requirements.txt
- [ ] 可运行的 Demo（app.py）

### 16.2 文档

- [ ] 项目书/PPT（<5MB）
- [ ] 技术方案说明
- [ ] Benchmark 报告
- [ ] 团队介绍

### 16.3 演示

- [ ] 演示视频（2–3 分钟，可选但推荐）
- [ ] 现场 Demo 备用 case

---

## 17. 每日站会建议

每晚 22:00 线上同步 30 分钟：
1. 今天完成了什么？
2. 阻塞问题是什么？
3. 明天计划做什么？
4. 是否需要调整范围？

---

## 18. 最终成功标准

1. **功能成功**：Demo 能跑通绿的谐波案例端到端
2. **验证成功**：每个金融结论可追溯
3. **创新成功**：Causal Critic 和 State Verifier 能展示
4. **benchmark 成功**：至少 5 个 test cases 有结果
5. **提交成功**：在 9/10 前完成所有材料提交

---

## 19. 总结

**Claim2Value 是可行、创新、且高度匹配团队的。**

关键成功因素：
1. 严格聚焦：机器人关节 + 绿的谐波
2. 发挥跨学科优势：Agent 可靠性 + 经济因果 + 工程 ground truth
3. 快速原型：先手工 case，再逐步自动化
4. 可验证性：多层 benchmark + evidence ledger
5. 时间纪律：每日站会 + 范围控制

如果严格执行本计划，2 周内可以产出：
- 一个可运行的 Agent 系统 Demo
- 一套多层 benchmark
- 一份有竞争力的项目书
- 一个清晰的商业/技术叙事
