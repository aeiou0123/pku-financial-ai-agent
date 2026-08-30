# 北京大学金融 AI 智能体创新大赛：团队讨论记录与项目方向备忘

> 用途：供团队成员、Kimi / Claude Code 等继续讨论、检索和方案设计。  
> 整理时间：2026-08-28  
> 说明：本文不是逐字聊天转录，而是对本轮讨论的完整结构化整理。涉及赛事规则、模型发布时间、免费额度、GitHub 项目现状等动态信息，后续正式申报前应再次以官方页面和项目仓库为准。

---

# 0. 当前最重要的结论

经过多轮讨论，目前形成的核心判断如下：

1. **我们更适合优先参加赛道一：金融 AI 智能体算法与应用创新。**
2. 赛道一**并不要求自己从头训练一个金融大模型**。完全可以把 GPT、Claude、Gemini、Qwen、DeepSeek、Ling-Fin 等模型当成可替换的底层推理引擎。
3. 真正需要体现技术与创新的，是：
   - Agent architecture
   - workflow / orchestration
   - tool use
   - memory
   - multi-agent collaboration
   - verification / critic
   - evidence tracing
   - temporal consistency
   - benchmark / evaluation
   - 产品化与真实金融场景价值
4. 不能只做“多个 Agent 聊股票”或“AI 炒股”。这一方向已非常拥挤，TradingAgents、FinRobot、RD-Agent 等已经覆盖大量典型结构。
5. 我们团队的独特优势不是“会搭 Agent”，而是：
   - 经济 / 金融
   - AI / Agent / 计算机
   - 工业工程相关背景（电气、机械）
   - 语言 / 跨语言资料能力
6. 因此目前最值得深入的项目母题是：

> **让金融 Agent 真正理解实体工业世界。**

即：

> **Engineering / Technology → Industry / Supply Chain → Economics → Finance**

而不是只做：

> 财报 / 新闻 / 行情 → 金融结论

7. 当前第一推荐方向：

> **Industrial-Tech-to-Finance Agent / 工业科技金融智能体**

它能读取技术参数、专利、设备规格、BOM、供应链、产能、材料、海外技术文件等，并将工程变化翻译为成本、产能、毛利率、现金流、估值、风险等金融结果。

8. 目前最值得参考的开源项目，不是找一个完整成品照抄，而是从不同项目拆模块：
   - Sanjaya AI：跨领域 Master Agent 架构
   - ModelForge：可审计金融模型与 deterministic verification
   - SupplyChainCortex：供应链工具层与风险分析
   - DisruptIQ：知识图谱与风险传播
   - Academic Commercialization Agent：技术→商业化
   - PatentAgent：专利与技术证据
   - Due-diligence-engine：技术 claim verification
   - Anthropic Financial Services：真实金融工作流拆解
   - Meridian：贸易金融规则 + Agent
   - RD-Agent(Q)：research–experiment–feedback loop
   - TradingAgents / FinRobot：作为 baseline 和“已被做烂的方向”参考

---

# 1. 比赛基本判断

我们讨论并定位到的赛事是：

**北京大学金融 AI 智能体创新大赛**

讨论中检索到的信息显示，它与以下单位相关：

- 北京大学创新创业学院
- 北京大学创业训练营
- 北京大学金融工程实验室
- BigQuant / 宽邦科技等

比赛并不是传统 Kaggle 式固定数据集算法赛，更接近：

> **AI Agent × Finance × Product × Entrepreneurship**

核心不只是模型分数，而是：

- 技术创新
- 落地价值
- 商业潜力
- 产品 Demo
- 场景合理性
- 可验证性

## 1.1 三个方向

### 赛道一：金融 AI 智能体算法与应用创新

讨论中将其理解为：

> 智能算法、模型架构与金融应用创新。

可做：

- 金融 Research Agent
- 投研分析 Agent
- 多 Agent 金融系统
- 金融 workflow Agent
- 风控 / 投顾 / 金融工具 Agent
- 可靠性 / verification / planning / memory / tool-use 方向

### 赛道二：量化投资策略与金融科技工具研发

核心不是 Agent，而是 Quant：

- Alpha / factor
- ML / DL 量化策略
- Portfolio construction
- Backtest
- Risk
- IC / ICIR
- Sharpe
- Turnover
- transaction cost
- research tools

一个简单判断：

> **如果把 Agent 去掉，项目核心仍然成立，则更偏赛道二。**

### 赛道三：金融 AI 智能体行业场景落地

更偏具体业务：

- 银行
- 保险
- 券商
- 合规
- KYC / AML
- 客服
- 财富管理
- 运营
- 企业金融

难点往往不是 AI，而是是否真正理解业务流程。

---

