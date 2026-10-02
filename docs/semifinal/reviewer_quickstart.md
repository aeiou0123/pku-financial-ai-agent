# 复赛作品：本地操作与证据导览

日期：2026-10-02。本轮代码位于 feat/semifinal-review-ui-20261002 分支，合并前 main 不包含本轮界面。

## 启动

安装 Python（本轮实测 Python 3.12）。下载该实现分支完整仓库，解压路径后：

- Windows：双击根目录 start_demo.bat。检测失败会显示错误并停留。Windows 脚本尚待真实 Windows 电脑验收。
- Linux：仓库根目录执行 `bash start_demo.sh`。
- 浏览器打开 http://127.0.0.1:8501 。本地版本不需要账号，不需要大模型密钥。

脚本创建独立 .venv-demo 并安装 requirements-demo.txt。首次安装需要联网；此文件固定直接依赖版本，尚非全量跨平台锁文件。安装好后可离线执行：

Windows：`.venv-demo\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501 --browser.gatherUsageStats false`

Linux：`.venv-demo/bin/python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501 --browser.gatherUsageStats false`

运行不调用外部API、不开启遥测；点击来源链接会在浏览器访问外站。退出在启动窗口 Ctrl+C。8501 被占用时将命令端口改为8502，浏览器同步改端口。不要将本机localhost地址填作评委远程访问地址。

## 三条操作路径

1. 示例情景：选择绿的谐波，点击运行示例。查看规则判断、证据状态与待核页码，再查看经济假设、因果批判、三情景；切换双环传动后重新运行，核对公司及产品线。两个示例使用已有固定公司参数和假设，不代表该条声明的已识别因果效应。
2. 自定义核查：粘贴声明、证据原文，可填来源链接与标题/页码，点击核查。规则能检出确定性矛盾或限定条件；没有明确规则判断时拒绝推断。自定义输入未绑定核对后的公司参数，因此不会自动套用示例估值。
3. 导出：查看证据与出处，下载JSON结构化记录和Markdown报告。包含真实提交输入、原文指纹、UTC时间、模式、限制、本次计算耗时。修改表单尚未提交时，界面保留并标明上次提交的记录。

空声明显示错误并清除旧结果，避免把旧报告误当作本次成功。证据留空会给缺证/拒答输出。来源链接和页码为记录字段，不会据此自动核实原PDF；不支持PDF上传/OCR。表内来源可信度、规则置信度未校准为现实事件概率。

## 本轮实测

- `python -m pytest tests -q`：148 passed（原140项加8项本轮回归；包括Streamlit AppTest表单/案例切换/下载控件/空输入）。
- Linux Python 3.12独立 .venv-demo：依赖安装完成，Streamlit健康接口返回ok，独立环境AppTest运行绿的谐波示例通过。
- `git diff --check`、Python编译、`bash -n start_demo.sh` 通过。
- Windows脚本实际运行、真实浏览器视觉检查、非开发成员试用尚未验收；不宣称已通过这些项目。

AppTest是模拟页面交互测试，不等同真人使用或浏览器视觉检查。记录中的毫秒数是该次本地函数计算耗时，未含阅读、联网、大模型或端到端用户操作；不能拿它证明完整在线Agent的成本与延迟。

## 技术证据索引

`docs/semifinal/evidence/offline_review_20261002/` 保存本次真正运行的4组输入输出：

| 文件前缀 | 场景 | 验收结果 |
|---|---|---|
| green_demo | 绿的谐波固定示例 | 部分支持；三情景完成 |
| shuanghuan_demo | 双环传动固定示例 | 部分支持；对应公司三情景完成 |
| missing_evidence | 无证据 | abstain；不产生财务结论 |
| unresolved_semantics | 有文本但规则不足以判断 | abstain；不产生财务结论 |

每组JSON为完整结构化结果，Markdown为报告；run_index.json记录环境、输入与关键代码SHA-256、实际耗时和错误列表。四组是功能演示，不是准确率统计，也没有新大模型评测结果。

复跑到全新目录：`python scripts/record_review_cases.py --out work/review_run_new`。脚本拒绝覆盖已有目录，避免混入旧记录。

建议最终05_技术证据引用此索引与对应案例，06_本地部署包含根目录启动文件、requirements-demo.txt、app.py、src/和流水线需要的data/processed文件。本轮尚未制作最终部署zip或视频；记录不替代视频真实操作。

## 下一轮

接上交结构化财务及西交原件后，先核对字段与证据页，再扩充公司/模型覆盖与时间外验证。材料中区分本轮已实现能力、已有数据下的示例、待开发能力。匿名因子技术题独立开展，不能以本界面的估值模型替代技术题建模。
