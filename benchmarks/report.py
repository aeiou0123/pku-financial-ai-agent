"""
report.py — Claim2Value Benchmark: 判别力报告生成器
================================================================

读取 evaluate.py 的结果，汇总成可读的报告。

输出：
  1. 控制台表格（快速查看）
  2. benchmarks/report.md（完整报告，可直接放进比赛材料）

核心指标：
  - 判别准确率：hit / (hit + miss)，error 不计入（避免网关抖动冤枉模型）
  - abstain 率：证据缺失用例中模型选择拒答的比例（诚实性核心指标）
  - overconfident 率：模型置信度超过合理上限的比例

运行：
    python benchmarks/report.py
    python benchmarks/report.py --input benchmarks/results/evaluation_results.jsonl
"""

from __future__ import annotations
import argparse
import io
import json
from collections import defaultdict
from pathlib import Path
from datetime import datetime

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT = REPO_ROOT / "benchmarks" / "results" / "evaluation_results_v2.jsonl"
V1_INPUT = REPO_ROOT / "benchmarks" / "results" / "evaluation_results_v1.jsonl"
REPORT_PATH = REPO_ROOT / "benchmarks" / "report.md"

MUTATION_LABELS = {
    "value_tampering":   "数值篡改",
    "qualifier_removal": "限定词删除",
    "unit_swap":         "口径偷换",
    "source_downgrade":  "来源降级",
    "temporal_shift":    "时间错位",
    "evidence_absence":  "证据缺失",
}

VERDICT_CN = {
    "supported": "成立",
    "refuted": "不成立",
    "partially_supported": "部分成立",
    "definition_mismatch": "口径不符",
    "low_confidence": "来源不可靠",
    "abstain": "拒答",
}


def load_results(path):
    rows = []
    with io.open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                # 跳过写入到一半的残行（后台 evaluate 正在 append 时可能出现）
                continue
    return rows


def summarize(rows):
    """按模型分组统计。返回 {model: {...}}"""
    by_model = defaultdict(list)
    for r in rows:
        by_model[r["model"]].append(r)

    summary = {}
    for model, rs in by_model.items():
        hit = sum(1 for r in rs if r["judgement"] == "hit")
        miss = sum(1 for r in rs if r["judgement"] == "miss")
        err = sum(1 for r in rs if r["judgement"] == "error")
        total_valid = hit + miss
        acc = hit / total_valid if total_valid else 0.0

        # abstain 率：只看证据缺失用例
        ev_abs = [r for r in rs if r["mutation_type"] == "evidence_absence"]
        abstain = sum(1 for r in ev_abs if r["actual_verdict"] == "abstain")
        abstain_rate = abstain / len(ev_abs) if ev_abs else 0.0

        # 失败模式拆解：
        #   over_abstain 过度拒答 —— 有证据却判"拒答"（太保守）
        #   deceived     被骗过   —— 证据被扰动却判"成立"（太轻信）
        miss_rows = [r for r in rs if r["judgement"] == "miss"]
        over_abstain = sum(1 for r in miss_rows if r["actual_verdict"] == "abstain")
        deceived = sum(1 for r in miss_rows if r["actual_verdict"] == "supported")
        other_miss = len(miss_rows) - over_abstain - deceived

        # overconfident 只在判错时统计：
        # "答错还自信"才是危险信号；单纯置信度高不算问题
        overconf = sum(1 for r in miss_rows
                       if r.get("actual_confidence") is not None
                       and r["actual_confidence"] > 0.7)
        overconf_rate = overconf / len(rs) if rs else 0.0

        # 按扰动类型分解
        by_type = defaultdict(lambda: {"hit": 0, "miss": 0, "error": 0})
        for r in rs:
            by_type[r["mutation_type"]][r["judgement"]] += 1

        summary[model] = {
            "total": len(rs),
            "hit": hit, "miss": miss, "error": err,
            "accuracy": acc,
            "abstain_rate": abstain_rate,
            "abstain_n": abstain,
            "ev_abs_n": len(ev_abs),
            "overconfident_rate": overconf_rate,
            "over_abstain": over_abstain,
            "deceived": deceived,
            "other_miss": other_miss,
            "by_type": dict(by_type),
        }
    return summary