# 2. 为什么目前更推荐赛道一

团队大体构成：

1. **经济 / 金融方向**
   - 负责金融逻辑、经济机制、估值、行业分析、金融评价指标、商业价值。

2. **上交工程/AI方向同学**
   - 对 AI、Agent、Agent 协作等比较熟悉。
   - 可负责 orchestration、multi-agent、tool use、workflow、verification 等。

3. **西交计算机方向同学 Chen Luodi**
   - 有较强计算机/AI研究能力。
   - 讨论中还检索到其可能参与 Agent / research lifecycle / benchmark 方向工作。
   - 这部分信息正式使用前应再核对个人公开主页 / 论文作者信息。

4. **电气方向同学**
   - 可负责电机、电驱、电力电子、电气设备、能源系统、工程参数理解。

5. **机械方向同学**
   - 可负责机器人、机械结构、制造工艺、设备、BOM、产线、机械系统。

此外团队还有语言 / 跨语言资料能力。

## 2.1 为什么不是纯量化优先

不是做不了 Quant，而是比较优势不在：

- 团队并非传统纯数理金融 / 统计套利 / 高频量化配置；
- 纯赛道二可能遇到已经长期做 Qlib、多因子、机器学习、高频、stat arb 的队伍；
- 我们真正稀缺的是跨领域组合。

因此更理想的是：

> **赛道一为主，必要时吸收赛道二的 Quant / backtest / financial modeling 能力。**

也就是：

> **01 × 02，但最终报 01。**

---

# 3. 赛道一不等于“自己训练模型”

这是我们明确讨论过的一个关键点。

赛道一更接近：

> 设计一个好的 Financial Agent System

而不是：

> 从头训练一个 7B / 70B / 100B 金融大模型

底层模型可以作为 endpoint：

```text
Agent Layer
    ↓
Model Router
 ├─ GPT
 ├─ Claude
 ├─ Gemini
 ├─ Qwen
 ├─ DeepSeek
 ├─ Ling-Fin
 └─ Local Model
```

不同 Agent 甚至可以调用不同模型。

例如：

- Planner：强 reasoning model
- 信息抽取：便宜模型
- 长文档：长上下文模型
- 金融推理：Finance-specialized model
- Critic：不同模型
- Calculation：Python
- Spreadsheet：deterministic spreadsheet engine
- Search：独立 retrieval / search tool

## 3.1 真正应该做好的部分

- task decomposition
- planning
- tool selection
- structured output
- memory
- state management
- multi-agent communication
- debate / critic
- verification
- evidence tracing
- temporal control
- confidence
- retry / error recovery
- benchmark
- latency / cost
- product interface

## 3.2 一个重要原则

不要让 LLM 负责所有计算。

应当尽量：

```text
LLM
负责：
理解、推理、拆任务、解释、提出假设

Python / deterministic tools
负责：
公式、财务计算、回测、Excel更新、规则校验
```

---

# 4. 比赛和纯学术研究的偏好有什么不同

我们讨论出的判断是：

> **这是一个“有学术验证习惯的产品型技术比赛”。**

不是纯论文，也不是纯创业 PPT。

## 4.1 学术论文通常重点

- method
- baseline
- benchmark
- ablation
- significance
- error analysis
- reproducibility

## 4.2 比赛还会继续问

- 谁会用？
- 为什么不用 ChatGPT / Claude？
- 为什么愿意付钱？
- 省了多少时间？
- 提高多少准确率？
- 降低多少风险？
- 是否可审计？
- 是否能嵌入实际金融 workflow？

因此需要同时回答：

> Does it work?  
> Does it work better?  
> Does anybody care?

## 4.3 推荐三层 evidence structure

### 第一层：技术 benchmark

- accuracy
- hallucination
- citation correctness
- task success
- tool success
- robustness
- latency
- token cost

### 第二层：金融 benchmark

按项目不同：

- 财报分析
- 估值
- risk
- factor
- backtest
- IRR / NPV
- project finance
- investment thesis

### 第三层：产品 benchmark

例如：

```text
人工：50 min
系统：8 min

成本：
人工：¥150 / task
系统：¥3 / task

准确率：
91% → 94%
```

## 4.4 需要 ablation

例如：

```text
完整系统                86%
- Critic                82%
- Evidence Check        75%
- Temporal Check        79%
- Multi-Agent           80%
```

用于证明：

> 到底是哪一个模块真正带来提升。

---

# 5. 讨论中定位到的新金融模型：Ling-3.0-flash-Fin

用户之前记得：

- 一百多 B 总参数
- 激活参数约 6B
- 金融 / 行业垂直模型
- 刚发布
- 某平台有免费期

讨论中高度怀疑对应：

> **InclusionAI / 蚂蚁的 Ling-3.0-flash-Fin**

