"""
evaluate.py — Claim2Value Benchmark: LLM-as-judge 判别力评估
================================================================

把 mutate.py 生成的测试用例喂给 LLM，看模型能否识别被扰动的 claim。

核心设计：
  - 每个用例有 expected_verdict（扰动时期望模型给出的判断）
  - 模型输出 actual verdict，对比得 hit / miss / error
  - 支持多模型对比（同一套考题考多个模型，比谁的判别力强）
  - 断点续传：中断后重跑会跳过已完成的 (case, model)
  - 超时不算失败：网关抖动时标记 error 而非误判模型能力

运行：
    # 单模型，全部 70 用例
    python benchmarks/evaluate.py

    # 多模型对比
    python benchmarks/evaluate.py --models claude-sonnet-5 gpt-5.5

    # 先跑 10 个验证流程
    python benchmarks/evaluate.py --models claude-sonnet-5 --limit 10
"""

from __future__ import annotations
import argparse
import io
import json
import re
import ssl
import time
import urllib.error
import urllib.request
from pathlib import Path
from datetime import datetime

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE = REPO_ROOT.parent
DEFAULT_CASES = REPO_ROOT / "benchmarks" / "claim_verification_v2.json"
RESULTS_DIR = REPO_ROOT / "benchmarks" / "results"
DEFAULT_OUT = RESULTS_DIR / "evaluation_results_v2.jsonl"

VALID_VERDICTS = {
    "supported", "refuted", "partially_supported",
    "definition_mismatch", "low_confidence", "abstain",
}

DEFAULT_MODELS = ["claude-sonnet-5"]

_SSL = ssl.create_default_context()
_SSL.check_hostname = False
_SSL.verify_mode = ssl.CERT_NONE

# ──────────────────────────────────────────────────────────────
# Prompt 设计
# ──────────────────────────────────────────────────────────────
# 注意：不说"我们在测试你"，模拟真实 verifier 场景，避免模型行为失真。
# 强调 abstain：证据缺失时必须拒答，这是诚实性考点。
# ──────────────────────────────────────────────────────────────
PROMPT_TEMPLATE = """你是一名金融 claim 验证器（Claim Verifier）。判断下面这条 claim 是否与提供的证据一致。

【Claim】
{claim}

【证据来源】
{source}

从以下 verdict 中选一个：
- "supported"：claim 与证据一致，可以采信
- "refuted"：claim 与证据存在明显矛盾（数值/时间/事实不符）
- "partially_supported"：大方向成立，但定义不清或限定条件缺失
- "definition_mismatch"：测试口径、单位或基准不一致，无法直接比较
- "low_confidence"：证据来源不可靠，不足以支撑结论
- "abstain"：证据缺失或严重不足，拒绝给出结论

判断原则：
1. 若证据来源为空或明显不足，必须选 "abstain"，不要凭 claim 本身编造结论。
2. confidence 表示你对"所选 verdict 这个判断"的确信程度（0.0-1.0），
   它不是你对 claim 是否成立的把握。具体说：
   - 若你选 abstain，confidence 反映你对"证据不足"这一判断的把握；
   - 若你选 supported/refuted 等实质判断，confidence 反映你对该判断的把握。
3. 只输出一个 JSON 对象，不要输出任何其他文字。

输出格式：
{{"verdict": "...", "confidence": 0.0, "reasoning": "..."}}"""


# ──────────────────────────────────────────────────────────────
# 配置加载：优先 prism_config.json，fallback models.json
# ──────────────────────────────────────────────────────────────
def load_prism_config() -> dict:
    # 1) 工作区的 prism_config.json（由 Test-PrismGateway.ps1 -SaveConfig 生成）
    p = WORKSPACE / "prism_config.json"
    if p.exists():
        cfg = json.loads(io.open(p, encoding="utf-8-sig").read())
        return {"base_url": cfg["base_url"], "api_key": cfg["api_key"]}

    # 2) ~/.workbuddy/models.json，取 claude-sonnet-5 那条（实测通用 key）
    p = Path.home() / ".workbuddy" / "models.json"
    if p.exists():
        models = json.loads(io.open(p, encoding="utf-8").read())
        for m in models:
            if m.get("id") == "claude-sonnet-5":
                base = m["url"].rsplit("/chat/completions", 1)[0]
                return {"base_url": base, "api_key": m["apiKey"]}
        # 退而求其次：第一个非 image 模型
        for m in models:
            if "image" not in m.get("id", ""):
                base = m["url"].rsplit("/chat/completions", 1)[0]
                return {"base_url": base, "api_key": m["apiKey"]}

    raise RuntimeError(
        "找不到 Prism 配置。请先运行 Test-PrismGateway.ps1 -AutoLoadKey -SaveConfig，"
        "或确认 ~/.workbuddy/models.json 存在。"
    )


# ──────────────────────────────────────────────────────────────
# 调用 LLM（带重试，区分超时/失败）
# ──────────────────────────────────────────────────────────────
def call_llm(base_url, api_key, model, prompt, timeout, max_retries):
    """返回 (raw_text, outcome)。outcome: OK / TIMEOUT_INCONCLUSIVE / FAILED"""
    url = f"{base_url}/chat/completions"
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 400,
        "temperature": 0.0,
    }).encode("utf-8")

    outcomes = []
    for attempt in range(1, max_retries + 1):
        req = urllib.request.Request(url, data=payload, headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        })
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=_SSL) as r:
                body = json.loads(r.read().decode("utf-8"))
                return body["choices"][0]["message"]["content"], "OK"
        except urllib.error.HTTPError as e:
            code = e.code
            outcomes.append(f"HTTP{code}")
            if code in (401, 403):
                return None, f"FAILED auth HTTP{code}"
            if code == 404:
                return None, f"FAILED model-not-found HTTP{code}"
            if code == 429:
                time.sleep(4)
                continue
            if code >= 500:
                time.sleep(2)
                continue
            return None, f"FAILED HTTP{code}"
        except Exception as e:
            name = type(e).__name__
            is_timeout = ("Timeout" in name) or ("timed out" in str(e).lower())
            outcomes.append("TIMEOUT" if is_timeout else name)
            time.sleep(2)
            continue

    if all(o == "TIMEOUT" for o in outcomes) and outcomes:
        return None, "TIMEOUT_INCONCLUSIVE"
    return None, "FAILED " + ",".join(outcomes)