def type_accuracy(type_stat):
    h, m = type_stat["hit"], type_stat["miss"]
    return h / (h + m) if (h + m) else 0.0


def print_console(summary):
    models = list(summary.keys())
    print("\n" + "=" * 72)
    print("  Claim2Value Benchmark — 判别力汇总")
    print("=" * 72)

    # 总体表
    print(f"\n{'模型':20s} {'准确率':>7s} {'hit':>4s} {'miss':>5s} {'err':>4s} "
          f"{'abstain率':>9s} {'过度拒答':>8s} {'被骗过':>7s}")
    print("-" * 72)
    for m in models:
        s = summary[m]
        print(f"{m:20s} {s['accuracy']*100:6.1f}% {s['hit']:4d} {s['miss']:5d} "
              f"{s['error']:4d} {s['abstain_rate']*100:8.0f}% "
              f"{s['over_abstain']:8d} {s['deceived']:7d}")

    # 按扰动类型分解
    all_types = sorted({t for s in summary.values() for t in s["by_type"]})
    print(f"\n{'扰动类型':14s}", end="")
    for m in models:
        print(f" {m[:18]:>18s}", end="")
    print()
    print("-" * (14 + 19 * len(models)))
    for t in all_types:
        label = MUTATION_LABELS.get(t, t)
        print(f"{label:14s}", end="")
        for m in models:
            ts = summary[m]["by_type"].get(t)
            if ts:
                acc = type_accuracy(ts)
                n = ts["hit"] + ts["miss"]
                print(f" {acc*100:6.0f}% ({n:2d}题)   ", end="")
            else:
                print(f" {'—':>18s}", end="")
        print()
    print()


