"""
workflow.py — Claim2Value LangGraph 工作流编排层
=================================================

将 claim_verifier → state_verifier → evidence_ledger 串联成端到端验证流水线。

架构：
    Input(claim, source)
        │
        ▼
    ┌─────────────────────┐
    │ evidence_ledger_node │  证据收集 & 分级
    └────────┬────────────┘
             │
             ▼
    ┌─────────────────────┐
    │ state_verifier_node  │  规则层检查
    └────────┬────────────┘
             │
             ▼
    ┌─────────────────────┐
    │ claim_verifier_node  │  LLM 语义判断 + 合并
    └────────┬────────────┘
             │
             ▼
    ┌─────────────────────┐
    │ report_node          │  生成结构化报告
    └─────────────────────┘

注意：本项目不强依赖 langgraph 库（避免安装复杂性）。
如果 langgraph 可用则用它编排；否则用纯 Python 函数链。
两者输出完全一致。

用法：
    from src.workflow import run_verification

    result = run_verification(
        claim="绿的谐波2024年谐波减速器销量24.65万台，同比增长16.56%",
        source="国信证券研报：2024年谐波减速器及金属部件收入3.25亿元...",
    )
    print(result["verdict"])        # "supported"
    print(result["confidence"])     # 0.85
    print(result["rule_flags"])     # []
    print(result["report"])         # 格式化报告
"""

from __future__ import annotations
import json
from dataclasses import asdict
from typing import Dict, Any, List, Optional
from pathlib import Path

from src.state_verifier import StateVerifier
from src.evidence_ledger import EvidenceLedger, EvidenceLevel
from src.claim_verifier import ClaimVerifier, VerificationOutput


# ============================================================
# 工作流节点
# ============================================================

def evidence_ledger_node(state: Dict) -> Dict:
    """节点 1：证据收集 & 分级"""
    source = state.get("source", "")
    ledger = EvidenceLedger()
    if source and source.strip():
        ledger.add_from_text(source)

    state["ledger"] = ledger
    state["trust_score"] = ledger.trust_score()
    state["has_evidence"] = not ledger.is_empty
    state["evidence_summary"] = ledger.summary()
    return state


def state_verifier_node(state: Dict) -> Dict:
    """节点 2：规则层检查"""
    claim = state.get("claim", "")
    source = state.get("source", "")
    verifier = StateVerifier()
    rule_result = verifier.verify(claim, source)

    state["rule_result"] = rule_result
    state["rule_verdict"] = rule_result.verdict_override
    state["rule_flags"] = rule_result.flags
    return state


def claim_verifier_node(state: Dict) -> Dict:
    """节点 3：LLM 语义判断 + 合并"""
    claim = state.get("claim", "")
    source = state.get("source", "")

    # 如果规则层已检出确定性问题且无证据场景已处理，
    # 仍然调用 LLM 以获取语义层面的 reasoning（但规则层 verdict 优先）
    model = state.get("model", "claude-sonnet-5")

    # 无证据 → 直接 abstain，不调 LLM
    if not state.get("has_evidence", False):
        state["verdict"] = "abstain"
        state["confidence"] = 0.1
        state["reasoning"] = "证据缺失，拒绝给出结论"
        state["verdict_source"] = "rule"
        state["llm_verdict"] = None
        state["llm_reasoning"] = None
        return state

    # 有证据 → 调用 LLM
    verifier = ClaimVerifier(model=model)
    result = verifier.verify(claim, source)

    state["verdict"] = result.verdict
    state["confidence"] = result.confidence
    state["reasoning"] = result.reasoning
    state["verdict_source"] = result.verdict_source
    state["llm_verdict"] = result.llm_verdict
    state["llm_confidence"] = result.llm_confidence
    state["llm_reasoning"] = result.llm_reasoning
    return state


def report_node(state: Dict) -> Dict:
    """节点 4：生成结构化报告"""
    verdict_cn = {
        "supported": "成立",
        "refuted": "不成立",
        "partially_supported": "部分成立",
        "definition_mismatch": "口径不符",
        "low_confidence": "来源不可靠",
        "abstain": "拒答",
        "error": "错误",
    }

    lines = []
    lines.append("=" * 60)
    lines.append("  Claim2Value 验证报告")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"  Claim: {state.get('claim', '')[:80]}...")
    lines.append(f"  判定: {verdict_cn.get(state.get('verdict', ''), state.get('verdict', ''))}")
    lines.append(f"  置信度: {state.get('confidence', 0):.2f}")
    lines.append(f"  判定来源: {state.get('verdict_source', '')}")
    lines.append(f"  证据可信度: {state.get('trust_score', 0):.2f}")
    lines.append("")

    # 规则层标记
    flags = state.get("rule_flags", [])
    if flags:
        lines.append("  规则层检出:")
        for f in flags:
            lines.append(f"    - {f}")
    else:
        lines.append("  规则层: 未检出异常")
    lines.append("")

    # LLM reasoning
    llm_r = state.get("llm_reasoning")
    if llm_r:
        lines.append(f"  LLM 推理: {llm_r[:200]}")
    lines.append("")
    lines.append("=" * 60)

    state["report"] = "\n".join(lines)
    return state


# ============================================================
# 工作流编排
# ============================================================

