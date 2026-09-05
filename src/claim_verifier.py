"""
claim_verifier.py — Claim2Value LLM 验证引擎
==============================================

整合 state_verifier（规则层）+ evidence_ledger（证据层）+ LLM（语义层），
输出结构化验证结果。

架构（两层防线）：
    ┌──────────────────────────────────────────┐
    │            Claim + Source                │
    └──────────────┬───────────────────────────┘
                   │
    ┌──────────────▼───────────────────────────┐
    │  Layer 1: StateVerifier (确定性规则)      │
    │  - 口径偷换检测                           │
    │  - 限定词缺失检测                         │
    │  - 数值矛盾检测                           │
    │  - 来源降级检测                           │
    │  → verdict_override (可能直接给出结论)    │
    └──────────────┬───────────────────────────┘
                   │
    ┌──────────────▼───────────────────────────┐
    │  Layer 2: LLM (语义判断)                  │
    │  - 规则层未覆盖的语义不一致               │
    │  - 证据充分性判断                         │
    │  - abstain 判断                          │
    │  → verdict + confidence + reasoning       │
    └──────────────┬───────────────────────────┘
                   │
    ┌──────────────▼───────────────────────────┐
    │  Merge: 合并两层结果                      │
    │  - 规则层 verdict 优先（确定性 > 概率性） │
    │  - 规则层调整 LLM confidence              │
    │  - 输出最终 verdict + flags               │
    └──────────────────────────────────────────┘

设计原则：
    1. 规则层优先：如果 state_verifier 检出口径偷换，直接判 definition_mismatch，
       不需要 LLM 再判断——因为 LLM 在这上面只有 12-35% 准确率。
    2. 互补不替代：规则层不覆盖的场景（如语义矛盾、证据充分性）仍交给 LLM。
    3. 可审计：每条 verdict 都附带规则层 flags 和 LLM reasoning，方便回溯。

用法：
    from src.claim_verifier import ClaimVerifier

    verifier = ClaimVerifier(model="claude-sonnet-5")
    result = verifier.verify(claim, source)
    # result.verdict → "definition_mismatch"
    # result.confidence → 0.3
    # result.reasoning → "..."
    # result.rule_flags → ["口径偷换：..."]
    # result.llm_verdict → "supported" (LLM 原始判断，被规则层覆盖)
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
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any

from src.state_verifier import StateVerifier, VerificationResult
from src.evidence_ledger import EvidenceLedger, EvidenceLevel

# ============================================================
# 验证结果
# ============================================================

@dataclass
class VerificationOutput:
    """ClaimVerifier 的最终输出"""
    verdict: str               # 最终 verdict
    confidence: float          # 最终 confidence（0.0-1.0）
    reasoning: str             # 推理过程
    # 规则层
    rule_verdict: Optional[str] = None    # 规则层建议的 verdict
    rule_flags: List[str] = field(default_factory=list)
    rule_result: Optional[Dict] = None    # 完整的规则层结果
    # LLM 层
    llm_verdict: Optional[str] = None     # LLM 原始 verdict
    llm_confidence: Optional[float] = None
    llm_reasoning: Optional[str] = None
    # 证据层
    trust_score: float = 0.0
    evidence_summary: Optional[Dict] = None
    # 元数据
    source_used: bool = True             # 是否有证据
    verdict_source: str = "llm"          # "rule" / "llm" / "merged"
    model: str = ""
    elapsed_ms: int = 0

    def to_dict(self) -> Dict:
        return {
            "verdict": self.verdict,
            "confidence": round(self.confidence, 3),
            "reasoning": self.reasoning,
            "rule_verdict": self.rule_verdict,
            "rule_flags": self.rule_flags,
            "llm_verdict": self.llm_verdict,
            "llm_confidence": round(self.llm_confidence, 3) if self.llm_confidence is not None else None,
            "llm_reasoning": self.llm_reasoning,
            "trust_score": round(self.trust_score, 3),
            "source_used": self.source_used,
            "verdict_source": self.verdict_source,
            "model": self.model,
            "elapsed_ms": self.elapsed_ms,
        }


# ============================================================
# ClaimVerifier
# ============================================================

VALID_VERDICTS = {
    "supported", "refuted", "partially_supported",
    "definition_mismatch", "low_confidence", "abstain",
}

_SSL = ssl.create_default_context()
_SSL.check_hostname = False
_SSL.verify_mode = ssl.CERT_NONE

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE = REPO_ROOT.parent


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
3. 特别注意口径一致性：额定扭矩 vs 峰值扭矩、归母净利润 vs 扣非净利润、
   毛利率 vs 净利率 是不同概念，不可混用。
4. 特别注意限定条件：如果证据中提到"同等出力""同尺寸"等条件，
   而 claim 中缺失这些条件，应选 "partially_supported"。
5. 只输出一个 JSON 对象，不要输出任何其他文字。

输出格式：
{{"verdict": "...", "confidence": 0.0, "reasoning": "..."}}"""


