# Claim2Value 数据搜索报告

> 搜索时间：2026-09-01
> 搜索人：Claude Code
> 说明：本报告如实记录搜索过程中找到和未找到的资料。

---

## 一、已下载资料清单

### 1.1 公司年报/半年报

| 公司 | 文件 | 大小 | 页数 | 来源 | 状态 |
|---|---|---|---|---|---|
| 绿的谐波 | 2024年年度报告 | 1.8MB | - | 巨潮资讯网 static.cninfo.com.cn | ✅ 已下载 |
| 绿的谐波 | 2025年年度报告 | 1.7MB | 233页 | 巨潮资讯网 static.cninfo.com.cn | ✅ 已下载 |
| 步科股份 | 2024年年度报告 | 2.5MB | 268页 | 新浪财经文件服务器 | ✅ 已下载 |
| 步科股份 | 2025年半年度报告 | 1.6MB | 207页 | 新浪财经文件服务器 | ✅ 已下载 |
| 双环传动 | 2024年年度报告 | 4.9MB | 179页 | 新浪财经文件服务器 | ✅ 已下载 |
| 双环传动 | 2025年半年度报告 | 824KB | 128页 | 新浪财经文件服务器 | ✅ 已下载 |
| 环动科技 | 首次公开发行股票招股说明书（申报稿） | 5.7MB | 343页 | 上海证券交易所 | ✅ 已下载 |

**说明**：上交所/深交所直链有反爬机制，直接下载返回 JavaScript 验证页面。通过新浪财经文件服务器成功获取 PDF。

### 1.2 券商研报

| 文件 | 公司 | 大小 | 页数 | 来源 | 状态 |
|---|---|---|---|---|---|
| green_harmonic_2025q1_review.pdf | 绿的谐波 | 509KB | 7页 | 东方财富 pdf.dfcfw.com | ✅ 已下载 |
| green_harmonic_2025q1_review_2.pdf | 绿的谐波 | 519KB | 3页 | 东方财富 pdf.dfcfw.com | ✅ 已下载 |
| green_harmonic_2024_2025q1_review.pdf | 绿的谐波 | 615KB | 3页 | 东方财富 pdf.dfcfw.com | ✅ 已下载 |
| green_harmonic_2025_halfyear_review.pdf | 绿的谐波 | 619KB | 3页 | 东方财富 pdf.dfcfw.com | ✅ 已下载 |
| precision_reducer_research_202401.pdf | 行业/绿的谐波/双环传动 | 1.1MB | 14页 | 东方财富 pdf.dfcfw.com | ✅ 已下载 |
| humanoid_robot_joint_reducer_202209.pdf | 行业 | 5.0MB | 18页 | 东方财富 pdf.dfcfw.com | ✅ 已下载 |
| buke_2025q2_review.pdf | 步科股份 | 518KB | 4页 | 东方财富 pdf.dfcfw.com | ✅ 已下载 |
| buke_2025q3_review.pdf | 步科股份 | 458KB | 3页 | 东方财富 pdf.dfcfw.com | ✅ 已下载 |
| shuanghuan_2025_0122.pdf | 双环传动 | 782KB | 3页 | 东方财富 pdf.dfcfw.com | ✅ 已下载 |
| shuanghuan_2025_0515.pdf | 双环传动 | 652KB | 7页 | 东方财富 pdf.dfcfw.com | ✅ 已下载 |
| shuanghuan_2025q2_review.pdf | 双环传动 | 721KB | 3页 | 东方财富 pdf.dfcfw.com | ✅ 已下载 |

### 1.3 产品参数

| 文件 | 内容 | 来源 | 状态 |
|---|---|---|---|
| data/processed/buke_fmk_parameters.csv | 步科股份 FMK 系列 10 个型号参数 | WebSearch 公开资料 | ✅ 已整理 |
| data/processed/parameter_table_template.csv | 三家公司参数对比模板 | 待填写 | ⏳ 模板 |

---

## 二、未找到/无法获取的资料

### 2.1 官方产品 datasheet

