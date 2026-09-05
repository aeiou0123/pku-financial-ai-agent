# Claim2Value 研究资料库

本目录保存了北京大学金融 AI 智能体创新大赛 Claim2Value 项目的调研资料、文献、数据源和完整执行规划。

## 目录结构

```
research_materials/
├── papers/                         # 学术文献
│   └── bibliography.md            # arXiv 论文元数据、摘要、链接
├── github_repos/                   # GitHub 参考项目
│   └── github_reference_notes.md  # 12 个参考项目的详细笔记
├── data/                           # 数据（待填充）
├── notes/                          # 调研笔记和规划
│   ├── data_sources_and_config.md # 数据源、API、模型配置
│   └── feasibility_analysis_and_plan.md  # 深度可行性分析 + 2 周执行规划
└── benchmarks/                     # benchmark 数据集（待填充）
```

## 快速导航

- **想看最终推荐和计划**：打开 `notes/feasibility_analysis_and_plan.md`
- **想看数据源和模型配置**：打开 `notes/data_sources_and_config.md`
- **想看参考开源项目**：打开 `github_repos/github_reference_notes.md`
- **想看学术文献**：打开 `papers/bibliography.md`

## 重要说明

由于当前网络环境限制，无法直接从 arxiv.org 下载 PDF，也无法从 GitHub clone 仓库。因此：
- 论文以**元数据 + 摘要 + 链接**形式保存
- GitHub 项目以**详细笔记**形式保存
- 正式深度阅读和代码复用前，请在可访问外网的环境中下载原始资料

## 当前用途与下一步

本目录中的可行性分析、参考项目和论文笔记是项目早期研究资料，执行计划中的 Day 1–14 日期已经过期，不应作为当前进度依据。

当前仓库已经完成数据收集基础、Claim benchmark 和第一版 Claim 验证引擎。下一阶段以绿的谐波为主案例，优先开发：

1. 可追溯的简化财务模型；
2. 本地可复现的验证到财务影响 Demo；
3. 验证规则测试和误判修复。

当前实际进度请以根目录 [`README.md`](../README.md)、[`TODO.md`](../TODO.md) 和 [`SYNC_LOG.md`](../SYNC_LOG.md) 为准。