讨论中检索到的信息大致为：

- 124B total parameters
- 约 5.1B activated parameters
- 金融 / 投资长程任务
- 强调可信来源、口径一致、准确计算、可审计输出
- 近期在 OpenRouter / Vercel 等平台可能有免费 endpoint / 免费期
- 权重可能计划随后开源

**注意：**
这些属于动态信息，正式采用前必须再核对：
- 官方模型卡
- Hugging Face
- OpenRouter
- Vercel AI Gateway
- InclusionAI 官方发布

## 5.1 对我们最合理的用法

不要把 Ling-Fin 本身当创新。

它只是：

> Finance Specialist Engine

例如：

```text
Model Router
 ├─ Ling-Fin → financial reasoning / valuation / long docs
 ├─ GPT/Claude → hard planning / critic
 ├─ small model → extraction
 ├─ Python → calculation
 └─ spreadsheet engine → workbook
```

## 5.2 可以做的实验矩阵

```text
                  Direct   Generic Agent   Our Agent
Ling Flash
Ling Flash Fin
Qwen
GPT
```

测试：

- finance QA
- evidence correctness
- numerical accuracy
- task completion
- temporal safety
- latency
- cost

目的：

> 证明提升来自我们的 Agent architecture，而不是某一个模型。

---

# 6. 一开始考虑过的方向：可审计金融 Research Agent

早期讨论中曾比较看好：

> TraceAnalyst / AuditResearch

核心思想：

> 每一个金融结论都能追溯到证据、原始来源和计算。

架构示例：

```text
User
 ↓
Research Planner
 ↓
Claim Decomposition
 ↓
Source Agent
 ↓
Evidence Graph
 ↓
Numerical Verification
 ↓
Accounting / Definition Check
 ↓
Temporal Check
 ↓
Bear / Critic Agent
 ↓
Final Research Memo
```

一个 claim 可保存：

```text
Claim C17
 ├─ Evidence E31：年报 page 42
 ├─ Evidence E42：行业数据
 └─ Calculation K8：Gross Margin formula
```

并输出：

- Evidence strength
- Contradictory evidence
- Temporal validity
- Calculation status
- Primary source coverage

## 6.1 Temporal Firewall

金融 Agent 的核心风险之一：

> look-ahead bias / time travel

规则：

```text
t_publication <= t_decision
```

例如让系统“站在 2023-06-30”：

只能读取当日以前已公开信息。

然后：

```text
2023-06-30
生成 thesis
 ↓
冻结
 ↓
观察未来 3/6/12 月
 ↓
验证 thesis
```

这个方向仍然可以保留，但后来我们认为：

> **可审计 / temporal-safe 更适合作为整个系统的基础设施，不一定是项目母题本身。**

---

# 7. 后来修正：不应只做普通投研 Agent

在进一步检索后，我们发现：

- TradingAgents
- FinRobot
- AI Hedge Fund
- 多种 Financial Research Agent
- RD-Agent(Q)
- 各类多 Agent 股票分析系统

已经把下面这种模式做得非常多：

```text
Fundamental Agent
Technical Agent
Sentiment Agent
News Agent
Risk Agent
Portfolio Manager
→ BUY / HOLD / SELL
```

因此：

> **“多个 Agent 分析股票 + 最后给交易建议”已经非常拥挤。**

即使 UI 漂亮，也不够新。

所以方向逐步修正为：

> **用团队跨学科优势，去解决纯 CS / 纯金融队伍不容易解决的问题。**

---

# 8. 当前第一推荐母题：让金融 Agent 理解实体工业世界

## 8.1 核心逻辑

传统金融 Agent 常见：

```text
财报
新闻
研报
行情
 ↓
金融结论
```

我们希望增加一层：

```text
技术参数
工程设计
专利
设备
BOM
供应链
产能
材料
海外技术文件
        ↓
Engineering Reasoning
        ↓
Economic Translation
        ↓
Financial Model
        ↓
Financial Decision
```

可以概括为：

> **Technology / Engineering → Economics → Finance**

## 8.2 为什么适合团队

| 背景 | 可负责 |
|---|---|
| 经济 / 金融 | industry economics、unit economics、财务模型、估值、项目融资 |
| CS / AI | Agent、RAG、workflow、tools、benchmark、backend |
| Agent 熟悉成员 | orchestration、multi-agent、verification、state |
| 电气 | 电机、电驱、电气设备、功率、效率、能源系统 |
| 机械 | 机器人、机械结构、制造工艺、BOM、产线 |
| 语言能力 | 多语言技术资料、海外法规、跨境文件、标准 |

如果评委问：

> 为什么你们需要这样的团队？

可以回答：

