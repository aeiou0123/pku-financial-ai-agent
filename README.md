# Claim2Value — 北大金融 AI 智能体创新大赛

> 工业技术 Claim → 工程证据 → 经济机制 → 金融价值的可信映射 Agent

## 项目定位

Claim2Value（Evidence-Grounded Engineering-to-Finance Agent）面向产业链技术突破的金融价值评估：把企业关于技术升级、产能扩张、供应链重构的**宣称（Claim）**，通过多源证据进行**验证与追溯**，输出**可审计、可量化、可复盘**的财务影响分析。

**本次 Demo 聚焦**：机器人关节模组产业链  
**主案例**：绿的谐波（谐波减速器）  
**辅助案例**：步科股份（无框力矩电机）、双环传动（RV 减速器）

> 产品不是专用工具，而是通用 Agent。三个案例分别验证**技术性能、产能需求、客户订单**三类典型 claim。

## 参赛方向

- **赛道一（金融智能体创新应用）**：Claim2Value Agent 的工作流创新
- **赛道二（量化策略与智能体）**：技术事件驱动的基本面分析
- **赛道三（金融行业场景落地）**：聚焦机器人关节产业链场景

## 目录结构

```
.
├── README.md
├── requirements.txt                  # Python 依赖（待补充）
├── app.py                            # Streamlit/Gradio Demo
├── src/                              # 核心代码
│   ├── case.py                       # 通用案例抽象层
│   ├── claim_extractor.py            # Claim 提取
│   ├── evidence_retriever.py         # 证据检索
│   ├── evidence_ledger.py            # 证据账本
│   ├── claim_verifier.py             # Claim 验证
│   ├── engineering_analyzer.py       # 工程分析
│   ├── economic_mapper.py            # 经济机制映射
│   ├── financial_model.py            # 财务模型
│   ├── causal_critic.py              # 因果批判
│   ├── state_verifier.py             # 状态验证
│   └── workflow.py                   # LangGraph workflow
├── data/                             # 数据资料
│   ├── README.md                     # 数据目录说明
│   ├── collection_checklist.md       # 数据收集总清单
│   ├── search_guide.md               # 案例搜索方案
│   ├── raw/                          # 原始 PDF/资料
│   └── processed/                    # 结构化数据
├── benchmarks/                       # 测试基准
├── tests/                            # 单元测试
├── notebooks/                        # 分析笔记本
├── research_materials/               # 研究资料
│   ├── papers/                       # arXiv 论文（gitignored）
│   ├── github_repos/                 # 参考仓库（gitignored）
│   └── notes/                        # 研究笔记
├── setup_research_env.bat            # 一键下载论文+参考仓库
└── 北大金融AI智能体大赛_*.md        # 团队讨论记录
```

## 团队快速开始

### 1. Clone 仓库

```bash
git clone https://github.com/aeiou0123/pku-financial-ai-agent.git
cd pku-financial-ai-agent
```

### 2. 下载研究资料

双击运行 `setup_research_env.bat`，自动下载：
- 12 篇 arXiv 论文 → `research_materials/papers/`
- 12 个参考 GitHub 仓库 → `research_materials/github_repos/`

### 3. 阅读核心文档

1. `data/search_guide.md` —— 案例搜索方案
2. `data/collection_checklist.md` —— 数据收集清单
3. `research_materials/notes/feasibility_analysis_and_plan.md` —— 执行计划
4. `src/case.py` —— 通用案例抽象层

## 案例设计

| 公司 | 代码 | 细分 | 核心 Claim | 验证能力 |
|---|---|---|---|---|
| 绿的谐波 | 688017 | 谐波减速器 | 新一代关节模组扭矩密度提升 30% | 技术性能 claim |
| 步科股份 | 688160 | 无框力矩电机 | 第四代 FMK 功率密度提升 20%，出货 8.3 万台（+247%） | 产能/需求 claim |
| 双环传动 | 002472 | RV 减速器 | RV 扭矩密度 180 N·m/kg，获特斯拉 4000 套订单 | 客户/订单 claim |

## 协作规范

- **分支**：每人从 `main` 切出功能分支，如 `feat/claim-extractor`
- **提交**：小步提交，写清楚 commit message
- **合并**：通过 Pull Request 合并，不要直接 push
- **不提交**：API key、`.env`、PDF、第三方仓库、Python 缓存

## 当前任务

见 `data/collection_checklist.md` 中的 48 小时数据目标。

## 注意事项

- 本仓库仅用于比赛协作学习，不构成投资建议。
- 第三方代码请遵守各自 LICENSE。
- 所有外部数据需标注来源，避免使用未公开内部信息。