# 节点执行顺序
WORKFLOW_NODES = [
    ("evidence_ledger", evidence_ledger_node),
    ("state_verifier", state_verifier_node),
    ("claim_verifier", claim_verifier_node),
    ("report", report_node),
]


def run_verification(
    claim: str,
    source: str,
    model: str = "claude-sonnet-5",
) -> Dict[str, Any]:
    """
    运行端到端验证工作流。

    Args:
        claim: claim 文本
        source: 证据来源文本
        model: LLM 模型名

    Returns:
        包含所有节点输出的完整状态字典
    """
    state = {
        "claim": claim,
        "source": source,
        "model": model,
    }

    for name, node_fn in WORKFLOW_NODES:
        state = node_fn(state)
        state["_current_node"] = name

    return state


def run_batch(
    cases: List[Dict],
    model: str = "claude-sonnet-5",
    show_progress: bool = True,
) -> List[Dict]:
    """
    批量运行验证工作流。

    Args:
        cases: [{"case_id": ..., "mutated_claim": ..., "mutated_source": ...}, ...]
        model: LLM 模型名
        show_progress: 是否打印进度

    Returns:
        [{"case_id": ..., "verdict": ..., "judgement": ..., ...}, ...]
    """
    results = []
    total = len(cases)

    for i, case in enumerate(cases, 1):
        claim = case.get("mutated_claim", "")
        source = case.get("mutated_source", "")

        state = run_verification(claim, source, model)

        expected = case.get("expected_verdict", "")
        actual = state.get("verdict", "")
        hit = actual == expected

        row = {
            "case_id": case.get("case_id", ""),
            "mutation_type": case.get("mutation_type", ""),
            "expected_verdict": expected,
            "actual_verdict": actual,
            "judgement": "hit" if hit else "miss",
            "verdict_source": state.get("verdict_source", ""),
            "confidence": round(state.get("confidence", 0), 3),
            "rule_flags": state.get("rule_flags", []),
            "llm_verdict": state.get("llm_verdict"),
            "trust_score": round(state.get("trust_score", 0), 3),
        }
        results.append(row)

        if show_progress:
            mark = "HIT " if hit else "MISS"
            rule_tag = "[R]" if state.get("verdict_source") == "rule" else "[L]"
            print(f"[{i}/{total}] {mark} {rule_tag} {case.get('case_id',''):16s} "
                  f"exp={expected:20s} act={actual:20s}")

    return results


# ============================================================
# CLI 入口
# ============================================================

if __name__ == "__main__":
    import sys
    import argparse
    import io

    REPO_ROOT = Path(__file__).resolve().parent.parent

    ap = argparse.ArgumentParser(description="Claim2Value 验证工作流")
    ap.add_argument("--model", default="claude-sonnet-5")
    ap.add_argument("--cases", default=str(REPO_ROOT / "benchmarks" / "claim_verification_v2.json"))
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--out", default="")
    ap.add_argument("--single", action="store_true", help="单条验证模式")
    ap.add_argument("--claim", default="", help="单条验证的 claim 文本")
    ap.add_argument("--source", default="", help="单条验证的 source 文本")
    args = ap.parse_args()

    if args.single:
        # 单条验证
        if not args.claim:
            print("请用 --claim 提供 claim 文本")
            sys.exit(1)

        state = run_verification(args.claim, args.source, args.model)
        print(state.get("report", ""))
        print()
        print("详细输出:")
        print(json.dumps({
            "verdict": state.get("verdict"),
            "confidence": round(state.get("confidence", 0), 3),
            "verdict_source": state.get("verdict_source"),
            "rule_flags": state.get("rule_flags", []),
            "llm_verdict": state.get("llm_verdict"),
            "trust_score": round(state.get("trust_score", 0), 3),
        }, ensure_ascii=False, indent=2))

    else:
        # 批量验证
        cases_path = Path(args.cases)
        if not cases_path.exists():
            print(f"用例文件不存在: {cases_path}")
            sys.exit(1)

        data = json.loads(io.open(cases_path, encoding="utf-8").read())
        cases = data["cases"]
        if args.limit:
            cases = cases[:args.limit]

        print(f"用例: {len(cases)}  模型: {args.model}")
        print("=" * 70)

        results = run_batch(cases, args.model)

        # 统计
        hit = sum(1 for r in results if r["judgement"] == "hit")
        miss = sum(1 for r in results if r["judgement"] == "miss")
        total = hit + miss

        print(f"\n{'=' * 70}")
        print(f"总准确率: {hit}/{total} = {hit/total*100:.1f}%")

        # 按扰动类型
        from collections import defaultdict
        by_type = defaultdict(lambda: {"hit": 0, "miss": 0})
        for r in results:
            by_type[r["mutation_type"]][r["judgement"]] += 1

        print(f"\n按扰动类型:")
        for mtype, stats in sorted(by_type.items()):
            acc = stats["hit"] / (stats["hit"] + stats["miss"]) if (stats["hit"] + stats["miss"]) else 0
            print(f"  {mtype:25s} {acc*100:5.1f}%  ({stats['hit']}/{stats['hit']+stats['miss']})")

        if args.out:
            out_path = Path(args.out)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with io.open(out_path, "w", encoding="utf-8") as f:
                for r in results:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
            print(f"\n结果已写入: {out_path}")
