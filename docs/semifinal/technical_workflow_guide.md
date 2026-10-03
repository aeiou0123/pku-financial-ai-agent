# 技术题：三阶段执行与回传

更新：2026-10-03。新流程已通过合成数据与真实官方记账工具的集成检查，以及失败路径回归；尚未在真实赛事数据上训练。执行包不是正式的 `07_技术题/code.zip`，也没有真实持仓、模型成绩或报告PPT。

## 西交可以直接承担这一条线

统一技术题使用赛事提供的匿名数据，不需要CSMAR或CEIC，也不需要在预测中调用Qwen/Kimi。西交可先负责本地运行与记录；Qwen/Kimi可协助检查代码和分析开发结果，记录实际工具及版本，不能据2020结果反复改参数后仍称其为未触碰留出集。上交继续负责授权财务导出与字典；西交的公开原件补证任务也继续保留。本文没有替你们给队员发送任务。

## 先下载一次

1. 从你们已有Drive的技术题 development/FEL_MARKET 下载原始 `train.parquet`、`tools.py`；从 test/FEL_MARKET 下载 `test.parquet`。
2. 三份放在仓库/执行包之外同一目录，例如 `C:\FEL_MARKET`。保持原文件，不转换或重新保存Parquet。程序核验官方SHA-256、数据结构及split。执行包已附与官方指纹一致的tools.py，也可原样复制到数据目录。
3. 解压执行包，安装Python3.12或3.13。在解压后的根目录打开终端。第一次运行会建立独立环境并安装固定依赖，需要网络；首次依赖安装时间与后续建模时间分开理解。

最新云端状态：测试文件已在重试后成功下载，官方SHA-256、schema和1212日历通过核验；此前403已解除。训练文件622965149字节仍超出268435456字节单文件下载上限。若希望由云端训练，只需按[分段传输指南](cloud_data_transfer_guide.md)把原始train.parquet分成3个不超过200MiB的字节段，连同manifest上传已共享Drive；云端拼回并核验后即可继续。下面的本机完整运行方案仍可直接使用。大数据保留私人Drive/本机，不需校园账号。

## 按顺序执行

以下Windows示例在根目录执行；路径有空格也使用引号。Linux/macOS同样可用python3运行脚本，替换实际路径；也可使用start_technical.sh。Windows可用start_technical.bat传递同样参数。

### 1. 开发比较，并自动锁定

```powershell
python scripts/launch_technical.py develop --data "C:\FEL_MARKET" --out "C:\Claim2Value_runs\experiment_01"
```

输出目录第一次必须不存在。共9组预定参数、两折：训练至2015/验证2016—2017，训练至2017/验证2018—2019。每折每个alpha只训练一次，共6次模型拟合，复用模型比较3个持有奖励，生成18条策略记录与2条固定20公司对照。

选择规则在任何结果产生前写入plan.json：先最大化两折扣费Sharpe中较低值，再比较两折均值，再选择较小持有奖励和较小alpha。不是取单个最好年份，也不把两个独立账户的Sharpe称为连续全期Sharpe。交易费用调用原tools.py，另记录名单替换比例；绝对NAV单位费用总和不是换手率。

生成selection_lock.json，绑定全部模型、名单、官方账户、控制记录及代码指纹。若任一开发折不可评分，不自动锁定。请先把selection_lock.json、plan.json以及development/controls中的receipt.json/result.json回传Drive；无需先等整份报告。

完成边界之间中断，可在同一版本/环境使用：

```powershell
python scripts/launch_technical.py develop --data "C:\FEL_MARKET" --out "C:\Claim2Value_runs\experiment_01" --resume
```

仅复用完整、有指纹记录的边界；模型、名单或账户被改动即拒绝。中途留下没有receipt.json的目录不会被覆盖或猜作成功：保留失败记录，另建开发实验目录重跑。更改代码/依赖/运行环境也不能在原目录冒充同一次实验。

### 2. 只做一次2020留出验证

```powershell
python scripts/launch_technical.py holdout --data "C:\FEL_MARKET" --out "C:\Claim2Value_runs\experiment_01"
```

只用已锁定参数，训练至2019、验证2020，比较固定20家公司。holdout_started.json在读取2020数据之前创建；即使中断，这个实验目录的留出机会也被标为已使用，不支持静默重跑。成功生成holdout_summary.json，不会按2020结果重新选参数。

这是单个实验目录的程序约束，不能防止人手删文件、另建目录或修改代码。任何成员看过2020结果之后若改方法，就必须把2020改标开发数据并如实披露，不能靠换目录恢复“未触碰样本外”。不要把技术题报告写成已进行更多样本外验证。

### 3. 全量训练、两次预测与封装

```powershell
python scripts/launch_technical.py finalize --data "C:\FEL_MARKET" --out "C:\Claim2Value_runs\experiment_01" --ai-tools "填写实际使用的工具、模型和版本"
```

成功后 `experiment_01/final/` 生成真实submission.csv、code.zip和receipt.json。流程先核对开发锁与留出证据，再训练至2020；顺序预测2021—2025两次，调用官方check并要求名单指纹一致，再封装实际生成代码、模型、官方工具及复现命令。任何一步失败都不会留下“完整交付”receipt.json。测试收益不公开，test_sharpe始终null。若预测中断，保留记录，人工复核后按baseline的独立命令在新目录复跑；本流程不会自动覆盖final/。

把final/两份正式文件与技术题报告.pptx（不超过20页）放到总提交包的07_技术题。新流程不会编造报告结果，也不会替你们上传赛事平台。

## 没有大数据时也能自检

```powershell
python scripts/launch_technical.py smoke --data "C:\FEL_MARKET" --out "C:\Claim2Value_runs\synthetic_check_01"
```

此项仅需官方tools.py。5200条确定性模拟记录驱动三阶段中的开发/留出流程，调用真实CSV解析和扣费账户；不使用真实Parquet、不产出正式测试名单、不报告模拟Sharpe。模拟模型显式使用synthetic指纹，不冒充真实数据来源。首次自检和正式开发使用不同目录。

## 需要回传什么

| 阶段 | 最小回传 | 助手接下来能做什么 |
|---|---|---|
| 开发 | plan.json、selection_lock.json、models/development/controls完整记录 | 复核分割、参数选择、实际费用、失败与基线差异 |
| 留出 | holdout_started.json、holdout_summary.json、2020对应模型/账户/receipt | 对照冻结方案复核留出结果，撰写有证据的报告 |
| 最终 | final/submission.csv、code.zip、receipt.json、prediction/reproduction运行摘要 | 重新检验结构和复现证据，整理技术题报告与总包 |

优先传私人Drive；公共GitHub保留代码、脱敏研究说明和必要的小型证据。真实数据训练耗时、内存、Windows启动及跨系统复现目前未测；模拟耗时只说明自检执行时间，不能外推到真实数据。
