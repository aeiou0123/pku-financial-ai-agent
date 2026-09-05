# Claim2Value 数据目录说明

## 目录结构

```
data/
├── README.md                          # 本文件
├── collection_checklist.md            # 数据收集总清单
├── search_guide.md                    # 搜索方案与要领
├── raw/                               # 原始资料（PDF/网页/图片）
│   ├── company_filings/              # 公司公告、年报、招股书（当前已有）
│   └── analyst_reports/              # 券商研报/行业研报（当前已有）
├── processed/                         # 结构化数据
│   ├── claim_bank_filled.json        # 当前结构化 claim 集合
│   ├── parameter_table_filled.csv    # 当前技术参数对比表
│   ├── patent_collection.csv/json    # 专利结构化记录
│   ├── industry_data_summary.csv     # 行业数据
│   ├── competitor_market_share.csv   # 竞争格局数据
│   ├── buke_fmk_parameters.csv       # 步科 FMK 参数
│   ├── bom_template.csv              # BOM 模板
│   ├── financial_model_inputs_template.csv # 财务模型输入模板
│   ├── green_harmonic_model_inputs.csv     # 带来源/类型标签的模型输入
│   ├── green_harmonic_model.xlsx            # 三情景 Excel 输出
│   ├── green_harmonic_model_results.json    # 三情景机器可读输出
│   ├── local_demo_fixture.json              # 本地 Demo evidence fixture
│   └── local_demo_result.json               # 本地 Demo 运行结果
└── ../benchmarks/                    # 仓库根目录下的测试基准
    ├── claim_verification_v2.json
    ├── pipeline_report.md
    └── results/
```

## 重要原则

1. **所有 PDF 文件名用英文或拼音，不要空格**，例如：
   - `green_harmonic_2024_annual_report.pdf`
   - `green_harmonic_csd_25_specsheet.pdf`
   - ` harmonic_drive_csf_20_datasheet.pdf`

2. **每个原始文件对应一个 `.meta.json`**，记录来源、日期、URL、收集人，例如：
   - `green_harmonic_2024_annual_report.pdf.meta.json`

3. **优先收集可验证的公开资料**，避免依赖需要付费账号才能查看的内容。

4. **不要上传 API key、账号密码、内部未公开资料**。

## 当前数据状态（2026-09-05）

| 类别 | 当前数量/状态 | 说明 |
|---|---:|---|
| 公司年报/半年报/招股书 | 7 份 PDF | 绿的谐波、步科、双环传动、环动科技 |
| 券商/行业研报 | 11 份 PDF | 均有对应 `.meta.json` |
| 官方 datasheet | 0 份 | 仍以研报参数、年报描述和公开网页为替代 |
| 专利结构化记录 | 30 条 | 绿的 7、环动 15、步科 8；步科发明专利仍待核验 |
| 产品参数记录 | 14 条 | 部分字段仍为“待补充” |
| 行业数据 | 13 条 | 工业机器人、减速器需求、国产化率等 |
| 竞争格局数据 | 8 条 | 谐波/RV 减速器市占率 |
| Claim | 19 条 | 5 条已验证、14 条待验证 |
| Claim evidence_list | 0 条 | 当前验证引擎接收运行时 evidence，Claim Bank 尚未回填账本 |
| 财务模型输入 | 1 个正式 CSV | `green_harmonic_model_inputs.csv` 已区分历史锚点与人工假设；模型结果不写回输入 |
| 本地 Demo fixture | 1 个 | 绿的谐波 GH_001 的限定词缺失案例；页码仍待人工核验 |

当前阶段：资料收集已足以支撑绿的谐波单案例财务模型和 Demo 原型；datasheet、专利核验和重大事项公告属于证据增强任务，不阻塞首版 Demo。

注意：`claim_bank_filled.json` 与 `claim_bank_template.json` 当前仍相同，`parameter_table_filled.csv` 与 `parameter_table_template.csv` 当前仍相同；后续应在形成经过人工核验的正式数据后再分离模板与 filled 文件。

财务模型输入中的情景销量、ASP、成本、费用率、税率和 DCF 参数均是原型假设，不能当作公司披露或管理层指导。详见 `TODO.md` 的验收标准。