> 因为我们解决的问题本身，就要求同时理解工程、产业和金融。

---

# 9. 当前候选方向排序

## 方向 A：工业技术 → 金融价值 Agent

暂名：

> **Tech2Value / Engineering-to-Finance Intelligence Agent**

核心：

> AI 不仅看财报，还真正看懂技术、设备、供应链和工程变化，并把这些变化翻译成金融影响。

例如机器人企业推出新关节模组：

系统要回答：

- torque density 是否真的提高？
- weight 是否下降？
- BOM 是否变化？
- 国产替代率如何？
- 供应商变化？
- 良率变化？
- 产能变化？
- ASP 如何？
- 毛利率如何？
- EPS / FCF / valuation 如何？

核心链路：

```text
Engineering Change
 ↓
Unit Economics
 ↓
BOM / Capacity / ASP
 ↓
COGS / Revenue
 ↓
Gross Margin
 ↓
EBITDA / FCF
 ↓
Valuation
```

这是目前**第一推荐**。

---

# 10. 候选方向 B：工业项目融资 Agent

暂名：

> **ProjectFin Agent**

适用：

- 新能源
- 制造工厂
- 工业项目
- 基础设施
- 设备产线

输入：

- 可研报告
- 技术方案
- 设备清单
- CAPEX
- OPEX
- 电价
- 原材料
- 融资方案
- 利率
- 汇率
- 税收
- 政策
- 海外招标资料

自动形成：

- CAPEX
- OPEX
- Revenue
- EBITDA
- FCF
- NPV
- IRR
- DSCR

并做 stress test：

```text
原材料 +20%
汇率 -8%
利率 +100bp
利用率 -10%
建设延期 6个月
```

最后回答：

> 哪一个变量真正决定项目风险？

这一方向产品价值非常高，也极其适合工程 + 金融团队。

---

# 11. 候选方向 C：供应链冲击 → 金融影响 Agent

核心：

```text
事件
 ↓
材料 / 零件
 ↓
供应商
 ↓
产品
 ↓
公司
 ↓
库存
 ↓
替代性
 ↓
产量 / 成本
 ↓
毛利 / 现金流
 ↓
估值 / 信用风险
```

例如：

> 某国限制某类关键材料出口

普通 AI：

> 可能影响新能源行业

我们的系统：

> 哪些公司真正暴露？库存能撑多久？单位成本上涨多少？利润影响多少？

可以概括为：

> **Physical Supply Chain → Financial Exposure**

---

# 12. 候选方向 D：跨境工业金融 Agent

面向：

> 中国工业企业出海 / 海外订单 / 跨境项目

同时处理：

- 产品技术
- HS / trade classification
- 关税
- 产品标准
- 出口控制
- 汇率
- 信用证
- 贸易融资
- working capital
- insurance
- 当地法规
- 多语言文件

最终回答：

> 这笔订单到底赚不赚钱？金融、合规、工程风险是什么？

这一方向很适合语言 + 工程 + 金融，但需要控制范围。

---

# 13. 当前优先级

| 方向 | 团队契合 | 创新潜力 | 产品价值 | MVP难度 | 推荐 |
|---|---:|---:|---:|---:|---|
| 工业技术→金融价值 | 10 | 9.5 | 9 | 8 | 第一 |
| 工业项目融资 | 10 | 9.5 | 10 | 7 | 第二 |
| 供应链冲击→金融风险 | 9.5 | 10 | 9.5 | 6.5 | 第三 |
| 跨境工业金融 | 10 | 8.5 | 10 | 6 | 第四 |
| 通用投研 Agent | 7 | 6 | 9 | 9 | 后备 |
| 普通 Multi-Agent 炒股 | 6 | 4 | 7 | 9 | 不建议 |

---

# 14. 推荐的总体产品叙事

目前最有辨识度的一句话：

> **别人只让 AI 看懂财报，我们让 AI 看懂一台机器、一条产线、一条供应链，然后算清楚它值多少钱。**

英文方向可以表达为：

> **We build financial agents that understand the physical industrial world.**

或者：

> **From engineering evidence to financial value.**

---

# 15. 推荐的系统结构

```text
                      User
                       │
                Master / Planner
                       │
      ┌────────────────┼─────────────────┐
      │                │                 │
      ↓                ↓                 ↓
Engineering       Supply Chain       Finance
Intelligence      Intelligence       Engine
      │                │                 │
      └────────────────┼─────────────────┘
                       ↓
              Tech → Economics Mapper
                       ↓
                Financial Model
                       ↓
             Evidence / Verification
                       ↓
                Final Work Product
```

更完整：