# ──────────────────────────────────────────────────────────────
# 解析模型输出（容错：允许 markdown 包裹、前后废话）
# ──────────────────────────────────────────────────────────────
def parse_verdict(text):
    if not text:
        return None
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return None
    try:
        obj = json.loads(m.group())
    except json.JSONDecodeError:
        return None
    verdict = str(obj.get("verdict", "")).strip().lower()
    if verdict not in VALID_VERDICTS:
        return None
    conf = obj.get("confidence")
    try:
        conf = float(conf) if conf is not None else None
    except (TypeError, ValueError):
        conf = None
    return {
        "verdict": verdict,
        "confidence": conf,
        "reasoning": str(obj.get("reasoning", ""))[:300],
    }


# ──────────────────────────────────────────────────────────────
# 断点续传：读取已完成的 (case_id, model)
# ──────────────────────────────────────────────────────────────
def load_done(path):
    done = set()
    if path.exists():
        with io.open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                    done.add((r["case_id"], r["model"]))
                except (json.JSONDecodeError, KeyError):
                    continue
    return done


# ──────────────────────────────────────────────────────────────
# 主评估循环
# ──────────────────────────────────────────────────────────────
def evaluate(models, limit, timeout, max_retries, cases_path, out_path):
    cases = json.loads(io.open(cases_path, encoding="utf-8").read())["cases"]
    if limit:
        cases = cases[:limit]

    cfg = load_prism_config()
    print(f"网关: {cfg['base_url']}")
    print(f"模型: {', '.join(models)}")
    print(f"用例: {len(cases)}  (每个模型 {len(cases)} 次调用)")
    print(f"考卷: {cases_path}")
    print(f"输出: {out_path}")
    print("=" * 60)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    done = load_done(out_path)
    if done:
        print(f"断点续传：已完成 {len(done)} 条，将跳过\n")

    out = io.open(out_path, "a", encoding="utf-8")
    total = len(cases) * len(models)
    n = 0
    t_start = time.time()

    for model in models:
        for case in cases:
            key = (case["case_id"], model)
            if key in done:
                n += 1
                continue

            source = case["mutated_source"] if case["mutated_source"] else "（无）"
            prompt = PROMPT_TEMPLATE.format(claim=case["mutated_claim"], source=source)

            raw, outcome = call_llm(cfg["base_url"], cfg["api_key"], model,
                                    prompt, timeout, max_retries)
            parsed = parse_verdict(raw)

            # 判定
            expected = case["expected_verdict"]
            if parsed is None:
                judgement = "error"
                actual_verdict = None
                actual_conf = None
            else:
                actual_verdict = parsed["verdict"]
                actual_conf = parsed["confidence"]
                judgement = "hit" if actual_verdict == expected else "miss"

            overconfident = False
            if parsed and actual_conf is not None and case.get("expected_confidence_max") is not None:
                overconfident = actual_conf > case["expected_confidence_max"]

            record = {
                "case_id": case["case_id"],
                "model": model,
                "mutation_type": case["mutation_type"],
                "expected_verdict": expected,
                "actual_verdict": actual_verdict,
                "actual_confidence": actual_conf,
                "expected_confidence_max": case.get("expected_confidence_max"),
                "judgement": judgement,
                "overconfident": overconfident,
                "outcome": outcome,
                "reasoning": parsed["reasoning"] if parsed else None,
                "ts": datetime.now().isoformat(timespec="seconds"),
            }
            out.write(json.dumps(record, ensure_ascii=False) + "\n")
            out.flush()

            n += 1
            mark = {"hit": "HIT ", "miss": "MISS", "error": "ERR "}[judgement]
            elapsed = time.time() - t_start
            rate = n / elapsed if elapsed > 0 else 0
            eta = (total - n) / rate if rate > 0 else 0
            print(f"[{n}/{total}] {mark} {case['case_id']:16s} {model:18s} "
                  f"exp={expected:20s} act={str(actual_verdict):20s} "
                  f"{outcome:8s} ETA {eta:0.0f}s")

    out.close()
    print("\n完成。结果已写入:", out_path)
    return out_path


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Claim2Value benchmark 判别力评估")
    ap.add_argument("--models", nargs="+", default=DEFAULT_MODELS,
                    help="要测的模型，默认 claude-sonnet-5")
    ap.add_argument("--limit", type=int, default=0, help="只跑前 N 个用例（调试用）")
    ap.add_argument("--timeout", type=int, default=60, help="单次请求超时秒数")
    ap.add_argument("--retries", type=int, default=3, help="失败重试次数")
    ap.add_argument("--cases", type=str, default=str(DEFAULT_CASES),
                    help="用例文件路径（默认 v2 修正版）")
    ap.add_argument("--out", type=str, default=str(DEFAULT_OUT),
                    help="结果输出路径（默认 evaluation_results_v2.jsonl）")
    args = ap.parse_args()

    evaluate(args.models, args.limit, args.timeout, args.retries,
             Path(args.cases), Path(args.out))
