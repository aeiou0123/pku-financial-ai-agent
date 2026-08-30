# GitHub 参考项目深度笔记

> 整理时间：2026-08-29，更新于 2026-08-30
> 说明：2026-08-30 已成功 clone 以下 12 个仓库到本地 `research_materials/github_repos/` 目录。正式复用代码前请核对各仓库 LICENSE。

---

## 1. Sanjaya AI
- **Repo:** [Swayam8115/Sanjaya-AI](https://github.com/Swayam8115/Sanjaya-AI)
- **定位:** 制药领域的 Agentic AI 系统，用于跨国仿制药企业向创新医疗多元化评估。
- **架构:**
  - Frontend: React + Tailwind CSS + Vite
  - Backend: FastAPI + LangGraph
  - LLM: OpenAI SDK
  - Storage: Supabase
- **核心能力:**
  - Master Agent 协调多个 Worker Agent
  - 分子评估、市场趋势、CAGR、竞争对手、临床管线成熟度、专利壁垒、自由实施分析
  - 实时获取监管、临床试验、专利、出版物数据
  - 自动生成 PDF/Excel 报告
- **可借鉴:** 跨领域 Worker Agent 被 Master Agent 组织的方式；报告生成与可追溯性。
- **可复用模块:** Agent orchestration 架构思想、报告生成流水线设计。
- **迁移到 Claim2Value:** 把 "Molecule → Clinical → Patent → Market → Commercial Opportunity" 替换为 "Industrial Technology → Engineering → Patent → Supply Chain → Market → Finance"。

---

## 2. ModelForge
- **Repo:** [Whatsonyourmind/modelforge](https://github.com/Whatsonyourmind/modelforge)
- **PyPI:** `modelforge-finance`
- **定位:** "Bulge-tier Excel financial model factory"，程序化生成可审计 Excel 财务模型。
- **覆盖:** Project Finance、DCF、LBO、M&A、Restructuring、NPL、Structured Credit、Real Estate、IPO 等。
- **核心特性:**
  - 每个单元格 live-formulated
  - 每个数字 traceable
  - Deterministic byte-identical builds
  - `modelforge certify --strict`
  - Source tracing（每个硬编码 cell 链接到 source doc/page）
  - MCP-native，可在 Claude Code / Cursor / ChatGPT Enterprise 中使用
  - Data-room ingestion: PDFs/XLSXs/CSVs → validated YAML spec with traced sources
  - Trust Layer 合理性检查
- **CLI 示例:**
  ```bash
  pip install "modelforge-finance[mcp,export]"
  modelforge scaffold dcf -o demo_dcf.yaml
  modelforge build demo_dcf.yaml
  modelforge certify output/demo_dcf.xlsx
  ```
- **可借鉴:** 财务模型可审计性、公式完整性、source tracing、Trust Layer。
- **可复用模块:** Excel 构建与校验逻辑、source-to-cell tracing 思想。
- **局限:** 是财务模型工具，不是工业技术→金融映射；核心创新需自研。

---

## 3. SupplyChainCortex
- **Repo:** [JiuTian-dev/SupplyChainCortex](https://github.com/JiuTian-dev/SupplyChainCortex)
- **定位:** 供应链智能仪表盘，结合 OR 模型、LLM Agent、Graph RAG。
- **架构:**
  - Next.js 16 App Router + TypeScript 5
  - Tailwind CSS 4 + shadcn/ui + Recharts/ECharts
  - PostgreSQL + Prisma ORM
  - Zustand + TanStack Query
  - SSE 实时推送
  - DeepSeek / OpenAI / Anthropic Provider Adapter
  - ReAct Agent FSM v2
  - Python 3 + NumPy（10 modules, 24 OR functions）
  - SearXNG self-hosted + 8 fallback sources
- **工具规模:** 73 MCP tools（CRUD 11 + Operation 11 + Intelligence 27 + Math 24）
- **Graph RAG:**
  - graph-store.ts: 有向图，节点类型包括 supplier/warehouse/port/certification/regulation
  - graph-algorithms.ts: BFS cascade、Betweenness Centrality、Dijkstra shortest path、Impact Radius
  - cascade-risk.propagation.ts: 多源风险融合、Monte Carlo 传播、SEIR dynamics
  - graph-rag.ts: regex 实体抽取 → graph node matching → 2-hop traversal → 风险/中心性分析 → prompt context injection
- **可借鉴:** 复杂领域 tool registry 设计、供应商/BOM/库存/物流工具抽象、Graph RAG 风险传播。
- **可复用模块:** 供应链工具层设计、图传播算法思想、缓存与分层架构。
- **局限:** 偏供应链运营，缺少到财务影响的系统映射；LICENSE 需确认。

---

## 4. DisruptIQ
- **Repo:** [Sakshi3027/disruptiq](https://github.com/Sakshi3027/disruptiq)
- **Demo:** https://disruptiq.vercel.app
- **定位:** 实时供应链风险情报系统。
- **技术栈:**
  - DistilBERT fine-tuned 分类器（port/weather/geopolitical/semiconductor/factory/general）
  - Apache Kafka
  - Apache Spark Streaming
  - Neo4j knowledge graph
  - Next.js + FastAPI dashboard
- **知识图谱:** 10 companies, 10 ports, 7 product categories, 56 supply-chain relationships
- **风险传播公式:**
  ```
  risk_score = min(1.0, base_company_risk × event_severity × type_multiplier × 2)
  ```
- **可借鉴:** 事件→供应链风险传播的知识图谱构建。
- **可复用模块:** 风险传播公式、知识图谱查询模式。
- **局限:** 只到"哪些公司受影响"，不到"利润/估值影响多少"；数据集很小。

---

## 5. Academic Commercialization Agent
- **Repo:** [shuxiachai/academic-commercialization-agent](https://github.com/shuxiachai/academic-commercialization-agent)
- **Demo:** https://academic-commercialization-agent.up.railway.app
- **License:** MIT
- **定位:** 基于 CrewAI 的 6 Agent 系统，把论文转成商业化报告。
- **6 个 Agent:**
  1. Academic Literature Analyst
  2. Patent Landscape Analyst
  3. Market & Competitive Intelligence Analyst
  4. Technology Commercialization Report Writer
  5. Report Reviewer
  6. Commercialization Readiness Scorer
- **输出:** TRL、MRL、Patent Strength、Market Accessibility、Evidence Confidence、总分。
- **可借鉴:** 技术成熟度评估框架、引用溯源、多语言报告。
- **可复用模块:** TRL/MRL 评分思想、CrewAI Agent 分工模式。
- **局限:** 学术→商业化，需扩展为学术/工程→金融。

---

## 6. PatentAgent
- **Repo:** [iStoryOfSpring/PatentAgent](https://github.com/iStoryOfSpring/PatentAgent)
- **定位:** 可追溯专利分析系统，FastAPI + React + LLM Agent，支持 Claude/OpenAI/DeepSeek。
- **工具清单（16+）:**
  - get_dataset_summary
  - analyze_patent_trend
  - analyze_lifecycle
  - analyze_ipc_distribution
  - generate_wordcloud
  - analyze_burst_terms
  - analyze_yearly_keywords
  - analyze_country_distribution
  - analyze_co_network
  - analyze_tech_roadmap
  - analyze_tech_matrix
  - analyze_clustering
  - analyze_patent_valuation
  - analyze_competitor_evolution
  - search_patents
  - read_patent_details
- **数据源:** WoS Derwent、Google Patents Public Data JSONL、USPTO grant full-text XML、USPTO file-wrapper JSON；EPO OPS 和 CNIPA 仅格式准备。
- **可借鉴:** 专利作为技术证据、算法证据矩阵（`docs/tool-evidence-matrix.md`）、多供应商模型后端。
- **可复用模块:** 专利检索与分析工具设计、证据矩阵思想。
- **注意:** LICENSE 需确认；文件提示可能是 AGPL，正式复用前务必核对。

---

## 7. Due-diligence-engine (Atlas Associates)
- **Repo:** [Atlas-Associates-Inc/Due-diligence-engine](https://github.com/Atlas-Associates-Inc/Due-diligence-engine)
- **License:** Apache 2.0
- **Version:** v0.6.1
- **定位:** AI 驱动的 VC 技术尽调引擎，验证 startup 技术 claim、检测 AI-washing。
- **核心能力:**
  - 读取目标代码库
  - 验证宣称技术是否真正实现
  - 检测 AI-washing
  - 实时网络研究竞争对手、融资轮、CVE、市场动态
  - 多维度加权评分
  - 输出 ~24 页 PDF 报告 + 0-100 评分 + letter grade
- **使用:**
  ```bash
  python3 -m pip install --no-cache-dir git+https://github.com/Atlas-Associates-Inc/Due-diligence-engine.git
  dde prompt --pdf
  ```
- **可借鉴:** 技术 claim verification、competitor/CVE/融资动态网络研究、置信度评分。
- **可复用模块:** claim verification 流程、评分卡设计。
- **局限:** 面向软件代码尽调，不是工业设备；但验证思想高度相关。

---

## 8. Anthropic Financial Services
- **Repo:** [anthropics/financial-services](https://github.com/anthropics/financial-services)
- **License:** Apache 2.0
- **发布时间:** 2026 年 5 月
- **定位:** Anthropic 官方开源金融 Agent 套件，面向投资银行等真实金融工作流。
- **Agent 分类:**
  - Coverage & Advisory: Pitch Agent, Meeting Prep Agent
  - Research & Modeling: Market Researcher, Earnings Reviewer, Model Builder, Valuation Reviewer
  - Fund Admin & Finance Ops: GL Reconciler, Month-End Closer, Statement Auditor
  - Operations & Onboarding: KYC Screener
- **架构:**
  - Agents: `plugins/agent-plugins/<slug>/`
  - Skills: 每个 Agent 附带 domain-specific instructions
  - Commands: `/earnings`, `/comps`, `/dcf`, `/ic-memo`
  - Connectors: MCP servers for FactSet, S&P Global, Bloomberg, LSEG, Morningstar
- **可借鉴:** 每个 Agent 输出专业 work product（updated model、earnings note、variance table），不是自然语言。
- **可复用模块:** 金融工作流拆解、Agent 输出格式设计。
- **局限:** 通用金融 Agent baseline，没有工业工程理解层。

---

## 9. Meridian
- **Repo:** [YoussefMadkour/Meridian](https://github.com/YoussefMadkour/Meridian)
- **License:** MIT
- **定位:** 信用证（Letter of Credit）自动化，9 个 Agent 90 秒完成 LC 签发和审单。
- **技术栈:** Google Gemini 3 Flash + LangGraph + FastAPI + Next.js 16
- **Phase 1 — LC 签发（6 agents）:** 并行情报收集、风险综合、合规检查、LC 生成
- **Phase 2 — 审单（3 agents）:** 验证商业发票、运输单据、保险证书
- **UCP 600 覆盖:** 39 条中的 27 条 + 6 条 eUCP v2.1
- **可借鉴:** LLM + deterministic rule engine 结合模式、文档校验流程。
- **可复用模块:** 规则引擎与 LLM 结合、多 Agent 并行审单。
- **适用场景:** 如果你们做跨境工业金融方向，参考价值最大。

---

## 10. Microsoft RD-Agent
- **Repo:** [microsoft/rd-agent](https://github.com/microsoft/rd-agent)
- **PyPI:** `rdagent`
- **论文:** arXiv:2505.15155
- **定位:** LLM 驱动的 R&D 自动化框架。
- **核心循环:**
  ```
  Research（假设生成）
    ↓
  Development（Co-STEER 代码生成）
    ↓
  Validation（回测/实验）
    ↓
  Analysis（多臂老虎机选择下一步）
    ↓
  回到 Research
  ```
- **量化版本:** `rdagent fin_quant`, `rdagent fin_factor`, `rdagent fin_model`
- **可借鉴:** research–experiment–feedback loop、失败后回溯重做。
- **可复用模块:** 反馈循环架构、假设→实验→评估模式。
- **局限:** 偏量化/代码生成，需迁移到工程假设→证据→财务模型。

---

## 11. TradingAgents
- **Repo:** [TauricResearch/TradingAgents](https://github.com/tauricresearch/tradingagents)
- **论文:** arXiv:2412.20138
- **定位:** 多 Agent LLM 金融交易框架。
- **Agent 角色:** Fundamental Analyst, Sentiment Analyst, News Analyst, Technical Analyst, Bull/Bear Researcher, Risk Manager, Trader
- **用途:** 作为 baseline 和“不应做的方向”参考。
- **关键结论:** 这种 "Fundamental + Sentiment + Technical + Risk + PM" 模式已非常拥挤。

---

## 12. FinRobot
- **Repo:** [AI4Finance-Foundation/FinRobot](https://github.com/AI4Finance-Foundation/FinRobot)
- **论文:** arXiv:2405.14767
- **定位:** 开源金融 Agent 平台。
- **四层架构:**
  1. Financial AI Agents Layer
  2. Financial LLM Algorithms Layer
  3. LLMOps and DataOps Layer
  4. Multi-source LLM Foundation Models Layer
- **用途:** 作为通用金融 Agent baseline，了解哪些金融 Agent 功能已常见。

---

## 参考项目拼装图（针对 Claim2Value）

```
                     OUR PRODUCT
           Claim2Value / Industrial Finance Intelligence
                         │
       ┌─────────────────┼─────────────────┐
       │                 │                 │
       ↓                 ↓                 ↓
  Claim Verif.      Engineering       Financial
  & Evidence        Ground Truth      Modeling
       │                 │                 │
  Sanjaya AI        PatentAgent       ModelForge
  Due-diligence     Academic          Anthropic
  -engine           Commercial.       Financial
  DebateCV          SupplyChain       Services
  VeGraph           Cortex            Meridian
       │                 │                 │
       └─────────────────┼─────────────────┘
                         ↓
                    Agent Harness
                         │
                    RD-Agent loop
                    LangGraph
                    State Verification
                         │
                         ↓
                  Evidence Layer
                 Claim / Source /
               Confidence / Time
```

---

## 每个项目最值得拿的模块

| 项目 | 最值得复用的部分 | 不建议复用的部分 |
|---|---|---|
| Sanjaya AI | Master Agent + Worker Agent 架构、报告生成 | 制药领域数据/工具 |
| ModelForge | Excel 可审计构建、source tracing、certify | 具体金融模型模板 |
| SupplyChainCortex | Tool registry、Graph RAG、风险传播 | 过于复杂的 OR 模块 |
| DisruptIQ | 事件分类、风险传播公式 | 小数据集、缺少财务层 |
| Academic Commercialization | TRL/MRL 评分、引用溯源 | 学术商业化评分卡 |
| PatentAgent | 专利分析工具设计、证据矩阵 | 具体专利数据源 |
| Due-diligence-engine | Claim verification 流程、评分卡 | 软件代码分析 |
| Anthropic FS | Agent 输出专业 work product 的设计 | 通用金融工作流 |
| Meridian | LLM + 规则引擎结合、文档校验 | LC 特定规则 |
| RD-Agent | 反馈循环、假设→实验→评估 | 量化代码生成 |
| TradingAgents/FinRobot | 仅作为 baseline 参考 | 核心逻辑 |
