# 北大金融 AI 智能体大赛：核心成员能力画像与项目定位修正版

> 整理时间：2026-08-28  
> 用途：供团队成员、Claude Code、Kimi 等继续进行选题、架构设计和竞品调研。  
> 说明：本文件基于既往对话、科研简历和已有项目记录，对团队中两位主要成员——西交经济/金融方向成员与上交 SPEIT 孙圣尧——进行更细粒度画像，并据此修正此前较粗糙的“金融 / Agent / 计算机 / 电气 / 机械”式分工。

---

# 0. 最重要的修正

此前我们把团队大致概括成：

- 经济 / 金融
- AI / Agent
- 计算机
- 电气
- 机械
- 语言

这个概括没有错，但太粗。

重新梳理既往记录后，更准确的判断是：

> **你们最有价值的地方，不只是学科多元，而是各自已经形成了不同的“验证型研究能力”，并且这些能力恰好可以接成一条完整的工业金融 Agent pipeline。**

特别是两位核心成员：

## 西交经济 / 金融方向成员

最强项并不是泛泛的“懂金融”，而是：

> **经济机制建模 + 实证识别 + 因果推断 + 产业/政策解释 + 金融映射**

## 上交 SPEIT 孙圣尧

最强项也不是泛泛的“会 Agent”，而是：

> **Agent Reliability + Agent Evaluation + Tool-state Verification + Benchmark Design + Structured Output Robustness**

因此两个人最有意思的共同点是：

> **都是“验证派”。**

只是验证对象不同。

---

# 1. 西交经济 / 金融方向成员：更准确的能力画像

## 1.1 不是普通“商科 / 金融同学”

既往完整研究记录显示，已经做过相当系统的经济学研究流程。

代表性项目：

> **《大语言模型冲击下高校本科专业结构的适应性调整——理论建模、LLM 暴露度测度与连续双重差分实证》**

研究内容包括：

- 将 Acemoglu & Restrepo 的 task model 扩展到高等教育供给侧
- 构建职业暴露度 → 本科专业的 Crosswalk
- 将 101 个职业暴露度映射至 889 个本科专业
- 使用 2015–2024 年全国专业备案与审批面板
- 使用 27 省 2017–2024 年招生计划数据
- 数据规模约 434 万条记录

使用的方法包括：

- Continuous DID
- Event Study
- Dose-response
- Causal Forest
- Wild Cluster Bootstrap
- Trend-adjusted DID

## 1.2 一个特别重要的研究风格

基准 Continuous DID 曾出现大约：

```text
LLM exposure +1 SD
→ post-period enrollment ≈ -8.5%
```

但进一步做去趋势 DID 后：

```text
effect ≈ +0.022
p = 0.591
```

即：

> 原本看起来很漂亮的负效应，在更严格的趋势控制以后基本消失。

这说明一个很重要的研究习惯：

> **不因为结果“好看”就停止，而会继续检查：这个结果到底是不是因果？**

这种习惯可以迁移到比赛：

看到：

> “技术性能提高 20%”

不能直接推出：

> “盈利提高 20%”

而应该继续问：

- 对照组是什么？
- 是否存在同期需求景气？
- 是否伴随成本上升？
- 是否存在产能变化？
- 是否已有行业趋势？
- 是否存在替代解释？
- 真正 causal channel 是什么？

---

# 2. 西交成员的核心优势重新定义

更准确的能力标签是：

## Economic & Financial Intelligence

包括：

### 经济机制

```text
Technology
→ Productivity
→ Cost / Capacity / Demand
→ Firm Behavior
→ Financial Outcome
```

### 因果识别

关注：

- correlation vs causality
- confounders
- counterfactual
- pre-trend
- alternative mechanisms
- heterogeneous effects
- robustness

### 数据 / 实证

已经接触：

- panel data
- large-scale data construction
- crosswalk
- DID
- bootstrap
- causal forest
- event study

### 金融与产业解释

长期学习和讨论：

- Macro
- Micro
- Corporate Finance
- Investment
- International Finance
- Industrial Organization
- Econometrics
- Causal Inference
- Policy / Industry

并开始接触金融机构宏观研究环境。

---

# 3. 这一成员最适合在比赛中做什么

不应该只是：

> “负责金融业务和 BP。”

