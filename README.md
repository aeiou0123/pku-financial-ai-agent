# Claim2Value — 北大金融 AI 智能体创新大赛

> 工业技术 Claim → 工程证据 → 经济机制 → 金融价值的可信映射 Agent

## 项目定位

Claim2Value（Evidence-Grounded Engineering-to-Finance Agent）面向产业链技术突破的金融价值评估：把企业关于技术升级、产能扩张、供应链重构的**宣称（Claim）**，通过多源证据进行**验证与追溯**，输出**可审计、可量化、可复盘**的财务影响分析。

**本次 Demo 聚焦**：机器人关节模组产业链  
**主案例**：绿的谐波（谐波减速器）  
**辅助案例**：步科股份（无框力矩电机）、双环传动（RV 减速器）

> 产品不是专用工具，而是通用 Agent。三个案例分别验证**技术性能、产能需求、客户订单**三类典型 claim。

## 当前进展（2026-09-08，Phase 3D 完成 / 答辩待命）

代码、数据与文档已收口至交付前状态，质量线：**140 个回归测试全过 + 提案审校脚本 0 issue**（`python -m pytest tests -q`、`python scripts/audit_proposal.py`）。PR #2–#26 全部合并到 `main`，当前能力全景：

**1. 多公司证据网络（PR #15/#21）**：Claim Bank 扩展至 **11 家机器人产业链公司 51 条结构化 claim**——36 条已验证（公告原文级，附页码与内容指纹，BK_004 双源逐字、GH_002 双源互证），15 条待验证（带显式定义疑点，终验核对清单 `docs/proposal/appendix_pending_review.md` 由 Phase 3D 新增）；另有 1 条行业市场数据（IND_001）。

**2. 双环传动全链路估值链（PR #20）**：financial_model 泛化到多产品线（rv/gear 自动识别），economic_mapper 支持规则级 `product_line_scope`，ontology 变体 `tech_to_economics_ontology_shuanghuan.json` + `data/processed/shuanghuan_model_inputs.csv`，端到端输出三情景 EV **72.66 / 122.89 / 19.04 亿元**（base/upside/downside；PR #28 按环动招股书实际均价校准 RV 参数后），回归覆盖 `tests/test_shuanghuan_chain.py`。

**3. 反向 DCF 视角（PR #19）**：以 2026-09-04 市值 512.96 亿元反推，绿的谐波现价隐含销量倍数 **16.66×**；三情景下市价与内在价值 gap 为 **-94.00% / -88.60% / -99.82%**（PR #28 参数复核后口径）——"以价换量"放量逻辑与 365 倍 PE 期权定价并存的现象被量化呈现。

**4. 工程性能（PR #18）**：规则链延迟基准 N=30 实测 **p50 4.3ms / p95 5.0ms**（同日三次复测 3.7–4.3ms）（`scripts/benchmark_latency.py`，报告 `benchmarks/latency_report.md`）。

**5. 演示与答辩材料**：`docs/proposal/` 01–09 章成稿（产品、案例、商业论证、路线图、合规、答辩问答预案）；演示脚本（10 章）与路演 PPT 大纲（11 章）在 Phase 3D 补齐。

> 历史里程碑：PR #2 时代 98 个 benchmark 用例规则层 + LLM pipeline 判别准确率 Claude 83.7% / GPT 82.7%（测试集准确率，非业务最终准确率）。实时检索、专利核验全覆盖属赛后增强方向。完整状态见 [`TODO.md`](TODO.md)、[`SYNC_LOG.md`](SYNC_LOG.md) 与 [`docs/KIMICODE_PROGRESS.md`](docs/KIMICODE_PROGRESS.md)。

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
│   ├── financial_model.py            # 可追溯简化财务模型（含反向 DCF）
│   ├── economic_mapper.py            # 工程指标→经济机制映射
│   ├── engineering_analyzer.py       # 工程语义分析
│   ├── causal_critic.py              # 因果批判
│   ├── claim_bank_writer.py          # Claim Bank 结构化写入
│   ├── workflow.py                   # 串联验证工作流（四模块函数链）
│   └── data_tools/                   # PDF/文本候选提取脚本
├── scripts/                          # 工具脚本
│   ├── audit_proposal.py             # 提案文档审校（当前 0 issue）
│   └── benchmark_latency.py          # 规则链延迟基准
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

1. `docs/KIMICODE_PROGRESS.md` —— 30 秒项目进度入口
2. `data/collection_checklist.md` —— 数据收集清单
3. `data/search_report.md` —— 已完成资料与人工补充清单
4. `src/workflow.py` —— 验证到财务影响的串联链路

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
python -m pip install -r requirements.txt
python -m src.financial_model
python app.py --json-out data/processed/local_demo_result.json
python -m pytest tests -q
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

| 公司 | 代码 | 细分 | Claim 数（已验证/待验证） | 代表 Claim |
|---|---|---|---|---|
| 绿的谐波 | 688017 | 谐波减速器 | 7（6/1） | 新一代关节模组扭矩密度提升 30%；市值 512.96 亿锚点 |
| 步科股份 | 688160 | 无框力矩电机 | 5（3/2） | 第四代 FMK 功率密度提升 20%，出货 8.3 万台（+247%） |
| 双环传动 | 002472 | RV 减速器 | 6（4/2，含子公司环动科技 3 条） | RV 扭矩密度 180 N·m/kg；环动市占率 10.11%→提升；产能利用率 >100% |
| 中大力德 | 002896 | 减速器+电机 | 4（4/0） | 技术性能类 claim 全验证 |
| 鸣志电器 | 603728 | 步进/伺服电机 | 4（4/0） | 产能需求类 claim 全验证 |
| 柯力传感 | 603662 | 力矩传感器 | 4（4/0） | 技术性能类 claim 全验证 |
| 五洲新春 | 603667 | 丝杠/轴承 | 4（1/3） | 行星滚柱丝杠进展（3 条待终验） |
| 贝斯特 | 300580 | 丝杠/精密零部件 | 4（2/2） | 线性执行器产能扩张 |
| 恒立液压 | 601100 | 液压/丝杠 | 4（1/3） | 电动缸业务进展（3 条待终验） |
| 国茂股份 | 603915 | 减速器 | 4（3/1） | 产能/需求类 claim |
| 秦川机床 | 000837 | 齿轮磨床/减速器 | 4（3/1） | 产能/需求类 claim |

另有行业市场数据 1 条（IND_001，工业机器人市场）。51 条结构化明细见 `data/processed/claim_bank_filled.json`，原文摘录与核验指纹见 `docs/proposal/appendix_pending_review.md` 与 04 章。

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

## 当前任务（Phase 3D 完成后的交付准备）

1. 15 条待验证 Claim 人工终验（核对清单已备好：`docs/proposal/appendix_pending_review.md`）；
2. 经济金融组复核模型输入、BOM、税率、DCF 与 RV ontology 参数；
3. 演示彩排：按 `docs/proposal/10_demo_script.md` 走一遍 3 分钟版 + fallback 版；
4. 赛后增强（非阻塞）：实时检索、专利核验全覆盖、更多产业链公司接入。

首版 Demo 已覆盖绿的谐波本地单案例流程与双环传动全链路估值链；不以实时检索、全行业覆盖或全部 Claim 核验为阻塞条件。

## 注意事项

- 本仓库仅用于比赛协作学习，不构成投资建议。
- 第三方代码请遵守各自 LICENSE。
- 所有外部数据需标注来源，避免使用未公开内部信息。
