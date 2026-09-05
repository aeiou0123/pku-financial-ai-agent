# Claim2Value — 北大金融 AI 智能体创新大赛

> 工业技术 Claim → 工程证据 → 经济机制 → 金融价值的可信映射 Agent

## 项目定位

Claim2Value（Evidence-Grounded Engineering-to-Finance Agent）面向产业链技术突破的金融价值评估：把企业关于技术升级、产能扩张、供应链重构的**宣称（Claim）**，通过多源证据进行**验证与追溯**，输出**可审计、可量化、可复盘**的财务影响分析。

**本次 Demo 聚焦**：机器人关节模组产业链  
**主案例**：绿的谐波（谐波减速器）  
**辅助案例**：步科股份（无框力矩电机）、双环传动（RV 减速器）

> 产品不是专用工具，而是通用 Agent。三个案例分别验证**技术性能、产能需求、客户订单**三类典型 claim。

## 当前进展（2026-09-05）

PR #2 已合并到 `main`。Claim benchmark、Evidence Ledger、StateVerifier、ClaimVerifier 和验证 workflow 已可运行；98 个 benchmark 用例的规则层 + LLM pipeline 结果为 Claude 83.7%、GPT 82.7%。这些是测试集判别准确率，不是现实业务最终准确率。

当前已进入下一阶段首个可运行切片：

- 绿的谐波简化财务模型：输出 base/upside/downside 三种情景，并在输入表中区分历史锚点、人工假设和计算结果；
- 本地单案例 Demo：使用本地 evidence fixture，不调用外部 API；
- 最小回归测试：覆盖模型可复算性、输入溯源和 Demo 的保守判定。

模型输入、Claim 证据和 Demo 输出仍需人工复核；官方 datasheet、专利核验、全部 Claim evidence 回填和实时检索属于后续证据增强任务。完整状态见 [`TODO.md`](TODO.md) 和 [`SYNC_LOG.md`](SYNC_LOG.md)。

## 参赛方向

- **赛道一（金融智能体创新应用）**：Claim2Value Agent 的工作流创新
- **赛道二（量化策略与智能体）**：技术事件驱动的基本面分析
- **赛道三（金融行业场景落地）**：聚焦机器人关节产业链场景

## 目录结构

