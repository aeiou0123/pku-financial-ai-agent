# Claim2Value 数据目录说明

## 目录结构

```
data/
├── README.md                          # 本文件
├── collection_checklist.md            # 数据收集总清单
├── search_guide.md                    # 搜索方案与要领
├── raw/                               # 原始资料（PDF/网页/图片）
│   ├── company_filings/              # 公司公告、年报、招股书
│   ├── datasheets/                   # 产品 datasheet、手册
│   ├── patents/                      # 专利文本/PDF
│   ├── analyst_reports/              # 券商研报
│   ├── industry_reports/             # 行业报告
│   └── competitor/                   # 竞争对手资料
├── processed/                         # 结构化数据
│   ├── claim_bank.json               # claim 集合
│   ├── parameter_table.csv           # 技术参数对比表
│   ├── bom_template.csv              # BOM 模板
│   ├── tech_to_economics_ontology.json # 技术→经济映射规则
│   └── financial_model_inputs.csv    # 财务模型输入
└── benchmark/                         # 测试基准
    ├── claim_verification.json
    ├── engineering_accuracy.json
    ├── economic_reasoning.json
    └── financial_accuracy.json
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

## 数据收集状态

| 类别 | 目标数量 | 当前数量 | 负责人 |
|---|---|---|---|
| 年报/公告 | 5 | 0 | 西交经济金融 |
| datasheet | 4 | 0 | 机械成员 |
| 专利 | 5 | 0 | 电气成员 |
| 竞争对手参数 | 6 | 0 | 机械+电气 |
| 研报 | 5 | 0 | 西交经济金融 |
| 行业报告 | 2 | 0 | 西交经济金融 |

更新这个表格，让大家知道进度。
