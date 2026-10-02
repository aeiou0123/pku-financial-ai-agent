# 部署包、材料检查与技术题复现打包

日期：2026-10-02。工具帮助减少交付差错，不能替代效果验证和真人操作。

## 本地部署

仓库根目录执行：`python scripts/build_local_deployment.py --out work/Claim2Value_local_deployment.zip`。
输出只包含06_本地部署：运行代码、必要的示例数据、启动脚本和部署说明；不含密钥、校园账号、CSMAR导出、原PDF、虚拟环境或大模型。
解压后Windows双击start_demo.bat，Linux执行bash start.sh。首次安装依赖需要联网；依赖齐备且版本匹配时不再重复安装。无默认账号、无需模型密钥。
包内文件指纹见package_manifest.json。更改代码或数据后重新生成到新文件，不覆盖旧验收产物。

## 材料预检

先把最终材料按附件二放进一个目录，例如work/队名_Claim2Value。不要把单独部署ZIP当最终参赛ZIP。

`python scripts/check_semifinal_package.py work/队名_Claim2Value --json-out work/package_check.json`

可增加 `--tools C:\FEL_MARKET\tools.py --test C:\FEL_MARKET\test.parquet`，现场执行官方持仓check。
提供在线页面则加 `--online-url https://实际页面地址`；工具只记录和检查地址形式，不会替你测试账号或登录。localhost不能当评委远程地址。

工具检查必交文件、证据目录、部署启动文件、Word/PPTX可读性、技术题报告20页上限、持仓完整日历及20股结构。安装pypdf后检查PDF页面与书签；安装ffprobe后检查视频分辨率和时长。视频最低1280×720，建议5分钟内；容器没有章节不代表画面没章节，必须人工看。
缺件/损坏会返回BLOCKED和非零退出码；没有结构错误仍只返回STRUCTURE_VALID_MANUAL_REVIEW_REQUIRED，不叫“可提交”。信息表限字、PDF章节覆盖、四方面视频内容、证据真实性和作品可操作性必须人工复核。

本轮准备目录只放实际技术证据和本地部署，检查如实报缺失信息表、PDF、PPT、视频及技术题三件套。旧初赛文件没有未经修改就被冒称复赛成品。

## 技术题code.zip

实际完成predict后，使用同版本代码执行：

`python -m competition.package_code --run competition/runs/test_predictions --tools C:\FEL_MARKET\tools.py --test C:\FEL_MARKET\test.parquet --ai-tools "实际使用的工具及版本" --out work/code.zip`

拒绝验证集/模拟运行/未完成预测；检查持仓与模型是否变动、代码指纹是否匹配，并重新执行官方check。当前代码产生的run_summary有code_sha256；旧版本记录须先用当前版本重跑predict。
code.zip含实际模型JSON、原生成代码、运行记录、官方工具、依赖和复现脚本。复现时指定官方test.parquet目录，生成名单并比对原CSV指纹。原始数据不随包进入公开仓库。
本轮没有真实predict产物，因此没有制造占位code.zip或正式submission.csv；该工具用于真实结果到位后的封装。

## 验收状态

独立解压目录首次安装和启动健康检查通过，Streamlit AppTest通过；源码回归172项通过。当前v2部署包首次启动实测含依赖安装约38.1秒，再次启动约1.5秒并跳过pip安装，仅代表本机这次环境，不当作用户任务响应时间。Windows真机、真实浏览器视觉与非开发成员试用仍待完成。