```text
Engineering Agent
 ↓
Patent / Technology Agent
 ↓
Supply Chain Agent
 ↓
Market / Industry Agent
 ↓
Tech-to-Economics Mapper
 ↓
Financial Modeling Engine
 ↓
Risk / Critic Agent
 ↓
Evidence + Temporal Verifier
 ↓
Research Memo / Excel / Scenario Dashboard
```

---

# 16. 重要开源项目：建议参考清单

以下项目是讨论中提到的主要参考对象。

---

## 16.1 Sanjaya AI

GitHub：

https://github.com/Swayam8115/Sanjaya-AI

用途：

- 多领域 Master Agent
- 制药商业机会分析
- 市场
- 贸易
- 专利
- 临床
- 科研
- 企业内部资料
- Web
- 最终商业价值

最值得借鉴：

> **跨领域 worker agents 如何被 Master Agent 组织起来。**

它的逻辑：

```text
Molecule
 ↓
Clinical
 ↓
Patent
 ↓
Market
 ↓
Commercial Opportunity
```

我们可平移：

```text
Industrial Technology
 ↓
Engineering
 ↓
Patent
 ↓
Supply Chain
 ↓
Market
 ↓
Finance
```

优先级：★★★★★

---

## 16.2 ModelForge

GitHub：

https://github.com/Whatsonyourmind/modelforge

用途：

- Project Finance
- DCF
- LBO
- Credit
- Structured Finance
- Real Estate
- 三表
- M&A
- Excel financial modeling

核心价值：

> **LLM 生成模型不等于模型正确。**

重视：

- formula integrity
- accounting invariants
- risk check
- source trace
- deterministic build
- verification certificate

建议我们借鉴：

```text
Source
 ↓
Structured Spec
 ↓
Financial Model
 ↓
Formula Check
 ↓
Accounting / Finance Constraints
 ↓
Verification
```

优先级：★★★★★

---

## 16.3 SupplyChainCortex

GitHub：

https://github.com/JiuTian-dev/SupplyChainCortex

用途：

- inventory
- supplier
- logistics
- cost
- supply chain risk
- tool registry
- SOP
- audit trail

讨论中提到其有大量供应链工具，可参考：

> complex domain tool registry 如何设计

重点借：

- Supplier Tool
- Inventory Tool
- BOM Tool
- Logistics Tool
- Commodity Tool
- Capacity Tool
- risk chain
- replayable decision trace

优先级：★★★★★

许可证：
正式复用代码前需核对 LICENSE。

---

## 16.4 DisruptIQ

GitHub：

https://github.com/Sakshi3027/disruptiq

用途：

```text
News
 ↓
Event Classification
 ↓
Supply Chain Knowledge Graph
 ↓
Risk Propagation
 ↓
Affected Companies
```

技术：

- DistilBERT
- Neo4j
- Kafka
- Spark
- FastAPI
- Next.js

对我们的启发：

它做到：

> Event → Supply Chain Risk

我们补：

> Supply Chain Risk → Production / Cost → Finance

优先级：★★★★★

---

## 16.5 Academic Commercialization Agent

GitHub：

https://github.com/shuxiachai/academic-commercialization-agent

用途：

- 论文
- 技术成熟度
- TRL
- MRL
- 专利
- 市场
- 商业化

核心：

> Technology → Commercialization

我们可扩展：

> Technology → Engineering → Industry → Economics → Finance

优先级：★★★★★

---

## 16.6 PatentAgent

GitHub：

https://github.com/iStoryOfSpring/PatentAgent

用途：

- 专利检索
- 专利分析
- evidence trace
- FastAPI + React
- 多模型后端

可用于：

- 技术路线
- 竞争对手
- 权利要求
- 技术 moat
- claim verification

例如：

> 公司声称新关节扭矩密度 +20%

系统：

```text
Company Claim
 ↓
Patent
 ↓
Competitor Patent
 ↓
Datasheet
 ↓
Engineering Assessment
```

优先级：★★★★☆

许可证：
讨论中认为可能为 AGPL，正式复用前务必核对。

---

## 16.7 Due-diligence-engine

讨论中提到的仓库链接：

https://github.com/Atlas-Associates-Inc/Due-diligence-engine

用途：

- VC / Technical Due Diligence
- startup technical claim verification
- competitor
- evidence
- confidence
- risk

对我们特别有价值：

> **不要只总结公司说了什么，而要验证它说的技术 claim 是否成立。**

输出可以像：

```text
Claim:
Efficiency +20%

Evidence:
datasheet
patent
third-party test
competitor benchmark

Engineering assessment:
Partially supported

Confidence:
0.72

Financial relevance:
Medium
```

优先级：★★★★☆

---

## 16.8 Anthropic Financial Services

GitHub：

https://github.com/anthropics/financial-services

用途：

包含大量真实金融工作流 Agent：

