"""Record reproducible offline review examples for semifinal evidence."""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.review_session import demo_cases, review_markdown, run_review


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path, help="New directory for evidence records")
    args = parser.parse_args()
    # Do not overwrite a previous run's evidence.
    args.out.mkdir(parents=True, exist_ok=False)
    records = [("green_demo", run_review(demo_name=list(demo_cases())[0])),
               ("shuanghuan_demo", run_review(demo_name=list(demo_cases())[1])),
               ("missing_evidence", run_review("公司产品适用于机器人。", "")),
               ("unresolved_semantics", run_review("公司产品适用于机器人。", "公司产品适用于机器人。"))]
    summary = []
    for name, result in records:
        (args.out / f"{name}.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        (args.out / f"{name}.md").write_text(review_markdown(result), encoding="utf-8")
        summary.append({"case": name, "verdict": result["verification"]["verdict"],
                        "financial_status": result["financial"]["status"],
                        "elapsed_ms": result["review_session"]["elapsed_ms"], "errors": result["errors"]})
    inputs = ["data/processed/local_demo_fixture.json", "data/processed/claim_bank_filled.json",
              "data/processed/shuanghuan_model_inputs.csv", "data/processed/tech_to_economics_ontology_shuanghuan.json"]
    # Include every processed CSV/ontology used by the default workflow as well.
    from src.workflow import DEFAULT_PARAMETER_CSV, DEFAULT_ONTOLOGY_PATH, DEFAULT_INDUSTRY_SUMMARY, DEFAULT_SHARE_CSV, DEFAULT_INPUT_PATH
    inputs += [str(Path(p).resolve().relative_to(ROOT)) for p in (
        DEFAULT_PARAMETER_CSV, DEFAULT_ONTOLOGY_PATH, DEFAULT_INDUSTRY_SUMMARY, DEFAULT_SHARE_CSV, DEFAULT_INPUT_PATH)]
    inputs += ["app.py", "src/review_session.py", "src/workflow.py", "src/state_verifier.py",
               "src/quantity_text.py", "src/engineering_analyzer.py", "src/economic_mapper.py", "src/causal_critic.py", "src/financial_model.py"]
    manifest = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in sorted(set(inputs))}
    (args.out / "run_index.json").write_text(json.dumps({
        "python": sys.version, "platform": platform.platform(),
        "streamlit": importlib.metadata.version("streamlit"),
        "scope": "Four functional examples; not an accuracy study, online LLM benchmark or real API billing measurement.",
        "external_api_calls": 0, "input_and_code_sha256": manifest, "cases": summary,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
