"""Claim2Value 本地 Demo。

默认运行不调用 LLM、不访问网络，只读取本地 fixture 和模型输入：

    python app.py

如果安装了 Streamlit，可运行：

    streamlit run app.py

无 API 模式的规则边界是刻意保守的：规则层发现确定性问题时给出对应结论，
否则返回 ``abstain``，并把 fixture 中的 expected verdict 标记为参考值。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

from src.evidence_ledger import Evidence, EvidenceLedger, EvidenceLevel
from src.financial_model import (
    DEFAULT_INPUT_PATH,
    FinancialModelInputs,
    run_all_scenarios,
)
from src.state_verifier import StateVerifier


REPO_ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE_PATH = REPO_ROOT / "data" / "processed" / "local_demo_fixture.json"


def load_fixture(path: Path | str = DEFAULT_FIXTURE_PATH) -> Dict[str, Any]:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Demo fixture 不存在：{path}")
    return json.loads(path.read_text(encoding="utf-8"))


def run_local_demo(
    fixture_path: Path | str = DEFAULT_FIXTURE_PATH,
    inputs_path: Path | str = DEFAULT_INPUT_PATH,
) -> Dict[str, Any]:
    fixture = load_fixture(fixture_path)
    evidence = fixture["evidence"]
    ledger = EvidenceLedger()
    ledger.add(Evidence(
        source_text=evidence["source_text"],
        source_type=EvidenceLevel(evidence.get("source_type", "unknown")),
        source_url=evidence.get("source_url"),
    ))
    rule_result = StateVerifier().verify(fixture["claim"], evidence["source_text"])

    if rule_result.verdict_override:
        verdict = rule_result.verdict_override
        verdict_source = "state_verifier_rule"
        reasoning = "；".join(rule_result.flags)
    else:
        verdict = "abstain"
        verdict_source = "local_no_llm"
        reasoning = "规则层未发现确定性异常，但本地 Demo 未调用 LLM，拒绝推断语义结论。"

    inputs = FinancialModelInputs.from_csv(inputs_path)
    scenarios = run_all_scenarios(inputs)
    financial_summary = {
        scenario: {
            "enterprise_value_bn": result["valuation"]["enterprise_value_bn"],
            "2027_revenue_bn": result["projections"][-1]["revenue_bn"],
            "2027_fcf_bn": result["projections"][-1]["fcf_bn"],
            "model_status": result["model_status"],
        }
        for scenario, result in scenarios.items()
    }
    return {
        "demo_status": "local_reproducible_prototype",
        "claim": {
            "case_id": fixture["case_id"],
            "company": fixture["company"],
            "text": fixture["claim"],
            "fixture_expected_verdict": fixture.get("expected_verdict"),
            "expected_verdict_scope": fixture.get("expected_verdict_scope"),
        },
        "evidence": {
            "ledger": ledger.summary(),
            "source_url": evidence.get("source_url"),
            "source_locator": evidence.get("source_locator"),
            "extraction_status": evidence.get("extraction_status"),
        },
        "verification": {
            "verdict": verdict,
            "verdict_source": verdict_source,
            "reasoning": reasoning,
            "rule_flags": rule_result.flags,
            "rule_result": rule_result.to_dict(),
        },
        "financial_impact": financial_summary,
        "limitations": fixture.get("limitations", []),
    }


def print_demo(result: Dict[str, Any]) -> None:
    claim = result["claim"]
    verification = result["verification"]
    print("=" * 72)
    print("Claim2Value 本地 Demo（无外部 API）")
    print("=" * 72)
    print(f"案例：{claim['company']} / {claim['case_id']}")
    print(f"Claim：{claim['text']}")
    print(f"验证结论：{verification['verdict']}（{verification['verdict_source']}）")
    print(f"说明：{verification['reasoning']}")
    print(f"证据可信度：{result['evidence']['ledger']['trust_score']}")
    print(f"证据定位：{result['evidence']['source_locator']}")
    print("\n财务影响（简化情景，bn CNY）：")
    for scenario, summary in result["financial_impact"].items():
        print(
            f"  {scenario:8s} EV={summary['enterprise_value_bn']:.4f} "
            f"2027收入={summary['2027_revenue_bn']:.4f} "
            f"2027 FCF={summary['2027_fcf_bn']:.4f}"
        )
    print("\n限制：")
    for limitation in result["limitations"]:
        print(f"  - {limitation}")


def render_streamlit() -> None:
    try:
        import streamlit as st
    except ImportError as exc:  # pragma: no cover - 仅在可选 UI 依赖缺失时触发
        raise RuntimeError("Streamlit UI 需要安装 requirements.txt 中的 streamlit") from exc

    st.set_page_config(page_title="Claim2Value 本地 Demo", layout="wide")
    st.title("Claim2Value：证据到财务影响")
    st.caption("绿的谐波单案例 · 本地 fixture · 无外部 API")
    result = run_local_demo()
    st.subheader("Claim 与证据")
    st.write(result["claim"]["text"])
    st.json(result["evidence"])
    st.subheader("验证结果")
    st.metric("本地结论", result["verification"]["verdict"])
    st.write(result["verification"]["reasoning"])
    if result["verification"]["rule_flags"]:
        st.warning("；".join(result["verification"]["rule_flags"]))
    st.subheader("简化财务影响")
    st.table([
        {"scenario": scenario, **summary}
        for scenario, summary in result["financial_impact"].items()
    ])
    st.subheader("限制")
    for limitation in result["limitations"]:
        st.write(f"- {limitation}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Claim2Value 本地 Demo")
    parser.add_argument("--fixture", default=str(DEFAULT_FIXTURE_PATH))
    parser.add_argument("--inputs", default=str(DEFAULT_INPUT_PATH))
    parser.add_argument("--json-out", default="")
    args = parser.parse_args()
    result = run_local_demo(args.fixture, args.inputs)
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
