# -*- coding: utf-8 -*-
"""生成说明文档与路演 PPT 共用的 7 张真实数据图（PDF 供 LaTeX，PNG 供 Beamer 备用）。
风格：克制——白底、无渐变、无多余网格、直接标数值、品牌色藏青/金/灰。"""
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from pathlib import Path

OUT = Path(__file__).parent
NAVY, GOLD, GRAY, LIGHT = "#1E2761", "#F0B429", "#9AA3B2", "#E9EDF5"

font_manager.fontManager.addfont("C:/Windows/Fonts/msyh.ttc")
plt.rcParams.update({
    "font.family": "Microsoft YaHei", "font.size": 10,
    "axes.edgecolor": "#CCCCCC", "axes.linewidth": 0.8,
    "axes.spines.top": False, "axes.spines.right": False,
    "figure.facecolor": "white", "axes.facecolor": "white",
})

def save(fig, name):
    fig.savefig(OUT / f"{name}.pdf", bbox_inches="tight")
    fig.savefig(OUT / f"{name}.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("saved", name)

def hgrid(ax):
    ax.yaxis.grid(True, color=LIGHT, linewidth=0.8)
    ax.set_axisbelow(True)

# ---------- 1. ASP 假设 vs 实际（击穿图） ----------
fig, ax = plt.subplots(figsize=(5.6, 2.6))
xs = ["券商盈利预测假设", "2024 年报实际", "2025 市场最新口径"]
vals = [1500, 1293, 1099]
colors = [GRAY, NAVY, GOLD]
bars = ax.bar(xs, vals, width=0.55, color=colors)
ax.axhline(1500, color=GRAY, linestyle="--", linewidth=0.8, alpha=0.6)
for b, v in zip(bars, vals):
    ax.text(b.get_x() + b.get_width()/2, v + 22, f"{v:,} 元/台", ha="center", fontsize=10, color="#212121")
ax.set_ylim(0, 1750)
ax.set_ylabel("谐波减速器 ASP（元/台）", fontsize=9)
ax.tick_params(axis="x", labelsize=9.5)
hgrid(ax)
save(fig, "fig_asp")

# ---------- 2. Claim Bank 公司分布（堆叠横条） ----------
bank = json.load(open("data/processed/claim_bank_filled.json", encoding="utf-8"))
per = {}
for c in bank:
    per.setdefault(c["subject"], [0, 0])
    per[c["subject"]][0 if c["verification_status"] == "已验证" else 1] += 1
items = sorted(per.items(), key=lambda kv: sum(kv[1]))
names = [k for k, _ in items]
ver = [v[0] for _, v in items]
pen = [v[1] for _, v in items]
fig, ax = plt.subplots(figsize=(6.2, 3.4))
y = range(len(names))
ax.barh(y, ver, color=NAVY, height=0.62, label="已验证")
ax.barh(y, pen, left=ver, color=GOLD, height=0.62, label="待验证")
for i, (v, p) in enumerate(zip(ver, pen)):
    ax.text(v + p + 0.08, i, str(v + p), va="center", fontsize=9, color="#212121")
ax.set_yticks(list(y), names, fontsize=9.5)
ax.set_xlim(0, 8.2)
ax.xaxis.grid(True, color=LIGHT, linewidth=0.8)
ax.set_axisbelow(True)
ax.legend(frameon=False, fontsize=9, loc="lower right")
save(fig, "fig_claims")

# ---------- 3. 置信度传导（批判前→批判后，成对柱） ----------
fig, ax = plt.subplots(figsize=(5.6, 2.4))
names = ["扭矩密度 → 渗透率", "重量 → BOM 成本"]
before = [0.8, 0.5]
after = [0.6, 0.32]
x = np.arange(2)
b1 = ax.bar(x - 0.17, before, width=0.32, color=GRAY, label="因果批判前")
b2 = ax.bar(x + 0.17, after, width=0.32, color=NAVY, label="因果批判后")
for bars in (b1, b2):
    for b in bars:
        ax.text(b.get_x() + b.get_width()/2, b.get_height() + 0.015, f"{b.get_height():.2f}",
                ha="center", fontsize=9.5)
ax.set_xticks(x, names, fontsize=9.5)
ax.set_ylim(0, 1.0)
ax.set_ylabel("经济假设置信度", fontsize=9)
ax.legend(frameon=False, fontsize=8.5, loc="upper center", bbox_to_anchor=(0.5, 1.04), ncol=2)
hgrid(ax)
save(fig, "fig_confidence")

# ---------- 4. RV 均价锚点 ----------
fig, ax = plt.subplots(figsize=(5.8, 2.7))
xs = ["2021", "2022", "2023", "2024H1"]
actual = [2533, 3209, 3065, 2653]
bars = ax.bar(xs, actual, width=0.5, color=NAVY)
for b, v in zip(bars, actual):
    ax.text(b.get_x() + b.get_width()/2, v + 70, f"{v:,}", ha="center", fontsize=9)
ax.axhline(4300, color=GRAY, linestyle="--", linewidth=1.0)
ax.text(3.45, 4460, "修正前假设 4,300", fontsize=8.5, color=GRAY, ha="right")
ax.axhline(3100, color=GOLD, linestyle="-", linewidth=1.4)
ax.text(3.45, 3150, "修正后 3,100", fontsize=8.5, color="#B8860B", ha="right")
ax.set_ylim(0, 4800)
ax.set_ylabel("RV 减速器均价（元/台）", fontsize=9)
hgrid(ax)
save(fig, "fig_rv_anchor")

# ---------- 5. Benchmark：裸 LLM vs 规则层+LLM（benchmarks/pipeline_report.md 口径） ----------
fig, ax = plt.subplots(figsize=(5.6, 2.5))
labels = ["Claude", "GPT"]
before = [62.5, 65.3]
after = [91.8, 90.8]
x = np.arange(2)
b1 = ax.bar(x - 0.17, before, width=0.32, color=GRAY, label="裸 LLM")
b2 = ax.bar(x + 0.17, after, width=0.32, color=NAVY, label="规则层 + LLM")
for bars in (b1, b2):
    for b in bars:
        ax.text(b.get_x() + b.get_width()/2, b.get_height() + 0.6, f"{b.get_height():.1f}%",
                ha="center", fontsize=9)
ax.set_xticks(x, labels, fontsize=10)
ax.set_ylim(50, 100)
ax.set_ylabel("98 用例判别准确率", fontsize=9)
ax.legend(frameon=False, fontsize=8.5, loc="upper center", bbox_to_anchor=(0.5, 1.04), ncol=2)
hgrid(ax)
save(fig, "fig_benchmark")

# ---------- 5b. 反向 DCF：市价 vs 模型三情景 ----------
fig, ax = plt.subplots(figsize=(6.0, 2.5))
names = ["市价（2026-09-04）", "乐观 upside", "基准 base", "悲观 downside"]
vals = [512.96, 58.5, 30.8, 0.9]
colors = [GOLD, NAVY, NAVY, GRAY]
y = np.arange(len(names))[::-1]
bars = ax.barh(y, vals, color=colors, height=0.58)
for yi, v in zip(y, vals):
    ax.text(v + 8, yi, f"{v:g}", va="center", fontsize=9.5, color="#212121", fontweight="bold")
ax.set_yticks(y, names, fontsize=9.5)
ax.set_xlim(0, 640)
ax.set_xlabel("亿元", fontsize=9)
ax.xaxis.grid(True, color=LIGHT, linewidth=0.8)
ax.set_axisbelow(True)
save(fig, "fig_reverse_dcf")

# ---------- 6. TAM/SAM/SOM（带宽示意，描述在条带右侧，非比例轴） ----------
fig, ax = plt.subplots(figsize=(6.2, 2.4))
rows = [("TAM 上限锚", "谐波环节远期空间 71–603 亿元", 1.00, LIGHT, NAVY),
        ("SAM", "买方 / 卖方 / 产业资本三类客户", 0.68, "#3A4A9E", "white"),
        ("SOM", "证据服务订阅 2–6 亿元/年", 0.40, NAVY, "white")]
for i, (name, desc, w, color, tcolor) in enumerate(rows):
    y = 2 - i
    ax.barh(y, w, height=0.6, color=color)
    ax.text(0.015, y, name, fontsize=10, fontweight="bold", color=tcolor, va="center")
    ax.text(w + 0.03, y, desc, fontsize=9, color="#5A6372", va="center")
ax.set_xlim(0, 1.75)
ax.set_ylim(-0.75, 2.55)
ax.axis("off")
ax.text(0.0, -0.6, "注：带宽为示意，不代表比例关系；TAM 取 GGII 与高盛两种口径并列。",
        fontsize=8, color="#9AA3B2")
save(fig, "fig_tam")

# ---------- 7. 路线图（三栏等宽） ----------
fig, ax = plt.subplots(figsize=(6.4, 2.7))
cols = [("0–6 月 · 验证期", GOLD, NAVY, ["Claim 终验 47/51 已完成", "5 家付费试点", "案例报告产品化"]),
        ("6–18 月 · 放大期", NAVY, "white", ["实时检索上线", "专利核验全覆盖", "覆盖扩展至 50 家"]),
        ("18–36 月 · 规模期", "#5B6DB8", "white", ["平台化 + API 输出", "跨行业 ontology", "证据资产订阅化"])]
for i, (title, color, tcolor, texts) in enumerate(cols):
    x = i / 3
    ax.barh(2.1, 1/3, left=x, height=0.52, color=color)
    ax.text(x + 1/6, 2.1, title, ha="center", va="center", color=tcolor, fontsize=10, fontweight="bold")
    for j, t in enumerate(texts):
        ax.text(x + 0.02, 1.42 - j * 0.6, "· " + t, fontsize=9, color="#212121", va="center")
ax.set_xlim(0, 1)
ax.set_ylim(-0.5, 2.6)
ax.axis("off")
save(fig, "fig_roadmap")

print("all figures done")