| 公司 | 原因 |
|---|---|
| 绿的谐波 | 官网未搜索到公开 PDF 选型手册； torque density 参数多见于行业分析文章 |
| 步科股份 | 官网有 FMK 系列页面和资料下载中心，但 API 返回 HTML，无法批量获取 PDF 直链 |
| 双环传动 | 环动科技官网未找到公开 RV 减速器 datasheet；180 N·m/kg 参数主要来自雪球等第三方分析 |

**应对**：使用研报中的参数对比表、年报中的产品描述、以及已搜索到的 FMK 参数表格。

### 2.2 核心专利

| 公司 | 原因 |
|---|---|
| 绿的谐波 | Google Patents 无法通过 curl/WebFetch 访问；CNIPA 需要浏览器交互 |
| 步科股份 | 同上 |
| 双环传动/环动科技 | 同上 |

**应对**：
- 环动科技招股书中包含专利清单，可从该 PDF 中提取
- 提供 Google Patents / CNIPA 搜索链接，由团队手动补充

### 2.3 更多行业报告

- 高工机器人、IIM 等行业报告多为付费或会员制，无法免费下载
- 部分 Wind/慧博投研报需要账号

**应对**：已下载的券商研报中包含大量行业数据，可作为替代。

---

## 三、关键财务数据摘要

### 3.1 绿的谐波（2024年报）

| 指标 | 数值 | 同比 |
|---|---|---|
| 营业收入 | 3.87亿元 | +8.77% |
| 归母净利润 | 5616.81万元 | -33.26% |
| 扣非归母净利润 | 4620.49万元 | -38.09% |
| 毛利率 | 37.54% | -3.60个百分点 |
| 基本每股收益 | 0.33元 | - |

### 3.2 步科股份（2024年报）

| 指标 | 数值 | 同比 |
|---|---|---|
| 营业收入 | 5.47亿元 | +8.09% |
| 归母净利润 | 4889.16万元 | -19.43% |
| 扣非归母净利润 | 3768.28万元 | -29.98% |
| 研发投入 | 7307.59万元 | +26.75% |
| 机器人行业收入 | 2.12亿元 | +12.26% |

### 3.3 双环传动（2024年报）

| 指标 | 数值 | 同比 |
|---|---|---|
| 营业收入 | 87.81亿元 | +8.76% |
| 归母净利润 | 10.24亿元 | +25.42% |
| 扣非归母净利润 | 10.01亿元 | +24.64% |
| 基本每股收益 | 1.22元 | +25.77% |
| 总资产 | 158.67亿元 | +20.46% |

### 3.4 双环传动（2025H1）

| 指标 | 数值 | 同比 |
|---|---|---|
| 营业收入 | 42.29亿元 | -2.16% |
| 归母净利润 | 5.77亿元 | +22.02% |
| 扣非归母净利润 | 5.55亿元 | +22.54% |
| 基本每股收益 | 0.68元 | +23.64% |
| 经营活动现金流净额 | 9.80亿元 | +20.92% |

---

## 四、搜索过程中的技术限制

1. **CNINFO 反爬**：巨潮资讯网 hisAnnouncement/query API 返回空，无法批量获取公告列表
2. **上交所/深交所直链反爬**：直接访问 PDF 链接返回 JavaScript challenge 页面
3. **Google Patents 访问受限**：curl/WebFetch 无法获取专利页面
4. **Wind/慧博付费研报**：无法访问

**绕过方法**：通过新浪财经文件服务器获取公告 PDF，通过东方财富 pdf.dfcfw.com 获取研报 PDF。

---

## 六、已完成替代方案（2026-09-01）

由于 PDF 中文字体编码问题，无法直接用 pdfplumber/PyMuPDF 提取环动科技招股书文字，因此采用以下替代路径：

### 6.1 专利数据

- 通过 WebSearch 整理三家公司核心专利：
  - 绿的谐波：7 项核心发明专利（含 P 型齿、Y 系列、密封轴承等）
  - 环动科技：15 项 RV/谐波减速器相关发明专利
  - 步科股份：8 项常州精纳无框/伺服电机实用新型专利（核心发明专利待核对）
