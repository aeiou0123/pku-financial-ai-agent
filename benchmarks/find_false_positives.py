"""定位规则层误伤明细：LLM 判对但被规则层覆盖后判错的用例"""
import io, json, sys
from pathlib import Path

REPO = Path(r"C:/Users/Sun/WorkBuddy/2026-09-04-00-09-51/pku-repo3")
sys.path.insert(0, str(REPO))
from src.state_verifier import StateVerifier

cases = json.loads(io.open(REPO / "benchmarks/claim_verification_v2.json", encoding="utf-8").read())["cases"]
case_map = {c["case_id"]: c for c in cases}
llm_rows = []
for line in io.open(REPO / "benchmarks/results/evaluation_results_v2.jsonl", encoding="utf-8"):
    line = line.strip()
    if line:
        try:
            llm_rows.append(json.loads(line))
        except json.JSONDecodeError:
            pass

verifier = StateVerifier()

for model in ["claude-sonnet-5", "gpt-5.5"]:
    print(f"\n{'='*90}\n模型: {model} — 误伤明细（LLM 判对 → 规则层覆盖后判错）\n{'='*90}")
    for r in llm_rows:
        if r["model"] != model or r["judgement"] != "hit":
            continue
        cid = r["case_id"]
        case = case_map[cid]
        rule_r = verifier.verify(case["mutated_claim"], case["mutated_source"])
        if rule_r.verdict_override and rule_r.verdict_override != r["expected_verdict"]:
            print(f"\n[{cid}] type={case['mutation_type']}")
            print(f"  expected: {case['expected_verdict']}  llm(对): {r['actual_verdict']}  rule(错): {rule_r.verdict_override}")
            for f in rule_r.flags:
                print(f"  FLAG: {f}")
            print(f"  claim : {case['mutated_claim'][:90]}")
            print(f"  source: {case['mutated_source'][:90]}")
