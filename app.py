"""Claim2Value 本地 Demo（串联全链路）。

默认运行不调用 LLM、不访问网络，通过本地 fixture 驱动真实的
``run_financial_chain(local_only=True)`` 链路：

    Claim → 验证 → 门控 → 工程归一化 → 经济映射 → 因果批判 → 财务三情景

得益于串联结构，Demo 展示的是产品的核心卖点：验证结论会真实传导进
经济假设与财务估值（如工程参数驱动销量/成本调整后得到不同的 EV），
而不是"验证归验证、财务照算"的两套并存数字。

    python app.py
    streamlit run app.py   # 若已安装 streamlit

无 API 模式的规则边界是刻意保守的：规则层发现确定性问题时给出结论，
否则返回 ``abstain`` 并把 fixture 的 expected verdict 标注为参考值。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

from src.workflow import run_financial_chain


REPO_ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE_PATH = REPO_ROOT / "data" / "processed" / "local_demo_fixture.json"


def load_fixture(path: Path | str = DEFAULT_FIXTURE_PATH) -> Dict[str, Any]:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Demo fixture 不存在：{path}")
    return json.loads(path.read_text(encoding="utf-8"))


def run_local_demo(
    fixture_path: Path | str = DEFAULT_FIXTURE_PATH,
) -> Dict[str, Any]:
    """走真实串联链路（local_only，无 LLM、无网络）。

    返回 ``run_financial_chain`` 的结构化结果，附带 fixture 参考标注。
    """
    fixture = load_fixture(fixture_path)
    evidence = fixture["evidence"]

    chain = run_financial_chain(
        claim=fixture["claim"],
        source=evidence["source_text"],
        local_only=True,
    )

    # 附加 fixture 参考信息（不参与校验，仅作比对展示）
    chain["demo_case"] = {
        "case_id": fixture["case_id"],
        "company": fixture["company"],
        "fixture_expected_verdict": fixture.get("expected_verdict"),
        "expected_verdict_scope": fixture.get("expected_verdict_scope"),
        "evidence": evidence,
        "limitations": fixture.get("limitations", []),
    }
    return chain


def _scenario_summary(scenarios: Dict[str, Any]) -> list[dict[str, Any]]:
    """把 financial.scenarios 转成便于打印/表格的行。"""
    return [
        {
            "scenario": name,
            "EV(bn)": s.get("enterprise_value_bn"),
            "2027收入(bn)": s.get("revenue_2027_bn"),
            "2027FCF(bn)": s.get("fcf_2027_bn"),
            "2027EBITDA(bn)": s.get("ebitda_2027_bn"),
            "model_status": s.get("model_status"),
        }
        for name, s in scenarios.items()
    ]


def _assumption_lines(economics: Dict[str, Any]) -> list[str]:
    """提取经济假设的可读文本行（含变量标签、方向、弹性、证据等级、置信度）。"""
    lines: list[str] = []
    assumptions = (economics or {}).get("assumption_set", {}).get("assumptions", [])
    for a in assumptions:
        label = a.get("variable_label") or a.get("variable", "?")
        direction = "↑" if a.get("direction") == "positive" else (
            "↓" if a.get("direction") == "negative" else "→")
        pct = a.get("delta_pct")
        evidence = a.get("evidence_grade", "")
        conf = a.get("confidence")
        line = f"  {label} {direction} "
        if a.get("qualitative_only"):
            line += "(定性)"
        elif pct is not None and abs(pct * 100) >= 0.05:
            line += f"{pct*100:+.2f}%"
        else:
            line += "(量化，|Δ|<0.05%)"
        line += f" | 证据 {evidence or '?'} | 置信度 {conf}"
        if a.get("rule_name"):
            line += f" | {a['rule_name']}"
        lines.append(line)
    return lines


def print_demo(result: Dict[str, Any]) -> None:
    case = result["demo_case"]
    verification = result.get("verification", {})
    gate = result.get("gate", {})
    economics = result.get("economics")
    causal = result.get("causal")
    financial = result.get("financial", {})
    errors = result.get("errors", [])

    print("=" * 72)
    print("Claim2Value 本地 Demo（串联全链路 · 无外部 API）")
    print("=" * 72)
    print(f"案例：{case['company']} / {case['case_id']}")
    print(f"Claim：{case.get('fixture_claim') or result.get('claim')}")
    print(f"证据来源：{case['evidence'].get('source_text')}")

    print("\n① 验证")
    print(f"  结论：{verification.get('verdict')} "
          f"({verification.get('verdict_source')})  置信度 {verification.get('confidence')}")
    print(f"  说明：{verification.get('reasoning')}")
    if verification.get("rule_flags"):
        print("  规则标记：")
        for f in verification["rule_flags"]:
            print(f"    - {f}")
    print(f"  [fixture 参考] expected_verdict={case.get('fixture_expected_verdict')} "
          f"({case.get('expected_verdict_scope')})")

    print("\n② 门控")
    print(f"  passed={gate.get('passed')} — {gate.get('reason')}")

    if gate.get("passed") and financial.get("status") == "ok":
        print("\n③ 工程归一化")
        eng = result.get("engineering") or {}
        print(f"  用 {eng.get('n_rows', 0)} 行参数做归一化，可比性分级 "
              f"{eng.get('comparability_counts', {})}")

        print("\n④ 经济假设（工程参数 → 经济机制，带 provenance）")
        lines = _assumption_lines(economics)
        print("\n".join(lines) if lines else "  （无定量假设）")

        print("\n⑤ 因果批判")
        if causal:
            print(f"  审查 {causal.get('total_alternatives', 0)} 个替代解释，"
                  f"{causal.get('total_open_counterfactuals', 0)} 条待补反事实证据")
        annotation = financial.get("critic_annotation") or {}
        if annotation:
            print(f"  置信度打折：{annotation.get('adjusted_confidence')}，"
                  f"不可归因 {annotation.get('non_attributable_pct')}%")
            print(f"  依据：{annotation.get('basis')}")

        print("\n⑥ 财务三情景（bn CNY，批判层调整后假设）")
        for row in _scenario_summary(financial.get("scenarios", {})):
            print(f"  {row['scenario']:8s} EV={row['EV(bn)']:.4f} "
                  f"收入={row['2027收入(bn)']:.4f} FCF={row['2027FCF(bn)']:.4f} "
                  f"({row['model_status']})")
    else:
        print("\n⛔ 门控拦截 / 财务链路未生成")
        print(f"  验证结论 {verification.get('verdict')} 不在放行集合，"
              f"因此不生成财务结论 —— 这是刻意的诚实边界，不是缺陷。")

    if errors:
        print("\n[链路断点日志]")
        for e in errors:
            print(f"  - {e.get('stage')}: {e.get('error')}")

    print("\n限制：")
    for limitation in case.get("limitations", []):
        print(f"  - {limitation}")

    print("\n综合报告（markdown）：")
    print("-" * 72)
    print(result.get("report_markdown", ""))


def render_streamlit() -> None:
    try:
        import streamlit as st
    except ImportError as exc:  # pragma: no cover - 仅在可选 UI 依赖缺失时触发
        raise RuntimeError("Streamlit UI 需要安装 requirements.txt 中的 streamlit") from exc

    st.set_page_config(page_title="Claim2Value 本地 Demo", layout="wide")
    st.title("Claim2Value：证据到财务影响（串联全链路）")
    st.caption("绿的谐波单案例 · 本地 fixture · 无外部 API")

    result = run_local_demo()
    case = result["demo_case"]
    verification = result.get("verification", {})
    gate = result.get("gate", {})
    financial = result.get("financial", {})

    st.subheader("Claim 与证据")
    st.write(result.get("claim"))
    st.json(case["evidence"])

    col1, col2 = st.columns(2)
    with col1:
        st.metric("本地结论", verification.get("verdict"))
    with col2:
        st.metric("置信度", str(verification.get("confidence")))

    st.write(verification.get("reasoning"))
    for f in verification.get("rule_flags", []):
        st.warning(f)
    st.caption(f"[fixture 参考] expected_verdict={case.get('fixture_expected_verdict')} ")

    st.subheader("门控")
    st.write(f"passed={gate.get('passed')} — {gate.get('reason')}")

    st.subheader("经济假设（工程 → 经济传导）")
    st.write(_assumption_lines(result.get("economics")))

    st.subheader("因果批判")
    annotation = financial.get("critic_annotation") if financial else {}
    if result.get("causal"):
        st.write(f"审查 {result['causal'].get('total_alternatives')} 个替代解释，"
                 f"{result['causal'].get('total_open_counterfactuals')} 条待补反事实")
    if annotation:
        st.write(f"置信度打折：{annotation.get('adjusted_confidence')}，"
                 f"不可归因 {annotation.get('non_attributable_pct')}%")

    st.subheader("财务三情景（批判层调整后）")
    if financial.get("status") == "ok":
        st.table(_scenario_summary(financial.get("scenarios", {})))
    else:
        st.error(financial.get("reason", "门控拦截，不生成财务结论"))

    st.subheader("限制")
    for limitation in case.get("limitations", []):
        st.write(f"- {limitation}")


def main() -> None:
    if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    parser = argparse.ArgumentParser(description="Claim2Value 本地 Demo（串联全链路）")
    parser.add_argument("--fixture", default=str(DEFAULT_FIXTURE_PATH))
    parser.add_argument("--json-out", default="")
    args = parser.parse_args()
    result = run_local_demo(args.fixture)
    print_demo(result)
    if args.json_out:
        output = Path(args.json_out)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nJSON：{output}")


if __name__ == "__main__":
    if "streamlit" in sys.modules:
        render_streamlit()
    else:
        main()