def load_prism_config() -> dict:
    """加载 Prism 网关配置（复用 evaluate.py 的逻辑）"""
    p = WORKSPACE / "prism_config.json"
    if p.exists():
        cfg = json.loads(io.open(p, encoding="utf-8-sig").read())
        return {"base_url": cfg["base_url"], "api_key": cfg["api_key"]}

    p = Path.home() / ".workbuddy" / "models.json"
    if p.exists():
        models = json.loads(io.open(p, encoding="utf-8").read())
        for m in models:
            if m.get("id") == "claude-sonnet-5":
                base = m["url"].rsplit("/chat/completions", 1)[0]
                return {"base_url": base, "api_key": m["apiKey"]}
        for m in models:
            if "image" not in m.get("id", ""):
                base = m["url"].rsplit("/chat/completions", 1)[0]
                return {"base_url": base, "api_key": m["apiKey"]}

    raise RuntimeError(
        "找不到 Prism 配置。请先运行 Test-PrismGateway.ps1 -AutoLoadKey -SaveConfig"
    )


def call_llm(base_url, api_key, model, prompt, timeout=60, max_retries=3):
    """调用 LLM，返回 (raw_text, outcome)"""
    url = f"{base_url}/chat/completions"
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 400,
        "temperature": 0.0,
    }).encode("utf-8")

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
            if e.code in (401, 403, 404):
                return None, f"FAILED HTTP{e.code}"
            if e.code == 429:
                time.sleep(4)
                continue
            if e.code >= 500:
                time.sleep(2)
                continue
            return None, f"FAILED HTTP{e.code}"
        except Exception as e:
            time.sleep(2)
            continue

    return None, "FAILED"


def parse_verdict(text):
    """解析 LLM 输出"""
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
        "reasoning": str(obj.get("reasoning", ""))[:500],
    }


