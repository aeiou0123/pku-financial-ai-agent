# 给西交成员本地agent的任务

暂不处理CSMAR/CEIC。为Claim2Value复赛补充公开原文与工程证据。仓库https://github.com/aeiou0123/pku-financial-ai-agent ，先读docs/semifinal/team_execution.md、data_download_guide.md、data/raw与已有meta.json、claim_bank_filled.json，避免重复下载。代码/索引走独立分支，授权原件存本人指定目录。

1. 先为绿的谐波688017、双环传动002472及环动科技、步科股份688160建立缺件清单。按公司/股票代码在巨潮、交易所和公司官网找2025年报、2026半年报，以及2023年至2026-10-02相关募投/扩产/投资者关系/招股书。保留原PDF，记录标题、公告日、URL和SHA-256。
2. 定位产量、销量、产能利用率、分部收入毛利、研发、税收优惠、客户认证/订单等原文。每条写PDF文件页、印刷页、逐字摘录、统计期间、单位、限定词；抽取表格时保留原页以便核列。
3. 查四条急件：GH_007官方LHS-32手册；BK_003第四代与上一代同尺寸FMK参数/官方22%出处；SH_002的SHPR-20E与RV-20E官方规格原表；BK_001引用的2024协作机器人蓝皮书可用原文。找不到标未找到，不能以更多转载替代一手证据。
4. 如果得到上交专利索引，按准确申请/公开号补相关官方全文和法律状态；否则先明确母子公司法律主体再小范围检索。登录/验证码由本人处理，不绕过。不凭专利授权推断量产/性能/毛利。
5. 从未用于既有规则开发的原文选10—15个候选真实Claim（目标数，未完成不能当已完成），覆盖性能/产能/客户类。输出真实原文和出处，不自动编“标准答案”，供人工审标与来源分组评测。

交付：source_manifest.csv、evidence_candidates.csv（claim_id/company/claim_text/source_url/published_at/pdf_page/printed_page/excerpt/unit/period/qualifiers/verification_question）、原件、四条补件状态表。只记录真正下载/检查过的内容。

优先官网原PDF。允许人工下载替代复杂爬虫；下载失败时记录链接与原因。付费蓝皮书只能使用合法已获授权或公开原发布部分；不足就保留缺件。不要向公开GitHub提交不允许再分发的原文或任何账户数据。