- Market Researcher
- Earnings Reviewer
- Model Builder
- Valuation Reviewer
- Pitch Agent
- KYC
- Meeting Prep
- GL Reconciler

最值得学：

> **每个 Agent 输出专业 work product，而不是一段自然语言。**

例如 Earnings Reviewer：

```text
Earnings Call + Filing
 ↓
Actual
 ↓
Old Financial Model
 ↓
Update Model
 ↓
Variance vs Consensus
 ↓
Update Estimates
 ↓
Update Valuation
 ↓
Draft Note
```

最终交付：

- updated model
- earnings note
- actual vs estimate / consensus table

这对我们很重要：

我们的 Agent 也应该输出专业中间件：

```text
Engineering Agent
→ Tech Change Sheet

Supply Chain Agent
→ Exposure Matrix

Finance Agent
→ Updated Financial Model

Risk Agent
→ Risk Register
```

优先级：★★★★★

---

## 16.9 Meridian

GitHub：

https://github.com/YoussefMadkour/Meridian

用途：

- Letter of Credit
- trade finance
- UCP 600
- sanctions
- SWIFT MT700
- document examination
- multi-agent
- LangGraph

最值得学：

> **LLM + deterministic rule engine**

例如：

```text
LLM：
理解文件

Rules：
金额 / 日期 / 字段 / UCP600 条款严格校验

LLM：
解释风险
```

适合未来“工业出海 / 跨境金融”方向。

优先级：★★★★

---

## 16.10 Microsoft RD-Agent / RD-Agent(Q)

GitHub：

https://github.com/microsoft/RD-Agent

重点文档：

quant_agent_fin 相关文档

用途：

```text
Hypothesis
 ↓
Factor
 ↓
Implementation
 ↓
Experiment
 ↓
Backtest
 ↓
Feedback
 ↓
New Hypothesis
```

最值得学：

> **research–experiment–feedback loop**

不要只做：

```text
Agent A → B → C → Done
```

而要允许失败后回到前面重做。

可迁移为：

```text
Engineering Hypothesis
 ↓
Evidence Search
 ↓
Supply Chain Consequence
 ↓
Financial Model
 ↓
Consistency Check
 ↓
Fail?
 ↓
Revise Hypothesis
```

优先级：★★★★

---

## 16.11 TradingAgents

GitHub：

https://github.com/Carl-Wu/TradingAgents

用途：

- fundamental analyst
- sentiment
- technical
- researcher
- trader
- risk
- PM
- multi-agent debate

意义：

> 主要用作 baseline 和“已经被做得很成熟的方向”参考。

不要再把：

> Fundamental + Sentiment + Technical + Risk + PM

本身当作创新。

优先级：★★★

---

## 16.12 FinRobot

GitHub：

https://github.com/AI4Finance-Foundation/FinRobot

用途：

- 金融 Agent platform
- 年报
- forecasting
- trading
- research
- financial data / tools

意义：

- 看成熟金融 Agent 平台如何组织
- 作为 baseline
- 知道哪些金融 Agent 功能已经常见

优先级：★★★

---

# 17. 推荐的“参考项目拼装图”

```text
                     OUR PRODUCT
          Industrial Finance Intelligence
                        │
      ┌─────────────────┼─────────────────┐
      │                 │                 │
      ↓                 ↓                 ↓
 Engineering       Supply Chain         Finance
 Intelligence      Intelligence         Engine
      │                 │                 │
      │                 │                 │
 PatentAgent       SupplyChainCortex   ModelForge
 Academic          DisruptIQ           Anthropic
 Commercial.                         Financial Services
      │                 │                 │
      └─────────────────┼─────────────────┘
                        ↓
                   Agent Harness
                        │
                    RD-Agent
                    LangGraph
                    Verification
                        │
                        ↓
                  Evidence Layer
                 Claim / Source /
               Confidence / Time
```

Sanjaya AI 作为：

> 总体多领域产品结构参考。

---

# 18. 一个非常具体的比赛 Demo 示例

假设选：

> 某机器人企业推出新一代关节模组

用户问：

> “这个技术升级真的值得把 2027 年盈利预测上调吗？”

## Agent 1：Engineering Agent

读取：

- datasheet
- 专利
- 产品发布
- 技术标准

得到：

```text
Torque Density +18%
Weight -12%
Efficiency +X%
```

## Agent 2：Patent / Competitor Agent

发现：

> 竞品已有类似路线，technology moat 中等。

## Agent 3：Supply Chain Agent

分析：

- BOM
- reducer
- motor
- bearing
- material
- supplier
- localization

得到：

> 国产替代使 BOM 降低约 X%

## Agent 4：Market / Industry Agent

分析：