class ClaimVerifier:
    """
    两层验证引擎：规则层（StateVerifier）+ 语义层（LLM）。

    规则层优先：如果检出确定性错误（口径偷换/数值篡改/来源降级），
    直接覆盖 LLM 的 verdict。否则用 LLM 的语义判断。
    """

    def __init__(
        self,
        model: str = "claude-sonnet-5",
        timeout: int = 60,
        max_retries: int = 3,
    ):
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self.state_verifier = StateVerifier()
        self._llm_config = None  # lazy load

    @property
    def llm_config(self):
        if self._llm_config is None:
            self._llm_config = load_prism_config()
        return self._llm_config

    def verify(self, claim: str, source: str) -> VerificationOutput:
        """
        验证一条 claim。

        Args:
            claim: claim 文本
            source: 证据来源文本

        Returns:
            VerificationOutput
        """
        t_start = time.time()
        output = VerificationOutput(
            verdict="abstain",
            confidence=0.0,
            reasoning="",
            model=self.model,
        )

        # ── 证据层：构建证据账本 ──
        ledger = EvidenceLedger()
        if source and source.strip():
            ledger.add_from_text(source)
        output.trust_score = ledger.trust_score()
        output.evidence_summary = ledger.summary()
        output.source_used = not ledger.is_empty

        # ── 规则层：StateVerifier ──
        rule_result = self.state_verifier.verify(claim, source)
        output.rule_verdict = rule_result.verdict_override
        output.rule_flags = rule_result.flags
        output.rule_result = rule_result.to_dict()

        # ── 无证据 → 直接 abstain，跳过 LLM ──
        if not output.source_used:
            output.verdict = "abstain"
            output.confidence = 0.1
            output.reasoning = "证据缺失，拒绝给出结论（规则层直接判定）"
            output.verdict_source = "rule"
            output.elapsed_ms = int((time.time() - t_start) * 1000)
            return output

        # ── LLM 层：语义判断 ──
        prompt = PROMPT_TEMPLATE.format(claim=claim, source=source)
        raw, outcome = call_llm(
            self.llm_config["base_url"],
            self.llm_config["api_key"],
            self.model,
            prompt,
            self.timeout,
            self.max_retries,
        )
        parsed = parse_verdict(raw)

        if parsed:
            output.llm_verdict = parsed["verdict"]
            output.llm_confidence = parsed["confidence"]
            output.llm_reasoning = parsed["reasoning"]
        else:
            output.llm_verdict = None
            output.llm_reasoning = f"LLM 调用失败: {outcome}"

        # ── 合并两层结果 ──
        if rule_result.verdict_override:
            # 规则层检出确定性问题 → 覆盖 LLM verdict
            output.verdict = rule_result.verdict_override
            output.verdict_source = "rule"
            # confidence = LLM confidence + 规则层调整（下限 0.05，上限 0.95）
            base_conf = output.llm_confidence if output.llm_confidence is not None else 0.5
            output.confidence = max(0.05, min(0.95, base_conf + rule_result.confidence_adjustment))
            # reasoning 合并
            rule_explain = "; ".join(rule_result.flags)
            llm_explain = output.llm_reasoning or ""
            output.reasoning = f"[规则层] {rule_explain}"
            if llm_explain:
                output.reasoning += f" | [LLM] {llm_explain}"
        elif parsed:
            # 规则层未检出问题 → 用 LLM verdict
            output.verdict = parsed["verdict"]
            output.confidence = parsed["confidence"] if parsed["confidence"] is not None else 0.5
            output.reasoning = parsed["reasoning"]
            output.verdict_source = "llm"
            # 如果证据可信度低，适当降低 confidence
            if output.trust_score < 0.3:
                output.confidence = max(0.05, output.confidence - 0.2)
                output.reasoning += " | [证据层] 证据可信度低，confidence 已下调"
        else:
            # LLM 失败且规则层也没检出 → 标记为 error
            output.verdict = "error"
            output.confidence = 0.0
            output.reasoning = f"LLM 调用失败且规则层未检出问题: {outcome}"
            output.verdict_source = "error"

        output.elapsed_ms = int((time.time() - t_start) * 1000)
        return output

    def verify_batch(
        self,
        cases: List[Dict],
        show_progress: bool = True,
    ) -> List[Dict]:
        """
        批量验证 benchmark 用例。

        Args:
            cases: [{"case_id": ..., "mutated_claim": ..., "mutated_source": ...}, ...]
            show_progress: 是否打印进度

        Returns:
            [{"case_id": ..., "result": VerificationOutput.to_dict(), ...}, ...]
        """
        results = []
        total = len(cases)
        for i, case in enumerate(cases, 1):
            claim = case.get("mutated_claim", "")
            source = case.get("mutated_source", "")
            result = self.verify(claim, source)

            # 对比 expected_verdict
            expected = case.get("expected_verdict", "")
            actual = result.verdict
            hit = actual == expected

            row = {
                "case_id": case.get("case_id", ""),
                "mutation_type": case.get("mutation_type", ""),
                "expected_verdict": expected,
                "actual_verdict": actual,
                "judgement": "hit" if hit else "miss",
                "verdict_source": result.verdict_source,
                "confidence": round(result.confidence, 3),
                "rule_flags": result.rule_flags,
                "llm_verdict": result.llm_verdict,
                "trust_score": round(result.trust_score, 3),
                "elapsed_ms": result.elapsed_ms,
                "reasoning": result.reasoning[:200],
            }
            results.append(row)

            if show_progress:
                mark = "HIT " if hit else "MISS"
                rule_tag = "[R]" if result.verdict_source == "rule" else "[L]"
                print(f"[{i}/{total}] {mark} {rule_tag} {case.get('case_id',''):16s} "
                      f"exp={expected:20s} act={actual:20s} "
                      f"flags={len(result.rule_flags)} {result.elapsed_ms}ms")

        return results


