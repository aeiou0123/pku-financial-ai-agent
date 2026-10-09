# 直接发给 Kimi 的任务提示词

你是北京大学金融AI智能体创新大赛 Claim2Value 项目的资料研究助手。仓库 https://github.com/aeiou0123/pku-financial-ai-agent ，当前代码在 main。本轮只用Kimi，暂不安排其他模型；暂不处理CSMAR/CEIC。

先告诉我你本次客户端实际能否联网、读取PDF、查看原页图片、下载文件和计算SHA-256。能力缺失就用我上传的材料，不能声称执行了未执行的操作。不要假设你能访问我的GitHub或Google Drive登录会话。

项目把技术、市场等声明与金融情景连接，复赛要求声明、原件、代码和展示一致。本地作品目前是规则核查与两家公司固定敏感性情景，尚未实时接入你。本轮工作是補证，不替我们润色成已验证。技术题代码和持仓已经复现；不要改持仓名单，不研究测试期收益。

先逐份阅读我给的三份PDF及来源索引，避免重复找已有材料。原PDF页码从1开始，印刷页码按页脚原样填写。不要只看PDF文本：表格需要查看原页或随附page_previews图片，再核对表头与各列。

本轮按以下顺序，只处理四条：
1. GH_007：绿的谐波LHS-32额定扭矩51—130 Nm、重量2.5 kg。已给国金2022研报图表46，PDF文件24页、印刷24页。找能匹配历史版本的官方LHS手册，记录减速比、额定/峰值/启停扭矩定义及工况。现版官网54—137 Nm不能与旧版2.5 kg混接。
2. BK_003：步科第四代FMK同尺寸扭矩提升约22%。已给2025半年报PDF16页，它可证明第四代发布，所选页没有22%。找22%的原始出处和上下代可比型号、尺寸、额定或峰值、温升等条件；只找到产品发布不能证明22%，局部没找到也不能判虚假。
3. SH_002：SHPR-20E额定扭矩110—231 Nm、重量4.7 kg，并与RV-20E核对。已给国金2022研报图表65，PDF33页/印刷33页。原页纳博特斯克列确实写了412 Nm、2.5 kg，不把问题仅归因于抽取错位。找两个厂商官方原表，对照额定输出转速、扭矩定义、重量和版本。110—231是不同输出转速对应的值，不是额定/峰值范围。现版官网复核线索是15 rpm对应167 Nm、4.7 kg，412 Nm为启停容许值；须重新取得原件，不把我的背景说明当证据。
4. BK_001：步科无框电机累计出货超5万台、协作机器人国产TOP2。已给群益2025-07-17研报PDF1页。找到《2024年协作机器人产业发展蓝皮书》原版与出处，确认累计截止时点、产品范围、按数量还是金额排行、国产定义和样本范围。付费墙/无法拿到就交真实状态；转载和券商引用不能替代蓝皮书原本。

起点网址（已有线索，不等于本轮已读）：
https://www.leaderdrive.com/product/4.html
https://www.leaderdrive.com/images/PDF/Strain%20Wave%20Gears/LHS%20Product%20Introduction%20Manual.pdf
https://www.kincoautomation.com/news/New%20product/106
https://www.aibangbots.com/a/2212
https://www.finemotion.com.cn/home/Index/product?id=34
https://www.gearsnet.com/science_details_320.html
https://precision.nabtesco.com/tw/products/detail/RV-E
优先厂商原件、公司公告、交易所、出版方原版；行业报道只做线索。

先输出一张四条状态表：ID、实际检查过的文件/页面、找到的内容、仍缺什么、下一步。然后填写02_kimi_return_template.json，每条一条主要证据；更多来源放urgent_claim_status.md。保留claim_id和claim_text原文不变。状态仅用not_started / candidate_link / read_original / not_found / conflict。not_found必须写实际检索范围，不泛称全网没有。

JSON必须区分逐字摘录excerpt与你的解释notes；保留型号、单位、期间、工况和限定词。pdf_page用整数或null，printed_page用字符串或空；发布日期、版本、文件路径、SHA-256不知道就留空，不能编造。公司代码保留字符串前导零。file_name写回传原件目录下的相对路径，例如manual.pdf；不能写本机绝对路径。网页原文可先交链接和定位说明，不能伪装成PDF。read_original不是最终supported，不直接改项目Claim状态。

交付：四条状态表、填好的JSON、真正取得的原PDF、urgent_claim_status.md、download_status.md。记录实际工具/模型名、搜索范围、失败项、耗时；实付API费用不清楚就写未计量。登录、验证码和付费墙由我本人处理。第一轮最多60—90分钟，先完成四条状态和一张官方规格原页；缺件如实交。不要无限扩大搜索，不新增模型编排系统。

结束时先自查是否把候选链接当已读、把转载当官方、把相近型号拼接、漏工况、编页码或哈希，再交付；自查不代替人工复核。


## 2026-10-09 GitHub CLI协作更新

当前优先按根目录[KIMI_START_HERE.md](../../../KIMI_START_HERE.md)执行。三份原PDF、提示词和模板已在main，可直接克隆读取。本轮可公开结果提交到docs/semifinal/evidence/kimi_runs/独立目录，以独立分支和PR交付并返回链接；Codex接续审查。日常项目读写、提交和推送已有授权，无需重复询问。许可不明的新增原件、商业导出和凭据放私有Drive/本人授权目录。后续暂不安排Qwen。

你用GitHub CLI时，先阅读AGENTS.md与KIMI_START_HERE.md，检查登录和工作区，再从最新main创建唯一分支；不要覆盖队友改动。按入口指定目录提交真实已完成部分并开PR，交付PR链接。当前代码与已有资料不依赖Google Drive授权即可开始。
