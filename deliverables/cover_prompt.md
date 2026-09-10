# Claim2Value 封面图提示词（给 ChatGPT image 2.5 / 其他图像模型）

> 用法：把下面任一段提示词贴给图像模型，生成 16:9 封面。生成后直接替换
> `deliverables/cover_16x9.png`（注意 BigQuant 要求 16:9、JPG/PNG、≤3MB）。
> 品牌色：藏青 #1E2761（主背景）、金 #F0B429（强调）、冰蓝 #CADCFC（辅助）。

## 变体 A：含标题文字（推荐，信息完整）

**中文版：**

```
一张 16:9 横版科技品牌封面图。深邃的藏蓝色背景（#1E2761），画面中央偏上是一条水平的
链条图形：三个圆形节点由细线连接，中间节点为金色（#F0B429），两侧为冰蓝色（#CADCFC），
象征"Claim→证据→价值"的传递链。链条下方居中是大号白色粗体无衬线标题文字
"Claim2Value"，其下是较小的冰蓝色副标题"工业技术 Claim 到金融价值的可信映射 Agent"。
底部有一条深色横带，内写小字"北大金融 AI 智能体创新大赛"。整体风格：扁平矢量、
极简、高端金融科技品牌感、大量留白、无渐变堆叠、无照片元素、无 3D 效果。
```

**English version：**

```
A 16:9 landscape tech brand cover. Deep navy background (#1E2761). Centered upper area:
a horizontal chain motif of three circular nodes connected by thin lines — the middle
node is gold (#F0B429), the two side nodes are ice blue (#CADCFC) — symbolizing a
"Claim → Evidence → Value" pipeline. Below the chain, a large bold white sans-serif
title "Claim2Value", and beneath it a smaller ice-blue subtitle in Chinese
"工业技术 Claim 到金融价值的可信映射 Agent". A dark bottom band with small text
"北大金融 AI 智能体创新大赛". Flat vector style, minimalist, premium fintech brand feel,
generous negative space, no gradients, no photos, no 3D effects.
```

## 变体 B：纯图形无文字（文字后期自己加，最稳）

```
A 16:9 minimalist fintech cover background, deep navy (#1E2761). Center: a horizontal
chain of three circles connected by thin lines — middle circle gold (#F0B429), side
circles ice blue (#CADCFC). Around the chain, a faint dotted arc suggesting a magnifying
glass or an audit trail. A few very subtle document/ledger line icons fading into the
background at low opacity. Flat vector, clean geometry, premium and calm, lots of empty
space, absolutely no text, no letters, no numbers.
```

## 提示词设计说明（可删）

- 链条 motif 与 PPT 封面、PDF 封面页一致（三节点：CLAIM→证据→价值，中间金色），三个材料同源；
- 指定了精确色号，避免模型自由发挥成通用蓝色科技风；
- 变体 B 规避图像模型写不好中文的风险：先生成纯图形底图，文字用 PPT/PS 后期叠加。
