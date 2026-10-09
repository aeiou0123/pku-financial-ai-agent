# Kimi 从这里开始

2026-10-09。GitHub作为代码、任务和可公开交付的协作入口；Codex与Kimi各自使用独立分支和PR。本项目日常读写、提交与推送已有负责人授权，无需重复申请；客户端GitHub登录仍按实际状态处理。

## 一次读齐

1. [AGENTS.md](AGENTS.md)：整个仓库的协作约定。
2. [本轮执行单](docs/semifinal/agent_tasks/xjtu_kimi.md)。
3. [完整任务提示词](docs/semifinal/agent_tasks/kimi_prompt_20261009.md)。
4. [四条回传模板](docs/semifinal/templates/kimi_return_template.json)。
5. [原页Review与指纹](docs/semifinal/evidence/kimi_handoff_review_20261009.json)。
6. [Claim Bank原始声明与历史记录](data/processed/claim_bank_filled.json)：只筛本轮四个ID；[10月3日官网复核](docs/semifinal/evidence/primary_source_review_20261003/review.json)作为待重新取原件的线索。

三份PDF都已在仓库，克隆即可取得：

| 文件 | 先看哪里 |
|---|---|
| [国金2022减速器研报](data/raw/analyst_reports/humanoid_robot_joint_reducer_202209.pdf) | PDF24页图表46、33页图表65；全文件45页 |
| [步科2025半年报](data/raw/company_filings/buke_2025_halfyear_report.pdf) | PDF16页，第四代FMK发布；全文件207页 |
| [群益2025-07-17研报](data/raw/analyst_reports/buke_2025q2_review.pdf) | PDF1页，蓝皮书引用；全文件4页 |

先读已有原件，再按四条缺口找新原件。SHA-256与来源线索在Review中；不要把历史meta注释直接当已核实的页数或发布时间。原页预览在[Drive任务包](https://drive.google.com/file/d/11ltIfiI4GrgRuxLS5fDIh1mEUiTDGURV/view)内，克隆后也可自行渲染PDF。

## 用 GitHub CLI 开始

先检查登录（无需打印token）：

```bash
gh auth status
gh repo clone aeiou0123/pku-financial-ai-agent pku-claim2value-kimi
cd pku-claim2value-kimi
git switch -c kimi/evidence-20261009
```

若已有工作区，先检查git status和未提交修改，fetch后从最新origin/main新建独立分支或worktree；不要覆盖现有目录。分支名已存在则换唯一后缀。没有有效登录由本人完成GitHub CLI正常登录，不提交token到仓库。

## 本轮交付位置

新建docs/semifinal/evidence/kimi_runs/20261009_01/（已存在就加序号），放：

- candidates.json：填好的四条JSON，一条声明一条主要证据。
- urgent_claim_status.md：四条真实状态、已读原页、缺件、冲突和下一步。
- download_status.md：实际联网/文件工具、查找范围、下载结果、耗时和费用状态。
- source_manifest.csv：真实原件标题、来源、日期、文件指纹、再分发许可。
- review.md：自查结果、人工待核事项、运行验证与交付摘要。

可公开的新原件放data/raw对应目录并带meta索引；许可不明、付费或校园数据库文件留在私有Drive/本人目录。候选中的file_name仍指向本地原件目录下相对文件名，文件未在仓库时在状态表明确说明其授权存放处。公开候选仅保留必要短摘录；不能取得原文时如实留空。

用prepare_kimi_evidence.py检查回传；大于0条可进入文本核查后才运行review_evidence_batch.py，具体命令见执行单。回传存在候选链接或未找到时仍可交PR，不把未完成内容填成已验证。

## 提交与接续审查

只暂存本轮明确文件，用git diff --cached检查内容。下列目录名按实际修改；原件等其他文件逐项明确暂存：

```bash
git add docs/semifinal/evidence/kimi_runs/20261009_01
git diff --cached
git commit -m "Record Kimi primary evidence candidates"
git push -u origin kimi/evidence-20261009
gh pr create --repo aeiou0123/pku-financial-ai-agent --base main --head kimi/evidence-20261009 --title "Kimi: primary evidence for four pending claims" --body-file docs/semifinal/evidence/kimi_runs/20261009_01/review.md
```

返回PR链接。Codex读取PR和原件索引后接续审核与材料更新；Kimi不要在审查未完成时把候选升级为正式项目结论。完整任务可在一轮60—90分钟内先交真实已完成部分，无需等待所有来源都齐。

Google Drive是私有原件的补充渠道。本轮已有三份PDF、提示词和模板无需Drive权限即可从GitHub开始。

CLI命令参考：[gh repo clone](https://cli.github.com/manual/gh_repo_clone)、[gh pr create](https://cli.github.com/manual/gh_pr_create)。本轮只修改协作说明及入口，已核对新增链接和三份PDF的Git对象指纹；未在本环境运行Kimi的GitHub CLI。
