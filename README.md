# Claim2Value — 北大金融 AI 智能体创新大赛

> 工业技术 → 工程证据 → 金融价值的可信映射 Agent

## 项目定位

Claim2Value（Industrial-Tech-to-Finance Agent）面向“产业链技术突破的金融价值评估”场景：把企业/行业关于技术升级、产能扩张、供应链重构的**宣称（Claim）**，通过多源证据（专利、财报、供应链、研报、专家访谈）进行**验证与追溯**，最终输出**可审计、可量化、可复盘**的财务影响分析（DCF / 弹性模型 / 风险传播模型）。

## 参赛方向

- **赛道一（金融智能体创新应用）**：Claim2Value Agent 的工作流创新
- **赛道二（量化策略与智能体）**：技术事件驱动的基本面量化/因子挖掘
- **赛道三（金融行业场景落地）**：聚焦机器人关节减速器 / 绿的谐波等工业场景

## 目录结构

```
.
├── README.md                                    # 本文件
├── 北大金融AI智能体大赛_团队讨论记录.md          # 团队讨论与项目方向
├── 北大金融AI智能体大赛_核心成员能力画像与项目定位修正版.md
├── research_materials/
│   ├── README.md                                # 资料导航
│   ├── notes/
│   │   ├── data_sources_and_config.md           # 数据源、API、模型配置
│   │   └── feasibility_analysis_and_plan.md     # 可行性分析与 14 天执行计划
│   ├── papers/
│   │   └── bibliography.md                      # 论文元数据、摘要、链接
│   └── github_repos/
│       └── github_reference_notes.md            # 参考 GitHub 项目笔记
├── setup_research_env.bat                       # 一键下载论文 + 参考仓库
└── .gitignore
```

## 团队快速开始

### 1. Clone 本仓库

```bash
git clone https://github.com/aeiou0123/<仓库名>.git
cd <仓库名>
```

### 2. 下载研究资料

双击运行 `setup_research_env.bat`，会自动：
- 克隆 12 个参考 GitHub 仓库到 `research_materials/github_repos/`
- 下载 12 篇 arXiv 论文到 `research_materials/papers/`

> 论文和参考仓库体积较大，已加入 `.gitignore`，不进入主仓库。

### 3. 阅读核心文档

按这个顺序：
1. `research_materials/notes/feasibility_analysis_and_plan.md` —— 整体计划与分工
2. `research_materials/notes/data_sources_and_config.md` —— 数据源与配置
3. `research_materials/papers/bibliography.md` —— 文献库
4. `research_materials/github_repos/github_reference_notes.md` —— 参考项目笔记

## 协作规范

- **分支**：每人从 `main` 切出自己的分支，例如 `feat/claim-extractor`、`feat/evidence-ledger`
- **提交**：小步提交，commit message 用中文或英文均可，但要写清楚做了什么
- **合并**：功能完成后通过 Pull Request 合并到 `main`，不要直接 push
- **不提交**：API key、`.env`、PDF、第三方仓库、Python 缓存

## 核心成员分工

详见 `北大金融AI智能体大赛_核心成员能力画像与项目定位修正版.md`。

## 注意事项

- 本仓库仅用于比赛协作学习，不构成投资建议。
- 第三方代码请遵守各自 LICENSE，比赛作品中明确标注引用来源。