```
.
├── README.md
├── requirements.txt                  # 模型与可选 Streamlit 依赖
├── app.py                            # 本地 Demo（默认无 API）
├── src/                              # 核心代码
│   ├── case.py                       # 通用案例抽象层
│   ├── evidence_ledger.py            # 证据账本
│   ├── claim_verifier.py             # Claim 验证
│   ├── state_verifier.py             # 状态/口径验证
│   ├── financial_model.py            # 可追溯简化财务模型
│   ├── workflow.py                   # 验证工作流（当前为纯 Python 函数链）
│   └── data_tools/                   # PDF/文本候选提取脚本
├── data/                             # 数据资料
│   ├── README.md                     # 数据目录说明
│   ├── collection_checklist.md       # 数据收集总清单
│   ├── search_guide.md               # 案例搜索方案
│   ├── raw/                          # 原始 PDF/资料
│   └── processed/                    # 结构化数据
├── benchmarks/                       # Claim benchmark、pipeline 报告与结果
├── tests/                            # unittest 回归测试
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

### 4. 运行当前验证 MVP

规则层和无证据路径不需要 API key：

```bash
python -m compileall -q src benchmarks
python -m src.workflow --single --claim "绿的谐波新一代谐波减速器关节模组减重30%以上"
python -m src.claim_verifier --no-llm --limit 98
```

完整 LLM 验证需要工作区外部的 Prism 配置或 `~/.workbuddy/models.json`，配置文件和 API key 不得提交。

### 5. 运行财务模型与本地 Demo

安装依赖后，财务模型使用带来源标签的本地输入，输出三种情景：

```bash
pip install -r requirements.txt
python -m src.financial_model
python app.py --json-out data/processed/local_demo_result.json
python -m unittest discover -s tests -v
```

模型输出：

- `data/processed/green_harmonic_model.xlsx`：Inputs 溯源表、Summary 和 base/upside/downside 情景；
- `data/processed/green_harmonic_model_results.json`：同一结果的机器可读版本；
- `data/processed/local_demo_result.json`：本地 Demo 的证据、规则结论、限制和财务影响。

可选 Streamlit 界面：

```bash
streamlit run app.py
```

本地 Demo 不调用外部 API。规则层发现确定性问题时才输出对应结论；否则返回 `abstain`，避免把没有 LLM 语义判断的路径误报为“成立”。财务模型目前是情景原型，Inputs 表会明确区分 `historical`、`assumption` 和运行时 `calculated` 结果，不构成投资建议。

## 案例设计

| 公司 | 代码 | 细分 | 核心 Claim | 验证能力 |
|---|---|---|---|---|
| 绿的谐波 | 688017 | 谐波减速器 | 新一代关节模组扭矩密度提升 30% | 技术性能 claim |
| 步科股份 | 688160 | 无框力矩电机 | 第四代 FMK 功率密度提升 20%，出货 8.3 万台（+247%） | 产能/需求 claim |
| 双环传动 | 002472 | RV 减速器 | RV 扭矩密度 180 N·m/kg，获特斯拉 4000 套订单 | 客户/订单 claim |

## 协作规范

### 团队成员

| GitHub 账号 | 姓名 | 角色 |
|---|---|---|
| `aeiou0123` | （仓库所有者） | 项目主导、数据收集、Agent 开发 |
| `shushuyang231` | Sun Shengyao | 协作者（write 权限） |
| `FeishengLuo` | Feisheng Luo | 协作者（write 权限） |

### 首次加入（新协作者请按此操作）

1. **接受邀请**：打开 https://github.com/aeiou0123/pku-financial-ai-agent/invitations ，点击 Accept
   （邀请邮件也可能发到你的 GitHub 注册邮箱，主题含 "You've been invited to collaborate"）
2. **配置 Git 身份**（如果还没配置过）：
   ```bash
   git config --global user.name "你的名字"
   git config --global user.email "你的GitHub注册邮箱"
   ```
3. **克隆仓库**：
   ```bash
   git clone https://github.com/aeiou0123/pku-financial-ai-agent.git
   cd pku-financial-ai-agent
   ```
4. 开始工作前，养成习惯先拉取最新代码：
   ```bash
   git pull origin main
   ```

### 日常协作流程（小团队实用版）

我们团队人少，采用**轻量流程**：文档/数据更新可直接推 main，代码功能建议走分支。

**场景 A：改文档、补数据（直接推 main）**
```bash
git pull origin main          # 先同步
# ... 修改文件 ...
git add .
git commit -m "docs: 修改说明"
git push origin main
```

**场景 B：开发代码功能（走分支 + PR）**
```bash
git checkout -b feat/功能名    # 从 main 切分支
# ... 写代码，多次小提交 ...
git push -u origin feat/功能名
gh pr create                  # 发起 Pull Request（可选）
```

**冲突避免铁律**：每次开工前 `git pull`，推不上去时先 pull 再推。

### Commit Message 规范

```
type: 简短说明

type 取值：
- feat   新功能
- fix    修复 bug
- docs   文档
- data   数据文件
- test   测试
- refactor 重构
```

### 不提交的内容

API key、`.env`、`*.pdf`（研究报告类）、第三方仓库代码、Python 缓存（`__pycache__/`）

> 注意：公司公告/研报 PDF 在 `data/raw/` 下是**要提交**的，它们有 `.meta.json` 记录来源。

## 当前任务

1. 由经济金融成员复核简化模型的财务口径、BOM、税率和 DCF 假设；
2. 修复 StateVerifier 的数值、时间和复合 Claim 误判并补回归 fixture；
3. 继续补齐主案例可定位 evidence，再推进工程分析、经济映射和因果批判。

首版 Demo 只承诺绿的谐波本地单案例流程，不以实时检索、全行业覆盖或全部 Claim 核验为阻塞条件。

## 注意事项

- 本仓库仅用于比赛协作学习，不构成投资建议。
- 第三方代码请遵守各自 LICENSE。
- 所有外部数据需标注来源，避免使用未公开内部信息。