- 下游需求
- 出货量
- ASP
- competitor
- capacity

## Agent 5：Finance Engine

把工程参数转成：

```text
Units × ASP → Revenue

BOM → COGS → Gross Margin

Revenue / Margin → EBITDA / FCF

FCF → Valuation
```

例如：

```text
EPS 2027E
1.82 → 2.03
```

## Agent 6：Evidence / Critic

用户点击：

> EPS +11.5%

可以看到：

```text
Engineering Assumption
 ↓
Source
 ↓
Cost Assumption
 ↓
Calculation
 ↓
Financial Model Cell
```

核心：

> 每一步都能追。

---

# 19. 推荐的 benchmark

## 19.1 Engineering layer

测试：

- 技术参数抽取正确率
- datasheet 理解
- patent claim 理解
- engineering reasoning accuracy

## 19.2 Multilingual layer

同一个技术材料：

- 中文
- English
- Français

检查：

- parameter consistency
- conclusion consistency
- terminology correctness

## 19.3 Economics / Finance conversion

给定真实工程参数：

测试：

- unit cost
- BOM
- capacity
- revenue
- gross margin
- NPV
- IRR
- valuation

## 19.4 End-to-end

对比：

- GPT direct
- Ling-Fin direct
- generic RAG
- generic Research Agent
- TradingAgents / other baseline
- Our system

指标：

- factual accuracy
- engineering accuracy
- evidence correctness
- financial calculation accuracy
- temporal validity
- task success
- latency
- cost

---

# 20. Product vs Academic：我们最终应达到的形态

不要走两个极端。

## 极端 A：太学术

- 37 张 benchmark 表
- 8 个 dataset
- 但不知道谁会用

不够。

## 极端 B：太创业 PPT

- “AI 重塑金融未来”
- 网页漂亮
- 但准确率 / benchmark 不知道

也不够。

理想状态：

> **一个评委现场能用的产品 + 一套扎实 benchmark + 清晰场景 + 清晰商业价值。**

---

# 21. 当前产品化重点

最终系统不应该只输出 chat。

最好输出真正的金融 / 工业 work products：

- Research Memo
- Tech Change Sheet
- Supply Chain Exposure Matrix
- Risk Register
- Updated Excel Model
- Scenario Analysis
- Evidence Ledger
- Assumption Table
- Valuation Delta
- “What Changed?” Report

---

# 22. 当前最值得讨论的几个问题

这些是下一轮团队讨论需要真正决定的。

## Q1. 我们究竟选哪一个垂直行业做 MVP？

推荐优先：

- 人形机器人
- 工业机器人
- 伺服 / 电机
- 减速器
- 电气设备
- 电池设备
- 光伏 / 储能设备

不要一开始声称“所有工业”。

## Q2. 项目更偏哪一个主场景？

四选一：

A. 上市公司工业技术→估值  
B. 工业项目融资  
C. 供应链冲击→金融风险  
D. 工业企业出海 / 跨境金融

## Q3. 最终核心用户是谁？

可能是：

- Equity Research Analyst
- Buy-side Analyst
- PE / VC
- Project Finance
- Credit Analyst
- Bank / Industrial Finance
- Corporate Strategy
- Industrial Company CFO / Investment Dept.

必须选清楚。

## Q4. 核心创新究竟是什么？

不能只说“多 Agent”。

可选：

- Tech-to-Economics Mapper
- Engineering-aware Financial Agent
- Evidence-grounded industrial finance
- Temporal-safe industrial research
- Supply-chain risk propagation → financial model
- Claim verification → valuation
- deterministic financial verification

## Q5. 数据源是什么？

需要明确：

- company filings
- product datasheets
- patents
- standards
- BOM / supplier data
- market data
- commodity prices
- policy / regulation
- financial statements
- industry reports

## Q6. 哪些模块可以开源复用，哪些必须自己写？

建议：

复用：
- orchestration framework
- generic retrieval
- basic spreadsheet IO
- graph DB
- public finance data tools

自己写：
- Tech-to-Economics Mapper
- engineering ontology
- financial impact mapping
- evidence model
- evaluation benchmark
- industry-specific tools

---

# 23. 当前推荐分工

初版可考虑：

## 经济 / 金融

- use case
- finance model
- industry economics
- valuation
- IRR / NPV
- benchmark design
- product narrative

## AI / Agent

- orchestration
- planner
- state
- multi-agent
- tool use
- routing
- memory
- critic

## CS / Research

- backend
- retrieval
- benchmark
- model comparison
- evaluation harness
- graph / database

## 电气

- electrical engineering ontology
- motor / power electronics / energy
- technical parameter validation
- engineering benchmark

## 机械

- robot / machine / manufacturing
- BOM
- mechanical structure
- process
- production line
- engineering benchmark

