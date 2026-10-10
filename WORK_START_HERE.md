# 当前从这里开始

2026-10-10最新状态：[本机执行与交付Review](docs/semifinal/execution_update_20261010.md)。已接入34条公开财务样本，270项CSMAR原值仍待核；当前冻结技术题已在Windows独立复现，部署、真实录屏与01—07审阅材料完成。比赛工作区唯一入口为 `D:\notes\pkuaiagent`。

私人交付入口：工作区根目录 `复赛推进入口.md`；审阅材料位于 `deliverables/semifinal_20261012/`，实际运行证据位于 `work/semifinal_implementation_20261010/`。原始商业数据、比赛测试数据和私人提交包留在本地，不进入公开仓库。签名、真人试用、最终人工审阅及上传回执仍需负责人完成。

CSMAR公告续取用 `scripts/resume_csmar_announcements.py`，默认仅离线预览。只在已有校园权限且额度可用时显式 `--execute`；保留9个任务及按实际返回ID减少缺口，任何非零响应立即停止。正式字段定义仍未补齐。

2026-10-09：由 Codex 独立推进全部可完成项，暂不等待或分派 Kimi、Qwen 工作。负责人当前只需提供有校园数据库权限的原始导出。

1. [CSMAR 第一包下载清单](docs/semifinal/csmar_first_export.md)：688017、2024 年、合并三张表和字段说明，收到后再扩展。
2. [财务原页 Review](docs/semifinal/evidence/financial_review_20261009/review.md)：修正历史输入单位，新增 34 行真实年报数据；历史参考不会自动校准预测。
3. [离线接收工具](scripts/financial_intake.py)与[带溯源的长表模板](docs/semifinal/templates/financial_long_v2.csv)。
4. [10 月 9 日已完成材料与技术题 Review](docs/semifinal/execution_update_20261009.md)。该准备包是当时冻结版本，不自动包含后续财务改动。

下一步由 Codex 收原始导出、按真实字典映射、对照公告核查，再建立财务变化与技术声明之间可审查的参数联系。公开证据补充、验证、交付与材料修订继续由 Codex 执行。历史多模型任务保留供以后接续，当前不是执行依赖。
