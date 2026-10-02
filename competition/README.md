# 统一技术题：本地可复现基线

与Claim2Value作品估值模块独立。依据Drive中的FEL-MARKET-2026-LOCAL-v1.2.1说明实现。本轮完成代码、合成数据集成检查和防泄漏回归，尚未完成真实训练、真实测试名单或真实验证Sharpe。

## 数据与环境

将赛事原文件放在仓库外同一目录，例如 Windows `C:\FEL_MARKET`：train.parquet、test.parquet、tools.py。代码核验三个文件的官方SHA-256，且调用原tools.py的validate_data、backtest、check；不在公开仓库重发赛事原数据或工具。

Python 3.12或3.13；建议独立环境：

```bash
python -m venv .venv-competition
# Windows环境中的python为 .venv-competition\Scripts\python.exe
# Linux环境中的python为 .venv-competition/bin/python
python -m pip install -r competition/requirements.txt
```

上面最后一条的python必须换成新环境中的解释器，或先激活环境。命令下文省写为python；在仓库根目录执行，路径含空格时加引号。numpy/pandas/pyarrow直接依赖按赛事验证版本固定；本轮模拟集成实际运行环境Python3.12.14，未冒称Python3.13.2实测。

## 模型与组合

每日对当日400家公司的100因子做截面中位秩变换，固定映射为中心化尺度；并列值用平均秩。没有在完整测试期拟合标准化、特征筛选或统计量。匿名因子恒定于同日时该列变成零。

训练标签为同一行收益，按当日截面去均值，训练Ridge预测相对收益，不向后移标签。累计X'X、X'y后求解均方损失+alpha正则；无随机优化，seed=0仅记录确定性设置。

每日按预测收益加持有奖励hold_bonus选20家，排序并列按股票编号；只使用此前名单与当日因子。hold_bonus是降低换手的启发式参数，单位是日收益率，不是对实际成交费用的精确估计。真正计分使用官方扣费记账，包含恢复等权、首次买入、期末清仓和全期连续NAV。

## 三个命令

先在公共训练数据内完成开发验证。示例路径为Windows；其他系统换实际目录。

```bash
python -m competition.baseline validate --tools C:\FEL_MARKET\tools.py --train C:\FEL_MARKET\train.parquet --train-end 2015-12-31 --valid-start 2016-01-01 --valid-end 2017-12-31 --alpha 0.001 --hold-bonus 0 --out competition/runs/dev_a001_b0
```

生成model.json、validation.csv、官方accounting.json、固定前20家公司对照名单fixed20_validation.csv和run_summary.json。摘要同时给出策略与固定名单在相同区间、相同费用口径下的Sharpe。输出目录须不存在；未产生run_summary.json的目录视为未完成，不凭已有CSV报告成功。实际耗时从开始校验数据计算；不覆盖已有结果。

预先约定小网格：alpha={0.00001,0.001,0.1}，hold_bonus={0,0.0004,0.0008}，共9组。可先试一组再批量。开发折A训练2000—2015、验证2016—2017；折B训练2000—2017、验证2018—2019。按两折扣费Sharpe、结果稳定性与换手记录选择，不能只看最好一段。另比较固定20公司和不加持有奖励的简单基线。

锁定方案后，只做一次2020保留期评估：训练截止2019-12-31，验证2020-01-01至2020-12-31。看过2020结果后若调整方案，2020必须改标开发集；不能继续叫未触碰样本外。各折官方账户独立从1开始并清仓；折间Sharpe用于诊断，不能宣称等同跨折连续账户Sharpe。

方案与超参数锁定后全量公共训练：

```bash
python -m competition.baseline fit --tools C:\FEL_MARKET\tools.py --train C:\FEL_MARKET\train.parquet --train-end 2020-12-31 --alpha 0.001 --out competition/runs/final_model
python -m competition.baseline predict --tools C:\FEL_MARKET\tools.py --test C:\FEL_MARKET\test.parquet --model competition/runs/final_model/model.json --hold-bonus 0 --out competition/runs/test_predictions
```

这里alpha/hold_bonus为演示值，必须换成开发折选定并冻结的值，不代表已找到最优组合。predict逐日生成submission.csv并调用官方check；失败不得标完整提交。run_summary.json的test_sharpe始终null，因为测试收益不公开。

再到另一个新目录重复predict，比较CSV的SHA-256。复现包保留实际模型JSON、代码、依赖、冻结参数、种子和所用AI工具。最终07_技术题还须有code.zip与20页以内技术题报告.pptx；本轮没有生成最终三件套，也没有向赛事平台提交。

## Review与复跑

```bash
python -m pytest tests/test_competition_baseline.py -q
python -m competition.smoke --tools C:\FEL_MARKET\tools.py --out competition/runs/synthetic_smoke
```

smoke用确定性模拟数据，真实官方工具验收CSV解析、初始买费、期末清仓费、固定名单恢复等权的费用与连续净值。只保存通过/失败检查，不将模拟Sharpe包装成比赛成绩。源码允许按月读取因子以控制内存，但变换和选股只消费当前一天；未来因子扰动回归检查此前持仓不变。预测读取列不包含return。

## 当前数据落地限制

Drive训练文件622965149字节，大于连接器268435456字节上限，返回413。测试文件144652201字节虽返回下载引用，但当前工作环境两次落地下载返回403，未取得可校验文件。只能确认Drive元数据和官方说明，不能宣称已核验真实Parquet内容。最直接做法是在本机从已授权Drive下载，然后按上述命令执行；回传run_summary.json、model.json和必要的验证记录，无需把大数据上传公开GitHub。

复杂模型、因子筛选、滚动重训等后置，先获得真实基线再判断增量。当前代码只是一个可测量起点，不保证技术题加分或收益。