def render_markdown(summary, rows, input_path, v1_summary=None):
    models = list(summary.keys())
    lines = []
    a = lines.append

    a("# Claim2Value Benchmark — 判别力评估报告")
    a("")
    a(f"> 生成时间：{datetime.now():%Y-%m-%d %H:%M}")
    a(f"> 数据来源：`{input_path.name}`")
    a(f"> 评估模型：{', '.join(models)}")
    if v1_summary:
        a("> 含 Oracle 修正前后对比（v1 → v2）")
    a("")
    a("---")
    a("")
    a("## 一、方法论")
    a("")
    a("采用 **Mutation Testing**（变异测试）检验 claim 验证器的判别力：")
    a("对 19 条真实工业 claim 的证据链注入 6 类扰动，生成 70 个测试用例，")
    a("检验模型能否识别被动过手脚的输入。核心假设：")
    a("")
    a("> 一个可信的 verifier，不仅要能验证正确的 claim，")
    a("> 更要能识别看似合理但实际错误的 claim。")
    a("")
    a("### 扰动类型")
    a("")
    a("| 类型 | 说明 | 期望模型行为 |")
    a("|---|---|---|")
    a("| 数值篡改 | 把关键数值改大/改小 | refuted |")
    a("| 限定词删除 | 删掉\"同等出力\"等限定条件 | partially_supported |")
    a("| 口径偷换 | 额定扭矩 ↔ 峰值扭矩 | definition_mismatch |")
    a("| 来源降级 | 年报 → 市场传闻 | low_confidence |")
    a("| 时间错位 | 年份改错 | refuted |")
    a("| 证据缺失 | 删除全部证据 | **abstain**（拒答） |")
    a("")

    # Oracle 修正说明
    if v1_summary:
        a("### Oracle 自我修正")
        a("")
        a("首轮评估（v1）发现 benchmark 自身的 oracle 存在缺陷：部分用例的")
        a("expected_verdict 假设了模型不可见的证据（如只给来源名未给原始数值），")
        a("导致模型合理拒答被判为 miss。修正措施：")
        a("")
        a("1. **注入原始参数**：从 parameter_table 提取真实数值注入 evidence，")
        a("   让数值篡改类用例真正\"可检出\"")
        a("2. **修正 expected_verdict**：对证据不含原始数值的用例，")
        a("   abstain/low_confidence 才是正确答案")
        a("3. **修正 mutate.py**：value_tampering 排除年份，避免\"632年\"这类荒谬用例")
        a("4. **修正 confidence 语义**：明确区分\"对 verdict 的把握\"与\"对 claim 的把握\"")
        a("")
        a("这一过程本身就是 Oracle Mutation Testing 方法论的自我应验——")
        a("benchmark 的评判标准也需要被验证和修正。")
        a("")

    a("---")
    a("")
    a("## 二、总体判别力")
    a("")
    a("| 模型 | 判别准确率 | hit | miss | error | abstain 率 |")
    a("|---|---|---|---|---|---|")
    for m in models:
        s = summary[m]
        a(f"| {m} | **{s['accuracy']*100:.1f}%** | {s['hit']} | {s['miss']} | "
          f"{s['error']} | {s['abstain_rate']*100:.1f}% |")
    a("")
    a("> 判别准确率 = hit / (hit + miss)，error（API 调用失败）不计入，")
    a("> 避免网关抖动冤枉模型能力。abstain 率仅统计\"证据缺失\"用例。")
    a("")
    a("---")
    a("")
    a("## 三、失败模式分析")
    a("")
    a("判别准确率低，模型到底是怎么错的？把 miss 拆开看：")
    a("")
    a("| 模型 | miss 总数 | 过度拒答 | 被骗过 | 其他 |")
    a("|---|---|---|---|---|")
    for m in models:
        s = summary[m]
        a(f"| {m} | {s['miss']} | {s['over_abstain']} | {s['deceived']} | {s['other_miss']} |")
    a("")
    a("- **过度拒答**：模型判 abstain，但期望是给出实质判断（太保守）")
    a("- **被骗过**：模型判 supported，但证据已被扰动（太轻信）")
    a("")

    # 自动判断主导失败模式
    for m in models:
        s = summary[m]
        if s["over_abstain"] > s["deceived"]:
            a(f"> **{m} 的主导失败模式是「过度拒答」**：{s['over_abstain']} 条过度拒答 "
              f"vs {s['deceived']} 条被骗过。模型偏保守，在有证据时仍选择 abstain。")
        elif s["deceived"] > s["over_abstain"]:
            a(f"> **{m} 的主导失败模式是「被骗过」**：{s['deceived']} 条被骗过 "
              f"vs {s['over_abstain']} 条过度拒答。模型偏轻信，容易被扰动证据蒙混。")
        a("")
    a("---")
    a("")
    a("## 四、按扰动类型分解")
    a("")
    header = "| 扰动类型 |" + "".join(f" {m} |" for m in models)
    sep = "|---|" + "---|" * len(models)
    a(header)
    a(sep)
    all_types = sorted({t for s in summary.values() for t in s["by_type"]},
                       key=lambda t: list(MUTATION_LABELS).index(t) if t in MUTATION_LABELS else 99)
    for t in all_types:
        label = MUTATION_LABELS.get(t, t)
        row = f"| {label} |"
        for m in models:
            ts = summary[m]["by_type"].get(t)
            if ts:
                acc = type_accuracy(ts)
                n = ts["hit"] + ts["miss"]
                row += f" {acc*100:.0f}% ({n}题) |"
            else:
                row += " — |"
        a(row)
    a("")
    a("---")
    a("")
    a("## 五、关键发现")
    a("")

    # 自动提炼发现
    for m in models:
        s = summary[m]
        a(f"### {m}")
        a("")
        # 最弱项
        weak = None
        for t, ts in s["by_type"].items():
            acc = type_accuracy(ts)
            if weak is None or acc < weak[1]:
                weak = (t, acc)
        if weak and weak[1] < 1.0:
            a(f"- **最弱环节**：{MUTATION_LABELS.get(weak[0], weak[0])}，"
              f"判别准确率仅 {weak[1]*100:.0f}%")
        # abstain
        if s["ev_abs_n"]:
            a(f"- **诚实性（abstain）**：面对 {s['ev_abs_n']} 条无证据 claim，"
              f"拒答 {s['abstain_n']} 条（{s['abstain_rate']*100:.0f}%）。"
              + ("能做到证据不足时拒答。" if s["abstain_rate"] >= 0.8
                 else "**存在硬答倾向**——这是可信度隐患。"))
        a(f"- **失败模式**：过度拒答 {s['over_abstain']} 条，被骗过 {s['deceived']} 条")
        # 错且自信（最危险信号）
        if s["overconfident_rate"] > 0:
            a(f"- **错且自信**：{s['overconfident_rate']*100:.0f}% 的用例判错且置信度 > 0.7"
              f"（最危险的信号）")
        a("")

    a("---")
    a("")

    # Oracle 修正前后对比
    if v1_summary:
        a("## 六、Oracle 修正前后对比")
        a("")
        a("| 模型 | v1 准确率 | v2 准确率 | v1 过度拒答 | v2 过度拒答 | v1 被骗 | v2 被骗 |")
        a("|---|---|---|---|---|---|---|")
        for m in models:
            s2 = summary[m]
            s1 = v1_summary.get(m)
            if s1:
                a(f"| {m} | {s1['accuracy']*100:.1f}% | **{s2['accuracy']*100:.1f}%** | "
                  f"{s1['over_abstain']} | {s2['over_abstain']} | "
                  f"{s1['deceived']} | {s2['deceived']} |")
            else:
                a(f"| {m} | — | **{s2['accuracy']*100:.1f}%** | — | {s2['over_abstain']} | "
                  f"— | {s2['deceived']} |")
        a("")
        a("> v1 = Oracle 修正前（expected_verdict 假设了模型不可见的证据）")
        a("> v2 = Oracle 修正后（注入真实参数 + 修正期望答案 + 排除年份误改）")
        a("")

    a("## 七、局限")
    a("")
    a("- 评估基于 LLM-as-judge，judge 本身可能存在系统性偏差")
    a("- 70 个用例覆盖 6 类扰动，但未覆盖组合扰动（如同时篡改数值+偷换口径）")
    a("- abstain 的定义依赖 prompt 引导，不同 prompt 下拒答率可能变化")
    a("- 样本来自 3 家机器人产业链公司，外推到其他行业需重新验证")
    a("")

    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default=str(DEFAULT_INPUT))
    ap.add_argument("--output", default=str(REPORT_PATH))
    ap.add_argument("--v1", default=str(V1_INPUT),
                    help="v1 结果文件路径（Oracle 修正前），用于对比")
    ap.add_argument("--no-v1", action="store_true", help="不加载 v1 对比")
    args = ap.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        raise SystemExit(f"结果文件不存在: {input_path}\n先运行 evaluate.py")

    rows = load_results(input_path)
    if not rows:
        raise SystemExit("结果文件为空")

    summary = summarize(rows)
    print_console(summary)

    # 加载 v1 做对比
    v1_summary = None
    if not args.no_v1:
        v1_path = Path(args.v1)
        if v1_path.exists():
            v1_rows = load_results(v1_path)
            if v1_rows:
                v1_summary = summarize(v1_rows)

    md = render_markdown(summary, rows, input_path, v1_summary)
    out_path = Path(args.output)
    io.open(out_path, "w", encoding="utf-8").write(md)
    print(f"报告已写入: {out_path}")


if __name__ == "__main__":
    main()
