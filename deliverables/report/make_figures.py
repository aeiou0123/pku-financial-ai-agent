# -*- coding: utf-8 -*-
"""生成项目说明 PDF 与展示稿共用的图（PDF 供 LaTeX，PNG 备用）。

数据来自已核对的公开年报案例（绿的谐波 2024 年年度报告，13 页）与本轮实跑收据；
脚本只负责排版，不改动任何数值。
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]

INK, MUTED, LINE = "#25272b", "#62666b", "#dededb"
ACCENT, ACCENT_SOFT, TRACK = "#763b32", "#c49d95", "#e8e6e2"

font_manager.fontManager.addfont("C:/Windows/Fonts/msyh.ttc")
plt.rcParams.update({
    "font.family": "Microsoft YaHei",
    "font.size": 10.5,
    "axes.edgecolor": LINE,
    "axes.linewidth": 0.9,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.labelcolor": MUTED,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "text.color": INK,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
})


def save(fig, name):
    fig.savefig(OUT / f"{name}.pdf", bbox_inches="tight")
    fig.savefig(OUT / f"{name}.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("saved", name)


def check_tick_fit(ax, labels, name):
    """Fail loudly if axis tick labels overlap, so a broken figure never ships."""
    fig = ax.figure
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    boxes = [t.get_window_extent(renderer=renderer) for t in ax.get_xticklabels()]
    clashes = []
    for i in range(len(boxes) - 1):
        if boxes[i].x1 > boxes[i + 1].x0 + 0.5:
            clashes.append(f"{labels[i]} / {labels[i + 1]}")
    if clashes:
        raise SystemExit(f"OVERLAP in {name}: " + "; ".join(clashes))
    print(f"  {name}: {len(labels)} tick labels, no overlap")


def two_round():
    """同一份原件的两轮对比。"""
    labels = ["收下候选", "数值与参考表相符", "覆盖的目标口径", "报表口径错标"]
    before = [32, 26, 20, 6]
    after = [30, 30, 24, 0]
    fig, ax = plt.subplots(figsize=(6.6, 3.1))
    x = range(len(labels))
    width = 0.36
    bars1 = ax.bar([i - width / 2 for i in x], before, width, label="上一轮", color=TRACK, edgecolor=LINE, linewidth=0.7)
    bars2 = ax.bar([i + width / 2 for i in x], after, width, label="本轮（加入口径校验）", color=ACCENT, edgecolor=ACCENT, linewidth=0.7)
    for bars, values in ((bars1, before), (bars2, after)):
        for bar, value in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, value + 0.7, str(value),
                    ha="center", va="bottom", fontsize=10.5,
                    color=INK if bars is bars2 else MUTED,
                    fontweight="bold" if bars is bars2 else "normal")
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 36)
    ax.set_yticks([])
    ax.legend(frameon=False, loc="upper right", ncol=2, bbox_to_anchor=(1.0, 1.16))
    for side in ("left",):
        ax.spines[side].set_visible(False)
    save(fig, "fig_two_round")


def bridge():
    """归母净利润变化分解（真实数据，合计与目标变化完全相等）。"""
    data = json.loads((ROOT / "work/report_build/bridge.json").read_text(encoding="utf-8"))
    rows = data["bridge"]
    # The engine's factor names carry a parenthetical method note; shorten for the axis.
    short = {"收入变化贡献": "收入", "毛利率变化贡献": "毛利率",
             "其余税前项目净变化": "其他税前", "所得税费用变化": "所得税",
             "少数股东损益变化": "少数股东"}
    names = []
    for r in rows:
        base = r["因素"].split("（")[0].strip()
        names.append(short.get(base, base))
    values = [float(r["贡献_元"]) / 1e6 for r in rows]
    start = float(data["indicators"][3]["前期"]) / 1e6
    total = float(data["target_change_cny"]) / 1e6

    fig, ax = plt.subplots(figsize=(7.2, 3.2))
    # Position 0 is the starting level, 1..n the bridge steps, n+1 the ending level.
    ax.bar(0, start, color=INK, width=0.6, edgecolor="white", linewidth=0.8)
    ax.text(0, start + 2, f"{start:.2f}", ha="center", va="bottom", fontsize=9.5, color=INK)
    running = start
    for i, (name, value) in enumerate(zip(names, values), start=1):
        bottom = running if value >= 0 else running + value
        ax.bar(i, abs(value), bottom=bottom, color=ACCENT if value >= 0 else "#9aa3b2",
               edgecolor="white", linewidth=0.8, width=0.6)
        if value >= 0:
            ax.text(i, bottom + abs(value) + 1.6, f"+{value:.2f}", ha="center", va="bottom",
                    fontsize=9, color=INK)
        else:
            ax.text(i, bottom - 1.6, f"{value:.2f}", ha="center", va="top",
                    fontsize=9, color=INK)
        running += value
    end = len(names) + 1
    ax.bar(end, abs(start + total), bottom=min(start, start + total), color=INK, width=0.6,
           edgecolor="white", linewidth=0.8)
    ax.text(end, start + total + 2, f"{total:.2f}", ha="center", va="bottom",
            fontsize=9, color=INK)
    labels = ["2023 归母", "净利润"] + names + ["2024 归母", "净利润"]
    labels = ["2023 归母净利"] + names + ["2024 归母净利"]
    ax.set_xticks(range(end + 1))
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylim(0, max(start, abs(start), max(abs(v) for v in values), abs(start + total)) * 1.35)
    ax.set_ylabel("百万元")
    ax.grid(axis="y", color=LINE, linewidth=0.7)
    ax.set_axisbelow(True)
    check_tick_fit(ax, labels, "fig_bridge")
    save(fig, "fig_bridge")


def timing():
    """信号、成交与收益的时间关系。"""
    fig, ax = plt.subplots(figsize=(6.8, 1.9))
    steps = [("T 日", "收盘后形成信号", TRACK), ("T+1 日", "收盘按信号成交", ACCENT_SOFT),
             ("T+2 日", "持仓收益开始计入", ACCENT)]
    for i, (day, note, color) in enumerate(steps):
        ax.barh(0, 0.72, left=i * 1.0, height=0.44, color=color, edgecolor="white", linewidth=1.2)
        ax.text(i * 1.0 + 0.36, 0.34, day, ha="center", va="bottom", fontsize=11.5,
                color=INK, fontweight="bold")
        ax.text(i * 1.0 + 0.36, -0.34, note, ha="center", va="top", fontsize=9.5, color=MUTED)
        if i < len(steps) - 1:
            ax.annotate("", xy=(i + 0.97, 0), xytext=(i + 0.75, 0),
                        arrowprops=dict(arrowstyle="-|>", color=MUTED, linewidth=1.0))
    ax.set_xlim(-0.03, 2.75)
    ax.set_ylim(-0.85, 0.85)
    ax.axis("off")
    save(fig, "fig_timing")


def mechanism():
    """引用锚定与口径校验：命中与拒收。"""
    fig, ax = plt.subplots(figsize=(6.4, 3.2))
    ax.axis("off")
    steps = [
        ("模型提出候选", "字段与候选值一起返回", TRACK),
        ("摘录必须在原文中找到", "文件、位置、逐字一致", ACCENT_SOFT),
        ("口径与所在报表标题一致", "合并 / 母公司逐页判定", ACCENT_SOFT),
        ("进入人工核对表", "保留来源与摘录", ACCENT),
    ]
    top, height, gap = 0.90, 0.155, 0.035
    for i, (title, note, color) in enumerate(steps):
        y = top - height - i * (height + gap)
        ax.add_patch(plt.Rectangle((0.06, y), 0.88, height, facecolor=color,
                                   edgecolor="white", linewidth=1.2))
        ax.text(0.10, y + height * 0.62, title, ha="left", va="center", fontsize=11,
                color="white" if color == ACCENT else INK, fontweight="bold")
        ax.text(0.10, y + height * 0.26, note, ha="left", va="center", fontsize=9,
                color="white" if color == ACCENT else MUTED)
        if i < len(steps) - 1:
            ax.annotate("", xy=(0.50, y - gap + 0.008), xytext=(0.50, y - 0.006),
                        arrowprops=dict(arrowstyle="-|>", color=MUTED, linewidth=1.0))
    last_y = top - height - 3 * (height + gap)
    ax.add_patch(plt.Rectangle((0.06, last_y - 0.13), 0.88, 0.10, facecolor="#f4f3f1",
                               edgecolor=ACCENT, linewidth=0.9, linestyle="--"))
    ax.text(0.50, last_y - 0.08, "任一步不成立即拒收，并记录拒收原因", ha="center",
            va="center", fontsize=9.5, color=ACCENT)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    save(fig, "fig_mechanism")


def coverage():
    """24 个目标口径的覆盖：每个指标两年的数值是否都取到。"""
    labels = ["营业收入", "营业成本", "归母净利润", "利润总额", "所得税费用", "合并净利润",
              "经营现金流", "购建长期资产", "总资产", "总负债", "所有者权益", "归母权益"]
    before = [2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1]
    after = [2] * 12
    fig, ax = plt.subplots(figsize=(6.6, 3.0))
    y = range(len(labels))
    ax.barh([i + 0.19 for i in y], before, color=TRACK, height=0.32, label="上一轮",
            edgecolor="white", linewidth=0.7)
    ax.barh([i - 0.19 for i in y], after, color=ACCENT, height=0.32, label="本轮",
            edgecolor="white", linewidth=0.7)
    for i, (b, a) in enumerate(zip(before, after)):
        if b != 2:
            ax.text(b + 0.05, i + 0.19, str(b), va="center", fontsize=8.5, color=MUTED)
        ax.text(a - 0.06, i - 0.19, str(a), va="center", ha="right", fontsize=8.5,
                color="white", fontweight="bold")
    ax.text(0.02, -0.72, "条形内数字为该指标已取到的年度数（满分 2）", ha="left",
            va="center", fontsize=8.5, color=MUTED, transform=ax.transData)
    ax.set_yticks(list(y))
    ax.set_yticklabels(labels, fontsize=9.5)
    ax.set_xlim(0, 2.45)
    ax.set_xticks([0, 1, 2])
    ax.set_xticklabels(["0", "1 个年度", "2 个年度"])
    ax.legend(frameon=False, loc="lower right", ncol=2, bbox_to_anchor=(1.0, -0.24),
              fontsize=9)
    ax.grid(axis="x", color=LINE, linewidth=0.7)
    ax.set_axisbelow(True)
    ax.invert_yaxis()
    save(fig, "fig_coverage")


def efficiency():
    """两轮的调用、耗时与 token。"""
    fig, axes = plt.subplots(1, 3, figsize=(6.8, 2.5))
    specs = [("模型调用次数", [8, 3], "次"), ("耗时", [559.5, 348.5], "秒"), ("返回 token", [42516, 17932], "")]
    for ax, (title, values, unit) in zip(axes, specs):
        bars = ax.bar(["上一轮", "本轮"], values, color=[TRACK, ACCENT], width=0.55,
                      edgecolor="white", linewidth=0.8)
        for bar, value in zip(bars, values):
            text = f"{value:,.0f}" if value >= 1000 else f"{value:g}"
            ax.text(bar.get_x() + bar.get_width() / 2, value * 1.04, text,
                    ha="center", va="bottom", fontsize=9.5, color=INK)
        ax.set_title(title, fontsize=10, color=INK, pad=6)
        ax.set_ylim(0, max(values) * 1.28)
        ax.set_yticks([])
        ax.spines["left"].set_visible(False)
        ax.tick_params(axis="x", labelsize=9)
    fig.text(0.5, -0.06, "同一份年报 13 页，两轮均为实际调用模型；本地校验、回测不消耗调用",
             ha="center", fontsize=8.5, color=MUTED)
    save(fig, "fig_efficiency")


if __name__ == "__main__":
    two_round()
    bridge()
    timing()
    mechanism()
    coverage()
    efficiency()