# ============================================================
# CLI 入口
# ============================================================

if __name__ == "__main__":
    import sys

    ap = argparse.ArgumentParser(description="Claim2Value 验证引擎")
    ap.add_argument("--model", default="claude-sonnet-5", help="LLM 模型名")
    ap.add_argument("--cases", default=str(REPO_ROOT / "benchmarks" / "claim_verification_v2.json"),
                    help="benchmark 用例文件")
    ap.add_argument("--limit", type=int, default=0, help="只跑前 N 个用例（调试用）")
    ap.add_argument("--out", default="", help="结果输出路径")
    ap.add_argument("--no-llm", action="store_true", help="只跑规则层，不调 LLM（快速验证）")
    args = ap.parse_args()

    # 加载用例
    cases_path = Path(args.cases)
    if not cases_path.exists():
        print(f"用例文件不存在: {cases_path}")
        sys.exit(1)

    data = json.loads(io.open(cases_path, encoding="utf-8").read())
    cases = data["cases"]
    if args.limit:
        cases = cases[:args.limit]

    print(f"用例: {len(cases)}  模型: {args.model}  规则层only: {args.no_llm}")
    print("=" * 70)

    if args.no_llm:
        # 只跑规则层
        verifier = StateVerifier()
        hit = 0
        miss = 0
        for i, case in enumerate(cases, 1):
            claim = case.get("mutated_claim", "")
            source = case.get("mutated_source", "")
            r = verifier.verify(claim, source)

            # 规则层无覆盖时的 fallback：
            # - 无证据 → abstain（规则层 verify 已标记 flags 但不设 verdict_override）
            # - 有证据但无规则检出 → supported（规则层未发现异常）
            if r.verdict_override:
                actual = r.verdict_override
            elif not source or not source.strip():
                actual = "abstain"
            else:
                actual = "supported"

            expected = case.get("expected_verdict", "")
            is_hit = actual == expected
            if is_hit:
                hit += 1
            else:
                miss += 1
            mark = "HIT " if is_hit else "MISS"
            print(f"[{i}/{len(cases)}] {mark} {case.get('case_id',''):16s} "
                  f"exp={expected:20s} act={actual:20s} flags={len(r.flags)}")

        total = hit + miss
        print(f"\n规则层准确率: {hit}/{total} = {hit/total*100:.1f}%" if total else "无有效用例")

    else:
        # 完整两层验证
        verifier = ClaimVerifier(model=args.model)
        results = verifier.verify_batch(cases)

        # 统计
        hit = sum(1 for r in results if r["judgement"] == "hit")
        miss = sum(1 for r in results if r["judgement"] == "miss")
        total = hit + miss
        rule_hits = sum(1 for r in results if r["verdict_source"] == "rule" and r["judgement"] == "hit")
        llm_hits = sum(1 for r in results if r["verdict_source"] == "llm" and r["judgement"] == "hit")

        print(f"\n{'=' * 70}")
        print(f"总准确率: {hit}/{total} = {hit/total*100:.1f}%")
        print(f"规则层命中: {rule_hits}  LLM 命中: {llm_hits}")

        # 按扰动类型分解
        from collections import defaultdict
        by_type = defaultdict(lambda: {"hit": 0, "miss": 0})
        for r in results:
            by_type[r["mutation_type"]][r["judgement"]] += 1

        print(f"\n按扰动类型:")
        for mtype, stats in sorted(by_type.items()):
            acc = stats["hit"] / (stats["hit"] + stats["miss"]) if (stats["hit"] + stats["miss"]) else 0
            print(f"  {mtype:25s} {acc*100:5.1f}%  ({stats['hit']}/{stats['hit']+stats['miss']})")

        # 输出结果
        if args.out:
            out_path = Path(args.out)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with io.open(out_path, "w", encoding="utf-8") as f:
                for r in results:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
            print(f"\n结果已写入: {out_path}")