更合理的是：

# Economic & Financial Reasoning Lead

负责：

- use-case definition
- economic mechanism
- financial logic
- industry analysis
- policy interpretation
- causal chain
- counterfactual design
- valuation model specification
- financial benchmark validity
- scenario design
- commercial value

尤其可以设计一个非常有经济学特色的模块：

# Economic Critic Agent

它不是普通：

> Bear Agent / 看空 Agent

而是：

> **Causal Chain Critic**

例如：

```text
Claim:
新一代机器人关节发布
→ 2027 销量 +25%
```

Economic Critic 会问：

```text
Evidence insufficient.

Alternative explanations:
1. industry-wide demand growth
2. subsidy
3. capacity expansion
4. channel inventory
5. price reduction

Need:
- counterfactual
- competitor comparison
- pre-existing trend
- capacity evidence
```

这比简单“正方 Agent / 反方 Agent”更有学术和产业含量。

---

# 4. 上交 SPEIT 孙圣尧：更准确的能力画像

## 4.1 基本背景

上海交通大学巴黎卓越工程师学院（SPEIT）本科生。

训练体系：

- mathematics
- physics
- computer science
- engineering

未来更偏：

- mechanical engineering
- embodied intelligence
- robot learning

语言：

- CET-6 635
- French Early B1

但真正值得重视的不是专业名称，而是已经做过的 Agent research。

---

# 5. 孙圣尧现有三条重要 Agent 研究线

## 5.1 Ambiguous Tool Outcomes

代表项目：

> **Did It Happen? Counterfactual Evaluation of LLM Agent Recovery from Ambiguous Tool Outcomes**

核心问题：

> Agent 调用了一个工具以后，它是否真的知道环境发生了什么？

测试：

- ambiguous tool result
- clarification
- verification
- failure recovery
- environment state judgment

核心思想：

```text
Agent action
→ Tool result
→ Actual environment state
```

三者未必一致。

例如金融场景：

```text
Agent:
“更新 Excel 模型”

Tool:
“Operation completed”

Actual:
部分 cell 未更新
公式被破坏
文件未保存
sheet 错误
```

普通 Agent 可能继续运行。

这个研究恰恰关注：

> **Agent 如何确认操作真的成功。**

---

# 6. Benchmark Oracle / Mutation Testing

另一个研究方向：

> **Mutation Testing of Task-Scoped State Oracles in Software-Agent Benchmarks**

核心不是：

> Agent 是否通过 benchmark？

而是进一步问：

> **Benchmark 自己到底有没有能力正确判断 Agent 是否成功？**

方法：

人为制造：

- harmful state
- benign transformation
- hidden side effect
- abnormal environment state

然后检查 evaluator / oracle 是否能识别。

这使孙圣尧的能力更接近：

# Agent Evaluation & Reliability Research

而不是普通 Agent application development。

---

# 7. Structured Output Robustness

第三条研究：

> **Testing JSON Schema Instruction Artifacts**

研究问题：

如果两个 JSON Schema：

- validation-equivalent
- 语义等价
- 只是 serialization order 不同

模型输出分布是否会变化？

涉及：

- JSON Mode
- structured generation
- schema instruction design
- representation sensitivity
- distributional robustness

这个能力对于真实 Financial Agent 很重要，因为系统往往是：

```text
LLM
→ Structured JSON
→ Tool
→ Database
→ Financial Model
→ Another Agent
```

如果 structured output 不稳：

> 整个 workflow 都会不稳。

---

# 8. 孙圣尧不是“全栈工程师”的简单替代

这一点需要特别修正。

他的科研很明确，但根据简历：

- Python
- C++ basic working proficiency
- Ubuntu / Conda / tmux 基础
- 正在持续补科研开发工作流

因此不应该因为：

> 有多篇 Agent benchmark 项目

就直接假设：

> 他是团队最强 backend / infra / production engineer。

更准确的角色是：

# Agent Reliability & Evaluation Lead

而真正重的：

- backend
- RAG
- infra
- deployment
- data pipeline
- model serving

可能更适合团队中的西交计算机成员承担。

---

# 9. 孙圣尧还有一个重要的“实体世界”优势

做过：

> VEX V5 Robotics

经历包括：

