# Claim2Value 提交包说明

## 这是什么

这是“北大金融 AI 智能体创新大赛”的首版提交快照：项目表单素材、封面、路演 PPT、项目 PDF 说明文档、离线 Demo、核心代码、结构化数据、测试和答辩资料均已放入包内。

项目仓库：[https://github.com/aeiou0123/pku-financial-ai-agent](https://github.com/aeiou0123/pku-financial-ai-agent)

## 推荐提交文件

- `deliverables/cover_16x9.png`：16:9 项目封面
- `deliverables/Claim2Value_pitch.pptx`：12 页路演 PPT
- `deliverables/Claim2Value_项目说明文档.pdf`：项目说明 PDF
- `deliverables/submission_form.md`：网页表单可复制素材
- `app.py`、`src/`：离线 Demo 与核心实现
- `data/processed/`：可复现所需的结构化数据与本地 fixture
- `tests/`：回归测试
- `docs/proposal/`：项目书、答辩问答与演示脚本
- `team_and_sources.md`：团队成员与公开资料索引

## 本地运行

在解压后的项目根目录执行：

```text
python app.py
python -m pytest tests -q
python scripts/audit_proposal.py
```

Demo 默认不需要 API key；如未配置 LLM，系统保守降级到规则层/`abstain` 路径。估值结果是原型情景，不构成投资建议。

## 口径与边界

- Claim Bank：51 条结构化 Claim，47 条已验证、4 条保留待验证，并附显式疑点与后续核验路径。
- 2025H1 的双环传动收入数据按半年累计口径处理；不把研报误标的“Q2 单季”当成官方口径。
- 提交包有意排除 `data/raw/**/*.pdf`、`research_materials/papers/`、`research_materials/github_repos/`、`.git/`、缓存和临时文件，以控制体积、减少第三方资料再分发风险；原始资料索引和来源说明仍保留在项目文档中。
- 2026-09-09 本地快照可能比 GitHub `main` 多出尚未推送的文档/交付文件；提交时以本 ZIP 为准，后续再同步 GitHub。

## 赛后可继续完善

优先补齐 4 条待验证 Claim 的厂商 datasheet/蓝皮书原文、录制真人 Demo 视频，并将本地交付快照同步回 GitHub。
