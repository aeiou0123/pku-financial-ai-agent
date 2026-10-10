"""Measure the actual offline mode with family-aware, explicitly limited evidence."""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import statistics
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.review_session import run_review


def fingerprint(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def aggregate(rows):
    if not rows:
        raise ValueError("No evaluation rows")
    ids = [r["case_id"] for r in rows]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate case IDs")
    groups, types, confusion = defaultdict(list), defaultdict(list), Counter()
    for row in rows:
        groups[row["family"]].append(row)
        types[row["category"]].append(row)
        confusion[(row["expected"], row["actual"]) ] += 1
    def rate(items):
        return sum(r["expected"] == r["actual"] for r in items) / len(items)
    return {"cases": len(rows), "families": len(groups),
            "exact_hits": sum(r["expected"] == r["actual"] for r in rows),
            "exact_rate": rate(rows), "family_macro_rate": statistics.mean(rate(g) for g in groups.values()),
            "always_abstain_hits": sum(r["expected"] == "abstain" for r in rows),
            "by_type": {k: {"n": len(v), "hits": sum(r["expected"] == r["actual"] for r in v), "rate": rate(v)} for k, v in sorted(types.items())},
            "confusion": [{"expected": k[0], "actual": k[1], "n": v} for k, v in sorted(confusion.items())],
            "verdict_counts": dict(Counter(r["actual"] for r in rows))}


def measure(case_id, family, category, claim, source, expected, repeats):
    durations, verdicts = [], []
    for _ in range(repeats):
        start = perf_counter()
        result = run_review(claim, source)
        durations.append((perf_counter() - start) * 1000)
        verdicts.append(result["verification"]["verdict"])
    if len(set(verdicts)) != 1:
        raise ValueError("Non-deterministic verdict: " + case_id)
    return {"case_id": case_id, "family": family, "category": category,
            "claim": claim, "source": source, "expected": expected, "actual": verdicts[0],
            "rule_flags": result["verification"]["rule_flags"], "median_ms": statistics.median(durations),
            "financial_status": result["financial"]["status"], "external_api_calls": result["review_session"]["external_api_calls"]}


def evaluate(output, repeats=5):
    if repeats < 1 or repeats > 100:
        raise ValueError("repeats must be 1..100")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    bench = ROOT / "benchmarks/claim_verification_v2.json"
    probes_path = ROOT / "benchmarks/local_boundary_probes.json"
    cases = json.loads(bench.read_text(encoding="utf-8"))["cases"]
    probes = json.loads(probes_path.read_text(encoding="utf-8"))["cases"]
    # Keep one original reference per family; its source is not re-authenticated.
    references = {}
    for c in cases:
        pair = (c["original_claim"], c["original_source"])
        if c["original_claim_id"] in references and references[c["original_claim_id"]] != pair:
            raise ValueError("Conflicting original family references")
        references[c["original_claim_id"]] = pair
    mutations = [measure(c["case_id"], c["original_claim_id"], c["mutation_type"], c["mutated_claim"], c["mutated_source"], c["expected_verdict"], repeats) for c in cases]
    boundaries = [measure(c["case_id"], c["case_id"], "development_probe", c["claim"], c["source"], c["expected_verdict"], repeats) for c in probes]
    reference_rows = []
    for key, (claim, source) in sorted(references.items()):
        r = run_review(claim, source)
        reference_rows.append({"case_id": key, "claim": claim, "source": source,
                               "actual": r["verification"]["verdict"], "rule_flags": r["verification"]["rule_flags"]})
    elapsed = sorted(r["median_ms"] for r in mutations)
    p95_index = max(0, __import__("math").ceil(0.95 * len(elapsed)) - 1)
    summary = {"scope": "EXISTING_DEVELOPMENT_BENCHMARK_AND_AUTHORED_PROBES_NOT_OUT_OF_SAMPLE",
               "created_at_utc": datetime.now(timezone.utc).isoformat(), "mutations": aggregate(mutations),
               "development_probes": aggregate(boundaries),
               "original_references": {"n": len(reference_rows), "alerts": sum(bool(r["rule_flags"]) for r in reference_rows), "ground_truth_status": "NOT_REAUTHENTICATED_NOT_A_FALSE_POSITIVE_RATE"},
               "runtime": {"repeats_per_mutation": repeats, "p50_case_median_ms": statistics.median(elapsed), "p95_case_median_ms": elapsed[p95_index], "external_api_calls": sum(r["external_api_calls"] for r in mutations + boundaries), "api_charge": 0, "compute_cost_measured": False, "scope": "Warm local custom-rule function; excludes startup, browser, reading, network and LLM. No throughput claim."},
               "environment": {"python": platform.python_version(), "platform": platform.platform(), "cpu_logical_count": os.cpu_count()},
               "input_sha256": {str(p.relative_to(ROOT)): fingerprint(p) for p in [bench, probes_path]},
               "code_sha256": {str(p.relative_to(ROOT)): fingerprint(p) for p in [Path(__file__), ROOT/'src/review_session.py', ROOT/'src/state_verifier.py', ROOT/'src/quantity_text.py', ROOT/'src/workflow.py', ROOT/'src/evidence_ledger.py']},
               "limitations": ["98 mutations derive from 19 original families; no new independent natural claims or source-authenticated labels.", "Rules were previously developed using this benchmark; these are development results, not generalization accuracy.", "Always-abstain is a diagnostic baseline, not a competitive LLM baseline.", "No actual current Qwen/Kimi or other model API run.", "Local abstention on clean text is intentional and must not be called positive verification.", "Authored boundary probes were used to review and repair aliases; they are not a held-out set."]}
    payload = {"summary": summary, "mutations": mutations, "development_probes": boundaries, "original_references": reference_rows}
    (output/'results.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    failures = [r for r in mutations + boundaries if r["expected"] != r["actual"]]
    (output/'failures.json').write_text(json.dumps(failures, ensure_ascii=False, indent=2), encoding='utf-8')
    lines = ["# 本地核查模式开发评测", "", "此结果是既有开发库复测与人工构造边界探针，不是样本外业务准确率。98条扰动来自19条原声明家族；原件与标签未在本轮重新认证。", "", f"扰动题严格标签命中：{summary['mutations']['exact_hits']}/98（{summary['mutations']['exact_rate']:.1%}）；按19个家族等权平均：{summary['mutations']['family_macro_rate']:.1%}。", f"总是拒答诊断基线：{summary['mutations']['always_abstain_hits']}/98。不能据此证明优于商业大模型。", "", "| 类别 | 命中/样本 | 比例 |", "|---|---:|---:|"]
    for name, stats in summary['mutations']['by_type'].items():
        lines.append(f"| {name} | {stats['hits']}/{stats['n']} | {stats['rate']:.1%} |")
    lines += ["", f"19条未扰动原始参考中，{summary['original_references']['alerts']}条触发提示；未重审原件和自然标签，因此不把它叫误报率。", f"10条人工边界探针命中{summary['development_probes']['exact_hits']}/10，其中包括用于修复的同义术语；不是独立验证。", "", f"每题重复{repeats}次；98个题目中位耗时的p50={statistics.median(elapsed):.3f}ms，p95={elapsed[p95_index]:.3f}ms。暖启动本地函数，外部API调用0次、API费用0；算力费用未计量，不代表在线全流程成本。", "", "## 失败记录", ""]
    for r in failures:
        lines.append(f"- {r['case_id']}：期望{r['expected']}，实际{r['actual']}。{'; '.join(r['rule_flags'])}")
    lines += ["", "详见results.json（所有输入输出、环境、数据/代码指纹）与failures.json。正面支持不在本地规则模式能力内；未发现问题会保守拒答。下一轮应收集独立原文，预先冻结标签，按原始来源/时间分组留出测试，不能把同一原声明的扰动分到训练和测试两边。"]
    (output/'report.md').write_text('\n'.join(lines), encoding='utf-8')
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--repeats', type=int, default=5)
    args = parser.parse_args()
    print(json.dumps(evaluate(args.out, args.repeats), ensure_ascii=False, indent=2))
