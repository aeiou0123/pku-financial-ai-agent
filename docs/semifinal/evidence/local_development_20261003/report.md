# 本地核查模式开发评测

此结果是既有开发库复测与人工构造边界探针，不是样本外业务准确率。98条扰动来自19条原声明家族；原件与标签未在本轮重新认证。

扰动题严格标签命中：87/98（88.8%）；按19个家族等权平均：89.5%。
总是拒答诊断基线：19/98。不能据此证明优于商业大模型。

| 类别 | 命中/样本 | 比例 |
|---|---:|---:|
| evidence_absence | 19/19 | 100.0% |
| qualifier_removal | 18/19 | 94.7% |
| source_downgrade | 17/17 | 100.0% |
| temporal_shift | 8/10 | 80.0% |
| unit_swap | 11/17 | 64.7% |
| value_tampering | 14/16 | 87.5% |

19条未扰动原始参考中，3条触发提示；未重审原件和自然标签，因此不把它叫误报率。
10条人工边界探针命中10/10，其中包括用于修复的同义术语；不是独立验证。

每题重复5次；98个题目中位耗时的p50=0.051ms，p95=0.115ms。暖启动本地函数，外部API调用0次、API费用0；算力费用未计量，不代表在线全流程成本。

## 失败记录

- GH_001_QUAL_3：期望partially_supported，实际abstain。
- GH_006_UNIT：期望definition_mismatch，实际abstain。
- GH_006_UNIT_2：期望definition_mismatch，实际abstain。
- BK_001_VALU：期望refuted，实际abstain。
- BK_005_VALU：期望refuted，实际abstain。
- BK_005_UNIT：期望definition_mismatch，实际abstain。
- BK_005_UNIT_2：期望definition_mismatch，实际abstain。
- SH_003_TEMP：期望refuted，实际abstain。
- SH_005_UNIT：期望definition_mismatch，实际abstain。
- SH_005_TEMP：期望refuted，实际abstain。
- IND_001_UNIT_2：期望definition_mismatch，实际abstain。

详见results.json（所有输入输出、环境、数据/代码指纹）与failures.json。正面支持不在本地规则模式能力内；未发现问题会保守拒答。下一轮应收集独立原文，预先冻结标签，按原始来源/时间分组留出测试，不能把同一原声明的扰动分到训练和测试两边。