- team programmer
- operator
- C++
- VEXcode
- four-motor differential drive
- joystick dead-zone
- speed switching
- intake / launcher
- autonomous routines
- PID
- autonomous pickup / collect / delivery
- real-world measurement
- repeated trial-and-error
- hardware/software integration

这意味着他的研究路线实际上可以连成：

```text
Software Agent
→ Tool Action
→ Environment State
→ Verification
```

进一步延伸：

```text
Embodied Agent
→ Physical Action
→ Physical World
→ Verification
```

而这和工业金融方向意外地很搭。

---

# 10. 两位核心成员真正的互补关系

| 维度 | 西交经济金融成员 | 孙圣尧 |
|---|---|---|
| 学科底层 | Economics / Finance | Engineering / AI |
| 最强方法 | Causal inference / empirical identification | Agent evaluation / benchmarking |
| 核心问题 | “这个经济效应真的是因果吗？” | “这个 Agent 真的完成任务了吗？” |
| 数据 | Panel / econometrics / crosswalk | LLM experiment / benchmark pipeline |
| Verification | robustness / identification | state verification / oracle |
| 模型 | economic mechanism | agent behavior |
| 实体世界 | industry / firm / policy | robot / tool / environment |
| 金融适配 | 强 | 需要金融成员补 |
| Agent适配 | 产品 / reasoning | 研究层强 |
| 推荐角色 | Economic & Financial Intelligence Lead | Agent Reliability & Evaluation Lead |

---

# 11. 最关键的新发现：两个人都是“验证派”

西交成员问：

```text
X → Y
```

到底是不是因果？

孙圣尧问：

```text
Agent Action → Environment State
```

到底是不是真的发生？

本质上都是：

# Verification

因此团队的核心主题不一定应该是：

> Multi-Agent Collaboration

反而可能是：

> **Evidence + Verification + Consequence**

---

# 12. 由此修正项目母题

此前母题：

> **让金融 Agent 理解实体工业世界。**

这仍然成立。

但现在可以进一步精确成：

> **让金融 Agent 验证一个工业技术 Claim 是否成立，并严谨地识别它如何传导成经济与金融后果。**

可以叫：

# Claim2Value

英文副标题：

> **Evidence-Grounded Engineering-to-Finance Agent**

---

# 13. Claim2Value 核心链路

```text
Claim
 ↓
Evidence
 ↓
Physical / Engineering State
 ↓
Economic Mechanism
 ↓
Financial Impact
```

数学化：

```text
Claim
→ Evidence
→ Engineering Ground Truth
→ Unit Economics
→ Financial Statement
→ Valuation / Risk
```

---

# 14. 一个真实例子

企业公告：

> “新一代机器人关节模组扭矩密度提升 30%。”

普通金融 Agent：

```text
技术性能提升
→ 公司竞争力提高
→ 看好
```

我们系统：

---

## Step 1 — Claim Verification

由 Agent Reliability / Evidence 系统处理：

```text
Claim:
Torque density +30%

Sources:
- company datasheet
- patent
- competitor datasheet
- third-party material

Questions:
- compared with which generation?
- same operating condition?
- continuous torque or peak torque?
- same mass definition?
- thermal constraint?
```

输出：

```text
Claim validity:
Partially supported

Confidence:
0.81
```

---

## Step 2 — Engineering Ground Truth

机械 / 电气成员定义：

```text
+30% comes from:
motor?
reducer?
material?
thermal design?
control?
```

并检查：

- trade-off
- efficiency
- cost
- lifetime
- weight
- thermal
- reliability

---

## Step 3 — Economic Mechanism

西交经济成员负责：

技术提高后，到底影响什么？

```text
Technology
 ↓
Cost?
ASP?
Demand?
Capacity?
Yield?
CapEx?
Replacement cycle?
```

而不是：

> 技术提高 = 盈利提高

---

## Step 4 — Financial Mapping

```text
Units × ASP
→ Revenue

BOM + Yield + Capacity
→ COGS

Revenue - COGS
→ Gross Margin

Operating Model
→ EBITDA / FCF

FCF
→ Valuation
```

---

# 15. 为什么这比普通金融 Agent 更有辨识度

典型金融 Agent：

```text
Financial Statement
News
Market Data
 ↓
Investment View
```

