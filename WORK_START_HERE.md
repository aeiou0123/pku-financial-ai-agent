# Claim2Value 研究工作台

面向机器人产业链研究的本地工作台。三个任务：**观点审查**（把企业表述拆成待检查条件，在材料中检索支持与反证）、**财务整理**（从年报提取财务候选，核验后做两期盈利变化）、**策略回测**（先体检行情数据，再算净值、回撤与同费率基准）。

## 怎么开始

Windows 双击 `start_harness.bat`；Linux 或 macOS 执行：

```bash
bash start_harness.sh
```

浏览器打开 http://127.0.0.1:8510 。默认无需账号；财务核验、数据体检与回测都是本地规则，**不需要模型密钥**。只有候选整理与观点检索要按需连接自备的模型接口。

## 当前状态

- 已验证案例：绿的谐波（688017）2024 年年度报告，13 页。两轮实测对照见 [README](README.md#真实运行结果2024-年年度报告688017)。
- 财务提取具备逐字引用锚定与报表口径校验，收据在 `deliverables/semifinal_20261012/` 的提交包内。
- Windows 11 一键启动已实际验收；Linux 提供同一套脚本，未在真机验证。

## 主要文档

- [README](README.md) — 项目概览、核心机制与真实运行结果
- [入门教程](docs/harness/getting_started.md) / [产业研究工作流](docs/harness/industry_workflow.md)
- [模型连接](docs/harness/model-connections.md) / [资料目录](docs/harness/announcement_catalog.md)
- [开发记录](docs/CHANGELOG.md)
- [协作约定](CONTRIBUTING.md)

初赛版本的本地 Demo 仍在仓库根目录（`app.py`、`start_demo.*`），不是当前入口；冻结的技术题见提交包内的 `07_技术题/`。

商业数据库原始导出、校园账号与密钥留在授权私有目录，不进入本仓库与提交包。