## 语言能力

- multilingual technical material
- translation consistency
- terminology
- foreign standards / documents

---

# 24. 最推荐的下一步

不是继续“想更多点子”，而是：

## Step 1

从以下三条里选 1 条：

1. 机器人 / 高端装备技术→估值
2. 供应链冲击→金融影响
3. 工业项目融资

## Step 2

找到一个真实案例。

例如：

> 某机器人上市公司最近一个真实产品升级

## Step 3

手工走一遍：

```text
技术变化
→ 工程含义
→ 供应链
→ 经济参数
→ 财务模型
→ 最终决策
```

## Step 4

找出其中最适合 Agent 自动化的步骤。

## Step 5

定义 MVP：

必须只做 1 个场景，做深。

## Step 6

同时定义 benchmark。

---

# 25. 当前共识总结

可以给后续 AI / 团队一句话：

> 我们参加的是北京大学金融 AI 智能体创新大赛，当前倾向赛道一。我们不准备从头训练大模型，而是用现成强模型作为底层推理引擎，创新集中在 Agent workflow、工具调用、verification、金融应用与产品化。团队成员横跨经济金融、AI/Agent、计算机、电气、机械，并具备语言/跨语言能力。因此我们不想做已经很拥挤的“多 Agent 股票分析/AI hedge fund”，而更想做一个能理解实体工业技术、供应链和工程信息，并把它们系统映射到成本、产能、现金流、估值和金融风险的 Industrial-Tech-to-Finance Agent。我们计划借鉴 Sanjaya AI、ModelForge、SupplyChainCortex、DisruptIQ、Academic Commercialization Agent、PatentAgent、Anthropic Financial Services、RD-Agent 等开源项目的不同模块，但核心的 Tech-to-Economics-to-Finance mapping、工程金融 ontology、evidence / temporal verification 和 benchmark 需要自己设计。

---

# 26. 给 Kimi / Claude Code 的后续讨论提示词

可直接复制：

```text
我们正在参加北京大学金融 AI 智能体创新大赛，倾向赛道一“金融 AI 智能体算法与应用创新”。

团队背景包括：
- 经济/金融
- AI/Agent
- 计算机
- 电气
- 机械
- 语言/跨语言资料能力

我们不准备训练自己的 foundation model，而计划把现成 LLM 当作可替换的 reasoning engine，重点做 Agent architecture、tools、workflow、verification、benchmark 和产品。

目前最有希望的项目母题是：
“让金融 Agent 理解实体工业世界。”

核心链路：
Engineering / Technology
→ Patent / BOM / Supply Chain / Capacity
→ Economics
→ Financial Model
→ Valuation / Risk / Decision

目前候选：
1. 工业技术→金融价值 Agent
2. 工业项目融资 Agent
3. 供应链冲击→金融影响 Agent
4. 跨境工业金融 Agent

已知重要开源参考：
- Sanjaya AI
- ModelForge
- SupplyChainCortex
- DisruptIQ
- Academic Commercialization Agent
- PatentAgent
- Due-diligence-engine
- Anthropic Financial Services
- Meridian
- Microsoft RD-Agent
- TradingAgents
- FinRobot

请基于这些背景：
1. 批判性评估这个方向是否真的有创新和比赛竞争力；
2. 再搜索当前 GitHub / Hugging Face / arXiv / 产业产品中是否已有高度类似项目；
3. 找出真正没有被做好的 gap；
4. 提出 3-5 个更具体、两周左右能做出 MVP 的项目；
5. 对每个项目给出：
   - 用户
   - 痛点
   - Agent workflow
   - 数据源
   - 技术栈
   - 可复用开源模块
   - 必须自己实现的创新
   - benchmark
   - Demo
   - 商业价值
   - 撞题风险
   - 获奖潜力
6. 不要默认“多 Agent 越多越好”，重点关注真实金融 work product 和可验证性。
```

---

# 27. 重要提醒

本文件整理的是**当前讨论状态**，不是最终方案。

尤其以下信息后续必须再次核验：

- 赛事最新报名 / 截止时间
- 官方赛道描述
- Ling-3.0-flash-Fin 的具体参数、开源情况和免费额度
- 各 GitHub 项目的维护状态
- 各仓库许可证
- GitHub 项目是否存在更新 / fork / 更优实现
- 当前 2026 年已有的商业竞品
- 是否已经有人做过高度类似的 Industrial-Tech-to-Finance Agent

最终项目方向在确定前，应再做一轮系统的：
- GitHub
- Hugging Face
- arXiv
- Semantic Scholar / Google Scholar
- 产品官网
- 创业公司
- 金融机构公开案例
- 大模型厂商 Agent demos

的去重和竞品调研。