我们的系统：

```text
Technology Claim
Patent
Datasheet
Engineering Parameter
Supply Chain
 ↓
Verification
 ↓
Physical Meaning
 ↓
Economic Mechanism
 ↓
Financial Model
 ↓
Decision
```

也就是：

> **别人分析“公司说了什么”，我们分析“公司说的是不是真的，以及如果是真的，到底值多少钱”。**

---

# 16. 推荐的团队结构修正版

## 西交经济 / 金融成员

### Economic & Financial Intelligence Lead

负责：

- problem definition
- economic mechanism
- causal chain
- industry economics
- policy
- counterfactual
- valuation
- scenario
- finance benchmark
- commercial value

---

## 孙圣尧

### Agent Reliability & Evaluation Lead

负责：

- state verification
- tool-result ambiguity
- failure recovery
- evaluator / oracle
- benchmark
- adversarial test
- structured output
- reproducibility
- model comparison

---

## Chen Luodi / 西交计算机成员

暂时更建议：

### AI Systems & Agent Engineering Lead

负责：

- orchestration
- backend
- retrieval
- RAG
- model router
- agent harness
- tool integration
- database
- deployment
- system implementation

---

## 电气成员

### Electrical Engineering Ground Truth

负责：

- motor
- power electronics
- electrical system
- energy efficiency
- electrical equipment
- engineering validation

---

## 机械成员

### Mechanical / Manufacturing Ground Truth

负责：

- robot
- structure
- mechanical system
- BOM
- manufacturing
- process
- production line
- engineering benchmark

---

# 17. 团队整体能力链

目前最理想的 pipeline：

```text
AI System
 ↓
Agent Reliability
 ↓
Engineering Ground Truth
 ↓
Economic Mechanism
 ↓
Financial Model
 ↓
Decision
```

或者：

```text
Chen Luodi
System / Infrastructure
 ↓
Sun Shengyao
Agent Verification
 ↓
Electrical + Mechanical
Engineering Validation
 ↓
Economics / Finance
Economic Consequence
 ↓
Product
Financial Decision
```

---

# 18. 这意味着选题应该避免什么

## 不推荐 1

```text
Fundamental Agent
Technical Agent
News Agent
Sentiment Agent
Risk Agent
PM
```

原因：

> 已经高度同质化。

---

## 不推荐 2

纯粹：

> AI Hedge Fund

除非有极强的 Quant / Alpha 创新。

---

## 不推荐 3

纯 Agent 架构论文

例如：

> 新设计一种 multi-agent communication protocol

如果缺少实际金融产品和用户价值，比赛优势有限。

---

## 不推荐 4

只做漂亮 UI

没有：

- benchmark
- validation
- evidence
- real finance workflow

不够。

---

# 19. 更值得考虑的三类项目

## A. Claim2Value

### Industrial Technology Claim → Financial Value

推荐度：★★★★★

---

## B. SupplyChain2Risk

### Supply-chain event → physical exposure → financial risk

推荐度：★★★★☆

---

## C. ProjectFinance Agent

### Engineering project → CAPEX/OPEX → IRR/NPV/DSCR

推荐度：★★★★☆

---

# 20. Claim2Value 的 benchmark 可以很有特色

## Layer 1 — Claim Verification

指标：

- claim accuracy
- source correctness
- source authority
- contradiction detection
- definition mismatch detection

---

## Layer 2 — Agent Reliability

测试：

- ambiguous tool outcome
- tool failure
- partial success
- stale state
- hidden side effect

---

## Layer 3 — Engineering Accuracy

- parameter extraction
- technical interpretation
- trade-off recognition
- product comparison

---

## Layer 4 — Economic Reasoning

- mechanism validity
- alternative explanation
- causal chain completeness
- counterfactual quality

---

## Layer 5 — Financial Accuracy

- unit economics
- revenue
- COGS
- margin
- FCF
- NPV / IRR
- valuation

---

# 21. 一个非常适合你们的创新模块

# Causal Financial Critic

输入：

```text
Claim:
技术升级
→ Revenue +20%
```

输出：

```text
Causal chain not established.

Possible confounders:
- market growth
- capacity expansion
- subsidy
- lower ASP
- channel inventory

Required evidence:
- competitor comparison
- pre/post data
- capacity data
- pricing
- order backlog
```

