# 当前从这里开始

2026-10-11使用体验调整：默认任务首页，新增教程与直接载入样例、无API本地计算体验、成果记录下载。估值和策略诊断按需开启，常用财务列改用中文展示；原有核验要求保留。[入门教程](docs/harness/getting_started.md)、[本轮Review](docs/harness/customer_experience_review_20261011.md)。同学继续拉取 `industry-research-harness-20261010`；没有重建旧01—07正式材料。

2026-10-11同学试用反馈已按13张截图核对并修复：长报告分批、有限重试、部分成果与缓存续取、可见披露日期、本地计划模板、中文现金流输入。测试分支继续使用 `industry-research-harness-20261010`；[更新与试用入口](docs/harness/teammate_trial.md)、[本轮Review](docs/harness/peer_feedback_review_20261011.md)。464项测试和8组本机模拟页面流程通过；未调用同学的实际网关，未将开发核验当真人业务效果。此次研究工作台包更新，冻结技术题与旧01—07材料不在改动范围。

2026-10-10 本轮已接入论点审查与明确证据绑定、受产能和投产时点约束的盈利／估值兑现条件、预先声明参数的策略诊断。默认从“论点审查与兑现条件”进入，原财务整理与盈利桥保留。见[产业研究操作](docs/harness/industry_workflow.md)和[本次Review](docs/harness/industry_review_20261010.md)。全库401项、5项新增浏览器流程、8项旧流程回归通过；真实模型质量和真人业务效果未测。下文旧状态保留为历史记录，旧01—07包未覆盖。

2026-10-10 产业投研方向复核：重新读取复赛通知与附件，检查原项目和新工作台的差距，并接入两期盈利变化解释。财务数据确认和校验后，选择年度比较口径，点击“生成盈利变化研究底稿”；详见 [产品针对性审查与改造](docs/harness/product_revision_20261010.md)。论点证据审查、带产能和时点约束的估值兑现条件，以及策略整体诊断仍为后续模块，不将它们写成已完成。旧正式01—07材料暂未重建。

2026-10-10 产品方向调整：负责人要求模型 API＋上传文件的研究 harness，财务／估值与量化处理／回测分开。新增 `harness_app.py`、`start_harness.bat`，本机端口 8510；见 [操作说明](docs/harness/README.md) 与 [检查记录](docs/harness/review.md)。运行私存于 `work/harness_runs/`，独立部署包位于 `deliverables/harness_20261010/`。本轮沿用已完成 UI 分支为基础，不修改冻结技术题，也没有自动重建旧 01—07 提交包；新产品进入正式提交材料前仍需真实模型试跑、真人审阅和材料重录。

2026-10-10最新状态：[本机执行与交付Review](docs/semifinal/execution_update_20261010.md)。已接入34条公开财务样本，270项CSMAR原值仍待核；当前冻结技术题已在Windows独立复现，部署、真实录屏与01—07审阅材料完成。比赛工作区唯一入口为 `D:\notes\pkuaiagent`。

私人交付入口：工作区根目录 `复赛推进入口.md`；审阅材料位于 `deliverables/semifinal_20261012/`，实际运行证据位于 `work/semifinal_implementation_20261010/`。原始商业数据、比赛测试数据和私人提交包留在本地，不进入公开仓库。签名、真人试用、最终人工审阅及上传回执仍需负责人完成。

CSMAR公告续取用 `scripts/resume_csmar_announcements.py`，默认仅离线预览。只在已有校园权限且额度可用时显式 `--execute`；保留9个任务及按实际返回ID减少缺口，任何非零响应立即停止。正式字段定义仍未补齐。

2026-10-09：由 Codex 独立推进全部可完成项，暂不等待或分派 Kimi、Qwen 工作。负责人当前只需提供有校园数据库权限的原始导出。

1. [CSMAR 第一包下载清单](docs/semifinal/csmar_first_export.md)：688017、2024 年、合并三张表和字段说明，收到后再扩展。
2. [财务原页 Review](docs/semifinal/evidence/financial_review_20261009/review.md)：修正历史输入单位，新增 34 行真实年报数据；历史参考不会自动校准预测。
3. [离线接收工具](scripts/financial_intake.py)与[带溯源的长表模板](docs/semifinal/templates/financial_long_v2.csv)。
4. [10 月 9 日已完成材料与技术题 Review](docs/semifinal/execution_update_20261009.md)。该准备包是当时冻结版本，不自动包含后续财务改动。

下一步由 Codex 收原始导出、按真实字典映射、对照公告核查，再建立财务变化与技术声明之间可审查的参数联系。公开证据补充、验证、交付与材料修订继续由 Codex 执行。历史多模型任务保留供以后接续，当前不是执行依赖。
