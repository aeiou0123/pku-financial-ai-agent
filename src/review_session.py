"""Offline review sessions: custom evidence checks never inherit demo valuations."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from urllib.parse import urlsplit

from src.workflow import _rule_only_verification, run_financial_chain

ROOT = Path(__file__).resolve().parent.parent
MAX_CLAIM = 4000
MAX_SOURCE = 60000


def demo_cases():
    fixture = json.loads((ROOT / "data/processed/local_demo_fixture.json").read_text(encoding="utf-8"))
    bank = json.loads((ROOT / "data/processed/claim_bank_filled.json").read_text(encoding="utf-8"))
    claims = bank if isinstance(bank, list) else bank["claims"]
    sh = next(c for c in claims if c["claim_id"] == "SH_004")
    ev = sh["evidence_list"][0]
    return {
        "绿的谐波 · 减重声明": {
            "case_id": fixture["case_id"], "company": fixture["company"],
            "claim": fixture["claim"], "source": fixture["evidence"]["source_text"],
            "source_url": fixture["evidence"]["source_url"],
            "source_locator": fixture["evidence"]["source_locator"],
            "evidence_status": fixture["evidence"]["extraction_status"],
            "limitations": fixture["limitations"],
            "chain_options": {"target_company": fixture["company"]},
        },
        "双环传动/环动科技 · 客户覆盖": {
            "case_id": "SH_004_LOCAL", "company": "双环传动/环动科技",
            "claim": sh["claim_text"], "source": ev["source"] + "\n" + ev["excerpt"],
            "source_url": sh["source_url"], "source_locator": ev["locator"],
            "evidence_status": "仓库历史人工标注；本次未重新核对原PDF",
            "limitations": sh["definition_issues"],
            "chain_options": {
                "target_company": "双环传动/环动科技",
                "model_inputs_csv": ROOT / "data/processed/shuanghuan_model_inputs.csv",
                "ontology_path": ROOT / "data/processed/tech_to_economics_ontology_shuanghuan.json",
            },
        },
    }


def safe_source_url(value):
    """Only expose HTTP(S) links; nothing is fetched or authenticated here."""
    value = value.strip()
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise ValueError("来源链接不能包含换行或控制字符")
    parsed = urlsplit(value)
    if value and (parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.username or parsed.password):
        raise ValueError("来源链接须为不含账号密码的完整 HTTP(S) URL")
    return value


def run_review(claim="", source="", source_url="", source_locator="", *, demo_name=None):
    started = perf_counter()
    if demo_name is not None:
        case = demo_cases()[demo_name]
        claim, source = case["claim"], case["source"]
        source_url, source_locator = case["source_url"], case["source_locator"]
    else:
        case = None
    claim, source = claim.strip(), source.strip()
    if not claim:
        raise ValueError("请先填写要核查的声明")
    if len(claim) > MAX_CLAIM or len(source) > MAX_SOURCE:
        raise ValueError("声明最多4000字，证据原文最多60000字")
    source_url = safe_source_url(source_url)
    if case:
        result = run_financial_chain(claim, source, local_only=True, **case["chain_options"])
    else:
        state = _rule_only_verification(claim, source)
        verification = {key: state.get(key) for key in (
            "verdict", "confidence", "verdict_source", "rule_flags", "trust_score", "reasoning", "report"
        )}
        reason = "自定义输入尚未绑定经核对的公司参数和财务假设，仅输出规则核查，不生成估值"
        result = {
            "claim": claim, "source": source, "verification": verification,
            "gate": {"passed": False, "reason": reason},
            "engineering": None, "economics": None, "causal": None,
            "financial": {"status": "skipped", "reason": reason, "scenarios": {}},
            "errors": [], "report_markdown": verification["report"],
        }
    result["review_session"] = {
        "mode": "preset_scenario_demo" if case else "custom_rule_review",
        "case_id": case["case_id"] if case else None,
        "company": case["company"] if case else None,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "elapsed_ms": round((perf_counter() - started) * 1000, 3),
        "external_api_calls": 0,
        "source_url": source_url, "source_locator": source_locator.strip(),
        "source_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
        "evidence_status": case["evidence_status"] if case else "用户输入，未核对原件",
        "financial_scope": "固定工程参数与财务假设的敏感性示例，非本条声明的已识别因果效应" if case else "未生成",
        "limitations": (case["limitations"] if case else []) + [
            "本地规则未发现异常不代表声明成立；此模式不调用大模型或实时检索",
            "来源等级由文本规则推断，不代表原件已认证；链接与页码仅记录，不自动核验",
        ],
    }
    return result


def review_markdown(result):
    session = result["review_session"]
    lines = ["# Claim2Value 核查记录", "", f"时间（UTC）：{session['created_at_utc']}",
             f"模式：{session['mode']}", f"声明：{result['claim']}",
             f"来源链接：{session['source_url']}", f"定位：{session['source_locator']}",
             f"原文 SHA-256：{session['source_sha256']}",
             f"证据状态：{session['evidence_status']}", f"财务适用范围：{session['financial_scope']}",
             f"本次计算耗时：{session['elapsed_ms']} ms；外部API调用：0", "", "## 限制", ""]
    lines.extend("- " + item for item in session["limitations"])
    lines.extend(["", "## 证据原文", "", result["source"], "", "## 分析输出", "", result["report_markdown"]])
    return "\n".join(lines)