这可能是团队经济学背景最容易做出差异化的模块之一。

---

# 22. 另一个适合孙圣尧的创新模块

# State-Aware Financial Agent

每一次 tool call 后：

```text
Action
 ↓
Expected State
 ↓
Observed State
 ↓
Verification
```

如果：

```text
Expected ≠ Observed
```

则：

```text
Clarify
Retry
Rollback
Escalate
```

尤其适合：

- Excel
- database
- financial model
- document processing
- portfolio update
- workflow automation

---

# 23. 两个模块结合

最终系统不是普通：

```text
Agent → Tool → Answer
```

而是：

```text
Claim
 ↓
Evidence Verification
 ↓
Engineering Validation
 ↓
Economic Critic
 ↓
Financial Model
 ↓
State Verification
 ↓
Final Output
```

这是非常“像你们”的架构。

---

# 24. 一句话项目叙事

推荐：

> **别人让 AI 看懂财报，我们让 AI 验证技术、理解工程、识别经济机制，并算清楚它到底值多少钱。**

英文：

> **From claim to evidence, from engineering to value.**

或：

> **Financial agents that verify the physical world before pricing it.**

---

# 25. 给 Claude Code / Kimi 的继续讨论提示词

```text
我们正在参加北京大学金融 AI 智能体创新大赛，倾向赛道一。

请不要把我们的团队简单理解成“金融 + AI + 电气 + 机械”。

两个核心成员的真实特点是：

成员 A：
- 西安交通大学经济/金融方向
- 做过 LLM 冲击与高校专业结构的经济学研究
- 有 theory + Continuous DID + event study + causal forest + bootstrap + large panel data 经验
- 思维特点是 economic mechanism、causal inference、counterfactual、robustness
- 适合作为 Economic & Financial Intelligence Lead

成员 B：孙圣尧
- 上海交通大学巴黎卓越工程师学院
- 做过 LLM Agent ambiguous tool outcomes benchmark
- 做过 software-agent benchmark oracle mutation testing
- 做过 JSON Schema structured-output robustness
- 有 VEX 机器人、PID、自动控制、软硬件协同经历
- 适合作为 Agent Reliability & Evaluation Lead，而不是简单 full-stack engineer

另外：
- 一位西交计算机成员可承担 AI Systems / Agent Engineering
- 一位电气成员
- 一位机械成员

我们当前认为团队真正的共同优势是“Verification”：

经济成员：
验证经济效应是否真有 causal relation

Agent 成员：
验证 Agent action 是否真的导致预期 environment state

因此项目方向从普通 Industrial-Finance Agent 进一步精炼为：

Claim2Value
Evidence-Grounded Engineering-to-Finance Agent

核心链：

Claim
→ Evidence
→ Engineering Ground Truth
→ Economic Mechanism
→ Financial Impact

候选例子：
企业声称“新机器人关节 torque density +30%”
系统首先验证 claim 是否成立，再分析工程 trade-off、供应链、BOM、成本、ASP、产能，最终映射到 margin / FCF / valuation。

请基于这一更精确的团队画像：
1. 批判性评估 Claim2Value 是否真的有创新性；
2. 搜索 GitHub / arXiv / Hugging Face / startup / financial product 是否已有高度类似方案；
3. 找真正未解决的 gap；
4. 设计一个两周左右能完成的 MVP；
5. 明确哪些部分由各成员负责；
6. 设计 benchmark：
   - claim verification
   - state verification
   - engineering accuracy
   - economic causal reasoning
   - financial calculation
7. 不要为了 multi-agent 而 multi-agent；
8. 产品必须有真实金融 work product 和 Demo。
```

---

# 26. 当前最终判断

重新审视个人经历后，团队最稀缺的不是：

> “五个专业不同的人。”

而是：

> **Agent 系统工程 + Agent 可靠性验证 + 工程 Ground Truth + 经济因果机制 + 金融决策**

这条链几乎可以自然映射到每个成员。

因此后续选题时，应优先寻找：

> **只有同时具备技术验证、工程理解、经济机制和金融建模能力才容易做好的问题。**

而不是寻找：

> “一个金融 Agent 能做什么？”

这是接下来所有项目筛选最重要的原则。
