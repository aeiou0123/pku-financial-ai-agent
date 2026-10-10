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
    import streamlit as st
    from src.review_session import demo_cases, run_review, review_markdown
    from src.review_ui import STYLE, NAV_LABELS, page_heading, section_heading, note, verdict_html, scenario_rows, assumption_rows

    st.set_page_config(page_title="Claim2Value · 研究工作台", layout="wide")
    st.markdown(STYLE, unsafe_allow_html=True)
    with st.sidebar:
        st.markdown('<div class="c2v-brand"><div class="c2v-brand-name">Claim2Value</div>'
                    '<div class="c2v-brand-sub">产业研究工作台</div></div>', unsafe_allow_html=True)
        mode = st.radio("工作区", ["历史财务核验", "自定义核查", "示例情景"],
                        format_func=NAV_LABELS.get, key="review_mode")
        st.markdown('<div class="c2v-side-note">机器人产业链<br>绿的谐波 / 双环传动 / 步科股份<br><br>资料、判断与假设分别记录。</div>', unsafe_allow_html=True)
        with st.expander("使用说明"):
            st.write("财务记录可查看原值和年报出处。声明核查对照你提供的原文。情景测算使用两家公司的固定参数。")
            st.caption("本地运行，不联网检索。声明核查只覆盖已有规则；原件和统计口径仍需人工确认。")
    if mode == "历史财务核验":
        from src.financial_evidence import render_history
        pending_root = REPO_ROOT / "work/csmar_handoff/20261009"
        render_history(st, pending_root if pending_root.is_dir() else None)
        return
    if mode == "示例情景":
        page_heading(st, "情景测算", "选用已保存的公司参数，查看不同假设下的计算结果。", section="情景测算 / 固定假设")
        cases = demo_cases()
        name = st.selectbox("研究案例", list(cases), key="demo_name")
        case = cases[name]
        section_heading(st, case["company"], "固定参数示例")
        st.write(case["claim"])
        note(st, "这组结果用于比较假设。2025期是原有模型设定；不是当前预测，也不证明技术改进带来了收入或价值增长。")
        if st.button("计算情景", key="run_demo", type="primary"):
            st.session_state.pop("review_result", None)
            try:
                st.session_state["review_result"] = run_review(demo_name=name)
            except Exception:
                st.error("计算失败。请检查公司数据文件后重试。")
    else:
        page_heading(st, "声明核查", "把企业表述与引用原文放在一起，检查数值、指标和限定条件。", section="声明核查 / 原文对照")
        with st.form("custom_review"):
            claim = st.text_area("企业声明", placeholder="例如：新一代关节模组减重30%以上。", max_chars=4000, height=95, key="custom_claim")
            source = st.text_area("引用原文", placeholder="粘贴公告、年报或技术资料中的相关段落。", max_chars=60000, height=170, key="custom_source")
            left, right = st.columns(2)
            with left:
                url = st.text_input("来源链接（选填）", placeholder="https://…", key="custom_url")
            with right:
                locator = st.text_input("文档与页码（选填）", placeholder="例如：2025年报，第7页", key="custom_locator")
            submitted = st.form_submit_button("核查声明", type="primary")
        if submitted:
            st.session_state.pop("review_result", None)
            try:
                st.session_state["review_result"] = run_review(claim, source, url, locator)
            except ValueError as exc:
                st.error(str(exc))
            except Exception:
                st.error("核查失败，未生成报告。请检查运行环境后重试。")
    result = st.session_state.get("review_result")
    expected_mode = "preset_scenario_demo" if mode == "示例情景" else "custom_rule_review"
    if result and (result["review_session"]["mode"] != expected_mode or (
            mode == "示例情景" and result["review_session"]["case_id"] != case["case_id"])):
        result = None
    if not result:
        st.caption("填写后提交，结果会显示在下方。" if mode == "自定义核查" else "计算后可查看情景、参数依据和报告。")
        return
    session = result["review_session"]
    section_heading(st, "本次记录", session['company'] or "自定义输入")
    st.write(result["claim"])
    st.caption("结果对应上方这条已提交的声明。编辑输入后，请重新提交。")
    v = result["verification"]
    verdict_names = {"abstain": "缺少证据" if not result['source'] else "暂不能判断",
                     "partially_supported": "遗漏限定条件", "refuted": "原文与声明有矛盾",
                     "definition_mismatch": "指标口径不同", "low_confidence": "来源尚需核实", "supported": "未检出规则问题"}
    detail = "；".join(v.get('rule_flags') or []) or v['reasoning']
    detail = detail.replace('在 source 中存在但 claim 中缺失', '出现在引用原文中，但声明没有保留')
    st.markdown(verdict_html(verdict_names.get(v['verdict'], v['verdict']), detail), unsafe_allow_html=True)
    st.caption("这里只检查已有规则。未检出问题，不代表声明已经得到证实。")
    evidence_tab, analysis_tab, export_tab = st.tabs(["原文与出处", "测算与假设", "下载报告"])
    with evidence_tab:
        section_heading(st, "引用原文", "用户提供" if expected_mode == 'custom_rule_review' else "已有资料摘录")
        st.write(result["source"] or "没有提供引用原文。补充出处后可重新核查。")
        st.caption("出处：" + (session['source_locator'] or '未填写'))
        if session['source_url']:
            st.link_button("查看来源", session['source_url'])
        with st.expander("出处核验与记录明细"):
            status = session['evidence_status']
            st.write("摘录尚待原件核对。" if status == 'candidate_evidence_not_finally_verified' else status)
            for limitation in session['limitations']:
                st.write("• " + limitation)
            st.caption("原文指纹：" + session['source_sha256'])
            st.caption("记录时间（UTC）：" + session['created_at_utc'])
    with analysis_tab:
        financial = result["financial"]
        if financial.get("status") == "ok":
            section_heading(st, "情景结果", "人民币 · 亿元")
            st.table(scenario_rows(financial.get('scenarios', {})))
            st.caption("企业价值不是股价。下表是这组固定模型中的假设，历史财务更新不会自动改动它们。")
            section_heading(st, "采用的假设")
            st.table(assumption_rows(result.get('economics')))
            with st.expander("仍需补充的证据"):
                for review in (result.get('causal') or {}).get('reviews', []):
                    st.write(review['variable_label'])
                    for requirement in review.get('counterfactual_requirements', []):
                        if not requirement['satisfied']:
                            st.write("• " + requirement['requirement'])
                st.caption("模型中的归因折扣属于假设设定，没有经过独立因果检验。")
        else:
            note(st, "这条输入只做声明核查。没有绑定公司参数，不计算估值。")
        for error in result.get("errors", []):
            st.error(f"{error['stage']}: {error['error']}")
        with st.expander("查看完整计算记录"):
            st.text(result.get("report_markdown", ""))
    with export_tab:
        section_heading(st, "保存本次记录")
        st.write("报告包括已提交的声明、引用原文、出处和核查结果。")
        left, right = st.columns(2)
        with left:
            st.download_button("下载记录 · JSON", json.dumps(result, ensure_ascii=False, indent=2),
                               "claim2value_review.json", "application/json", key="review_json")
        with right:
            st.download_button("下载报告 · Markdown", review_markdown(result),
                               "claim2value_review.md", "text/markdown", key="review_md")
        st.caption(f"记录时间（UTC）：{session['created_at_utc']}。本次计算{session['elapsed_ms']}毫秒，不含页面操作；没有外部模型调用。")


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
