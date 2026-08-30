# Claim2Value 研究文献库

> 整理时间：2026-08-29
> 说明：由于当前网络环境无法直接访问 arxiv.org（curl/WebFetch 均被重置/拦截），以下文献以元数据+摘要+链接形式保存。正式深度阅读时请在可访问 arxiv 的环境下下载 PDF。

---

## 一、Claim Verification / Fact-Checking（直接相关）

### 1. DebateCV: Debate-driven Claim Verification
- **arXiv:** [2507.19090](https://arxiv.org/abs/2507.19090)
- **PDF:** [https://arxiv.org/pdf/2507.19090](https://arxiv.org/pdf/2507.19090)
- **Title:** *Debating Truth: Debate-driven Claim Verification with Multiple Large Language Model Agents*
- **Authors:** Haorui He, Yupeng Li, Dacheng Wen, Reynold Cheng, Francis C. M. Lau, et al.
- **Venue:** WWW 2026
- **核心思想:** 两个 Debaters 辩论 claim 正反两面，Moderator 裁决。提出 Debate-SFT 训练 moderator 克服 zero-shot 偏向中立的偏见。
- **对我们的启发:** 可用于 Causal Financial Critic 模块，让正反方 Agent 辩论技术升级的经济后果。

### 2. Verifiable Misinformation Detection via Multi-Tool LLM Agent
- **arXiv:** [2508.03092](https://arxiv.org/abs/2508.03092)
- **PDF:** [https://arxiv.org/pdf/2508.03092](https://arxiv.org/pdf/2508.03092)
- **Title:** *Toward Verifiable Misinformation Detection: A Multi-Tool LLM Agent Framework*
- **Authors:** Zikun Cui, Tianyi Huang, Chia-En Chiang, Cuiqianhe Du
- **核心工具:** precise web search + source credibility assessment + numerical claim verification
- **对我们的启发:** 三个工具可直接迁移到 Claim2Value 的 Claim Verification 层。

### 3. LoCal: Logical and Causal Fact-Checking
- **原文:** Ma, J., Hu, L., Li, R., & Fu, W. (2025). Local: Logical and causal fact-checking with llm-based multi-agents. *ACM Web Conference 2025*, 1614–1625.
- **Survey引用:** arXiv:2508.03860
- **核心思想:** 用多 Agent 做逻辑和因果事实核查。
- **对我们的启发:** Causal Financial Critic 的理论基础。

### 4. VeGraph: Verify-in-the-Graph
- **arXiv:** [2505.22993](https://arxiv.org/abs/2505.22993)
- **PDF:** [https://arxiv.org/pdf/2505.22993](https://arxiv.org/pdf/2505.22993)
- **Title:** *Verify-in-the-Graph: Entity Disambiguation Enhancement for Complex Claim Verification with Interactive Graph Representation*
- **Authors:** Hoang Pham, Thanh-Do Nguyen, Khac-Hoai Nam Bui
- **Venue:** NAACL 2025
- **核心思想:** 把 claim 分解为 triplets 构建图，通过与知识库交互消歧实体，再验证。
- **对我们的启发:** 工程 claim 中的技术参数、材料、供应商实体消歧。

### 5. CheckThat! 2026 Numerical Claim Verification
- **arXiv:** [2607.25069](https://arxiv.org/abs/2607.25069)
- **Title:** *DS@GT ARC at CheckThat! 2026: LLM-Based Trace Ranking and Grouped Reward Modeling for Multilingual Numerical Claim Verification*
- **Authors:** Sagnik Sinha, Shreyas Shrestha
- **核心思想:** 对数值 claim 的推理轨迹排序，用 reward model 聚合预测最终 verdict。
- **对我们的启发:** 金融 claim 多为数值，可借鉴 trace ranking 和 sub-claim decomposition 思想。

### 6. Corroborating and Refuting Evidence Retrieval
- **arXiv:** [2503.07937](https://arxiv.org/abs/2503.07937)
- **PDF:** [https://arxiv.org/pdf/2503.07937](https://arxiv.org/pdf/2503.07937)
- **Title:** *LLM-based Corroborating and Refuting Evidence Retrieval for Scientific Claim Verification*
- **核心思想:** 同时检索支持性和反驳性证据，用 weighted information gain 判断 Support/Refute/Neutral。
- **对我们的启发:** 工程 claim 需要同时找支持和反驳证据。

### 7. DECEIVE-AFC: Adversarial Claim Attacks
- **arXiv:** [2602.02569](https://arxiv.org/abs/2602.02569)
- **PDF:** [https://arxiv.org/pdf/2602.02569](https://arxiv.org/pdf/2602.02569)
- **Title:** *DECEIVE-AFC: Adversarial Claim Attacks against Search-Enabled LLM-based Fact-Checking Systems*
- **Authors:** Haoran Ou, Kangjie Chen, Gelei Deng, Hangcheng Liu, Jie Zhang, Tianwei Zhang, Kwok-Yan Lam
- **核心思想:** 黑盒攻击搜索增强的事实核查系统，准确率在攻击下从 78.7% 降到 53.7%。
- **对我们的启发:** 提醒我们要做 robustness benchmark，测试系统面对误导性 claim 的表现。

---

## 二、Supply Chain Risk Propagation（SupplyChain2Risk 方向）

### 8. Risk Propagation in Endogenous Supply Chains
- **arXiv:** [2403.16632](https://arxiv.org/abs/2403.16632)
- **PDF:** [https://arxiv.org/pdf/2403.16632](https://arxiv.org/pdf/2403.16632)
- **Title:** *Risk Propagation in Endogenous Supply Chains*
- **Author:** A. Titton
- **核心思想:** 内生形成的供应链中，上游风险相关导致企业多元化激励不足，网络脆弱。研究风险如何通过供应商关系传播。
- **对我们的启发:** 供应链风险传播的学术基础，可用于设计从事件到财务影响的传播模型。

---

## 三、Agent Systems / Financial Agents（背景参考）

### 9. LLM-Powered AI Agent Systems in Industry
- **arXiv:** [2505.16120](https://arxiv.org/abs/2505.16120)
- **PDF:** [https://arxiv.org/pdf/2505.16120](https://arxiv.org/pdf/2505.16120)
- **Title:** *LLM-Powered AI Agent Systems and Their Applications in Industry*
- **Authors:** Guannan Liang, Qianqian Tong
- **Venue:** IEEE AIIoT 2025
- **核心思想:** 把 Agent 分为 software-based、physical、adaptive/hybrid 三类，讨论制造自动化、金融交易等应用。
- **对我们的启发:** 我们的项目是 software + physical world understanding 的 hybrid agent。

### 10. TradingAgents
- **arXiv:** [2412.20138](https://arxiv.org/abs/2412.20138)
- **PDF:** [https://arxiv.org/pdf/2412.20138](https://arxiv.org/pdf/2412.20138)
- **Title:** *TradingAgents: Multi-Agents LLM Financial Trading Framework*
- **Authors:** Yijia Xiao, Edward Sun, Di Luo, Wei Wang (UCLA/MIT)
- **核心思想:** Fundamental + Sentiment + Technical + Bull/Bear + Risk + Trader 多 Agent 交易框架。
- **对我们的启发:** 作为 baseline 和“不应做的方向”参考。

### 11. FinRobot
- **arXiv:** [2405.14767](https://arxiv.org/abs/2405.14767)
- **PDF:** [https://arxiv.org/pdf/2405.14767](https://arxiv.org/pdf/2405.14767)
- **Title:** *FinRobot: An Open-Source AI Agent Platform for Financial Applications using Large Language Models*
- **Authors:** Hongyang Yang, Boyu Zhang, Neng Wang, et al.
- **核心思想:** 四层架构的金融 Agent 平台， Financial AI Agents / Financial LLM Algorithms / LLMOps & DataOps / Multi-source LLM Foundation Models。
- **对我们的启发:** 金融 Agent 平台的常见架构参考。

### 12. R&D-Agent-Quant
- **arXiv:** [2505.15155](https://arxiv.org/abs/2505.15155)
- **PDF:** [https://arxiv.org/pdf/2505.15155](https://arxiv.org/pdf/2505.15155)
- **Title:** *R&D-Agent-Quant: A Multi-Agent Framework for Data-Centric Factors and Model Joint Optimization*
- **Authors:** Yuante Li, Xu Yang, Xiao Yang, Minrui Xu, Xisen Wang, Weiqing Liu, Jiang Bian (Microsoft)
- **核心思想:** Research → Development → Feedback loop，自动化因子挖掘和模型共优化。
- **对我们的启发:** 反馈循环架构，可用于工程假设→证据→财务模型的迭代验证。

---

## 四、建议优先阅读的 Top 5

1. **DebateCV (2507.19090)** → Causal Financial Critic
2. **Multi-Tool Verifiable Misinformation (2508.03092)** → Claim Verification Agent
3. **VeGraph (2505.22993)** → 实体消歧与知识库交互
4. **Risk Propagation in Endogenous Supply Chains (2403.16632)** → SupplyChain2Risk 理论基础
5. **R&D-Agent-Quant (2505.15155)** → 反馈循环与 benchmark 设计

---

## 五、下载状态 ✅ 已下载

| 论文 | arxiv PDF | 本地文件名 | 大小 |
|---|---|---|---|
| 2507.19090 | ✅ | `2507.19090_debate.pdf` | 1.1 MB |
| 2508.03092 | ✅ | `2508.03092_verifiable.pdf` | 2.7 MB |
| 2505.22993 | ✅ | `2505.22993_vegraph.pdf` | 2.2 MB |
| 2607.25069 | ✅ | `2607.25069_checkthat.pdf` | 872 KB |
| 2503.07937 | ✅ | `2503.07937_corroborating.pdf` | 968 KB |
| 2602.02569 | ✅ | `2602.02569_adversarial.pdf` | 886 KB |
| 2403.16632 | ✅ | `2403.16632_supply_chain_risk.pdf` | 691 KB |
| 2505.16120 | ✅ | `2505.16120_llm_agents_industry.pdf` | 1.8 MB |
| 2412.20138 | ✅ | `2412.20138_tradingagents.pdf` | 1.9 MB |
| 2405.14767 | ✅ | `2405.14767_finrobot.pdf` | 5.4 MB |
| 2505.15155 | ✅ | `2505.15155_rdagent_quant.pdf` | 3.2 MB |
| 2508.03860 | ✅ | `2508.03860_local_survey.pdf` | 5.2 MB |

**状态说明：** 2026-08-30 重新尝试下载成功。所有 PDF 已保存到 `research_materials/papers/` 目录。
