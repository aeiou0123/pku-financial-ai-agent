# 当前复赛三稿与Review

2026-10-03：信息表Word 3页、项目说明PDF 6页、展示稿PPTX 9页已重新导出并逐页检查，统一使用本日运行案例、开发指标与v4部署证据。PDF保留5个主要书签与2个子书签，PPTX含7个可编辑原生表格。Review补齐展示稿扭矩密度单位，未把开发集命中率当真实业务准确率。

信息表保留官方7张表、原字段、声明及签名位置。五段保守字符计数155/115/284/342/253，总计1149，分别在300/200/800/700/500范围内。队名、成员、联系人、签名和日期仍需负责人补齐，Word原生字数尚需复核。

三稿使用212项软件回归、87/98既有开发扰动（19家族）、10/10修复用边界探针以及实际部署43.237/0.708秒。公司情景与来源、工况及历史版本限制一致。详细指纹和验证边界见evidence/materials_review_20261003.json。没有原生PowerPoint、Windows真机或真人试用验收。

准备包提供01—03、05证据及06部署；按正式文件名运行预检，实际仍缺04运行视频与07技术题三件套。证据见evidence/material_gaps_20261003.json；此包不能作为完整最终参赛提交。

## 当前构建路径

文档由scripts/build_semifinal_materials.py使用materials_content.json中的明确证据路径生成，须提供官方DOCX模板与中文TrueType字体，输出目录必须不存在。PPTX由scripts/build_semifinal_slides.mjs在Codex演示稿运行时生成，输出work/materials_final_20261003/03_展示稿_复赛草稿.pptx；已存在时finalizer拒绝覆盖。该构建环境不是部署依赖，队员可直接编辑已交付PPTX。

旧v3材料与旧运行记录只用于历史追踪。当前原件、真实财务样本、独立标签、真人试用、真实录屏和真实技术题仍有缺口，后续更新不得沿用旧指纹或旧情景数字。

## 10月2日历史记录

# 复赛材料草稿与Review

2026-10-02：已生成信息表Word草稿3页、项目说明PDF草稿6页、展示稿PPTX草稿9页。可编辑稿与准备ZIP保存在共享推进目录；它们还不是可直接上传赛事的最终材料。

## 内容与证据

文字源为`materials_content.json`。信息表保留官方附件一字段、表序、声明与签名位置；五段保守字符计数为155/100/284/320/224，总计1083，负责人仍须用Word复核限字、补队名、成员、联系人、签名及日期。

PDF覆盖附件二五方面，并有5个主要书签及2个子书签。展示稿使用7个可编辑表格。三稿采用相同指标口径：本地规则87/98是19个声明家族的开发库复测，10条人为边界题6/10含修复用题；不是独立样本外准确率。19条原始参考的3次告警未重审真值，不称误报率。EV来自固定公司情景，不是股价、收益或已识别因果效应。

逐页检查Word3页、PDF6页和展示稿9页的导出图，未见截字或重叠；PDF书签与PPTX结构、字体策略和一方导入检查通过。未在原生PowerPoint或Windows真机验收，不宣称原生字体渲染已验证。详细文件指纹和检查边界在`evidence/materials_review_20261002.json`。

## 构建

文档构建依赖python-docx、ReportLab、原始官方DOCX模板和中文TrueType字体；仓库不公开复制赛事原件。已安装依赖的Python环境中运行：

```bash
python scripts/build_semifinal_materials.py --information-template /path/附件一.docx --font /path/中文字体.ttc --out /path/新的输出目录
```

PPTX构建脚本为`scripts/build_semifinal_slides.mjs`，依赖Codex演示文稿运行时的`@oai/artifact-tool`和finalizePresentation工具，不是应用启动依赖。在该运行时设置`PROJECT_ROOT`为仓库绝对路径，设置`RUNTIME_NODE`、`RUNTIME_NODE_MODULES`、`RUNTIME_BIN_DIR`、`RUNTIME_PYTHON`；将脚本放到可解析该模块的构建目录执行。产物为`work/slide_output/03_展示稿_复赛草稿.pptx`，输出文件已存在时finalizer拒绝覆盖。队员可直接修改交付PPTX，无需装此构建环境。

本地规则评测可用普通应用环境复跑：

```bash
python scripts/evaluate_local_review.py --out /path/新的评测目录
```

计时只覆盖本地暖启动函数，不包括浏览器、网络、首次启动或大模型。代码与数据指纹记录在results.json；失败案例必须随材料保留。

## 剩余工作

- 西交：Qwen/Kimi定位GH_007、BK_003、SH_002、BK_001的公开原件、页码、原文和未找到状态；不得把模型回答当原件。
- 上交：CSMAR先单公司一年三表、字典与公告日，验证授权和字段复算后扩三公司；商业原始导出保存在受控共享位置。
- 能下载赛事数据的成员：按`competition/README.md`跑真实训练开发折，冻结方法后用2020保留期，再生成最终技术题三件套。当前无真实Sharpe、排名或正式持仓。
- 非开发成员：Windows启动、典型用户路径、独立自然声明标签与失败反馈；然后录真实视频、统一三稿事实和正式文件名。

准备ZIP保留“草稿”文件名，缺真实视频、技术题三件套及身份签名。不得将其当最终参赛压缩包上传。