- 输出文件：
  - [`data/processed/patent_collection.json`](data/processed/patent_collection.json)
  - [`data/processed/patent_collection.csv`](data/processed/patent_collection.csv)

### 6.2 产品参数

- 从国金证券《从人形机器人关节设计看待减速器投资机会》提取到：
  - 绿的谐波 LHS-32：额定扭矩 51–130 Nm，重量 2.5 kg
  - 双环传动 SHPR-20E：额定扭矩 110–231 Nm，重量 4.7 kg
  - 纳博特斯克 RV-20E：额定扭矩 412 Nm，重量 2.5 kg
- WebSearch 补充绿的谐波 LCS-20-100-C-I 与哈默纳科 CSF-20 对比参数
- 步科 FMK 系列 10 个型号参数已整理（缺重量/扭矩密度）
- 输出文件：
  - [`data/processed/parameter_table_filled.csv`](data/processed/parameter_table_filled.csv)
  - [`data/processed/parameter_table_template.csv`](data/processed/parameter_table_template.csv)

### 6.3 Claim 素材

- 自动扫描 18 份 txt 报告，生成 421 条候选 claim，人工筛选出 18 条：
  - 绿的谐波 7 条（技术性能 3、产能/需求 2、财务 2）
  - 步科股份 5 条（技术性能 1、产能/需求 1、客户 1、财务 2）
  - 双环传动/环动科技 5 条（技术性能 1、产能/需求 2、客户 1、财务 1）
  - 行业基准 1 条
- 输出文件：
  - [`data/processed/claim_bank_filled.json`](data/processed/claim_bank_filled.json)
  - [`data/processed/claim_bank_template.json`](data/processed/claim_bank_template.json)

### 6.4 行业与竞争数据

- 整理工业机器人销量、减速器需求量、国产化率、市占率等数据
- 输出文件：
  - [`data/processed/industry_data_summary.csv`](data/processed/industry_data_summary.csv)
  - [`data/processed/competitor_market_share.csv`](data/processed/competitor_market_share.csv)

## 七、仍建议手动补充的资料

1. **官方 datasheet**：绿的谐波 LCS/LHS/Y 系列、步科 FMK 完整选型手册、环动科技 RV 减速器样本
2. **步科核心发明专利**：目前公开检索以实用新型为主，需通过 CNIPA/Google Patents 或招股书核对发明专利
3. **重大事项公告**：绿的谐波定增/募投/股权激励、步科/双环客户合作公告
4. **财务模型输入**：基于年报数据填写 `data/processed/financial_model_inputs_template.csv`
5. **BOM 表**：基于研报和行业数据填写 `data/processed/bom_template.csv`

---

## 六、搜索链接汇总

### 专利搜索
- 绿的谐波： https://patents.google.com/?q=%22%E7%BB%BF%E7%9A%84%E8%B0%90%E6%B3%A2%22&language=CHINESE
- 步科股份： https://patents.google.com/?q=%22%E6%AD%A5%E7%A7%91%E8%82%A1%E4%BB%BD%22%20%E6%97%A0%E6%A1%86%E5%8A%9B%E7%9F%A9%E7%94%B5%E6%9C%BA&language=CHINESE
- 双环传动/环动科技： https://patents.google.com/?q=%22%E7%8E%AF%E5%8A%A8%E7%A7%91%E6%8A%80%22%20RV%E5%87%8F%E9%80%9F%E5%99%A8&language=CHINESE

### 公司公告
- 巨潮资讯网： http://www.cninfo.com.cn/new/index
- 新浪财经公告： https://vip.stock.finance.sina.com.cn/corp/view/vCB_AllBulletinDetail.php

### 研报
- 东方财富研报中心： https://data.eastmoney.com/report/stock.jshtml

---

## 七、数据来源声明

所有 PDF 均为上市公司法定披露文件或券商公开发布研报。未使用任何内部未公开信息。
