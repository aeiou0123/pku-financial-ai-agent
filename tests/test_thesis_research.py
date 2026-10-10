"""Source anchoring, time windows, scope and interrupted research, using synthetic text."""
from datetime import date
import json
from types import SimpleNamespace

import pytest

from src.harness.api import APIError
from src.harness.documents import parse
from src.harness.research import document_scope, retrieve, validate_plan, anchor_assessment, review_thesis, plan_thesis
from src.harness.store import Run

CONDITION = {"id": "C1", "type": "capacity", "label": "扩产已投产并能兑现销量", "query_terms": ["产能", "延期"]}


def corpus():
    return [parse("公司甲设计产能100万台/年。项目延期，尚未投产。".encode(), "capacity.txt"),
            parse("公司甲客户名单包含公司乙；未披露订单金额。".encode(), "customer.txt")]


def scope(docs=None):
    docs = docs or corpus()
    return document_scope(docs, [{"name": d["name"], "published_at": "2026-01-01", "confirmed": True,
                                   "company": "公司甲", "product": "减速器"} for d in docs], date(2026, 10, 10))


def client(responder, budget=10):
    value = SimpleNamespace(api_key="synthetic_private_key_123", model="mock", base_url="http://localhost/v1",
                            protocol="openai", max_output_tokens=8192, calls=0, usage=[])
    def call(system, payload):
        if value.calls >= budget:
            raise APIError("quota")
        value.calls += 1
        return responder(system, payload)
    value.json = call
    return value


def response(pieces):
    piece = next(p for p in pieces if "100万台" in p["text"])
    return {"evidence": [{"piece_id": piece["piece_id"], "quote": "设计产能100万台/年", "stance": "supports", "fact_type": "forecast", "explanation": "设计上限，不是实际销量"},
                         {"piece_id": piece["piece_id"], "quote": "项目延期，尚未投产", "stance": "contradicts", "fact_type": "historical", "explanation": "投产条件未兑现"}],
            "missing": ["本次材料未覆盖实际达产数据"], "conclusion": "材料存在限制条件，需核对。",
            "parameter_candidates": [{"evidence_index": 0, "key": "annual_capacity", "value_text": "100", "unit": "万台/年", "period": ""}]}


def test_scope_unknown_future_unconfirmed_dates_do_not_enter_historical_review():
    docs = [parse(b"text", f"{i}.txt") for i in range(4)]
    metadata = [{"name": "0.txt", "published_at": "2026-01-01", "confirmed": True},
                {"name": "1.txt", "published_at": "", "confirmed": True},
                {"name": "2.txt", "published_at": "2027-01-01", "confirmed": True},
                {"name": "3.txt", "published_at": "2026-01-01", "confirmed": False}]
    result = document_scope(docs, metadata, date(2026, 10, 10))
    assert len(result["eligible"]) == 1 and len(result["excluded"]) == 3
    assert result["eligible"][0]["metadata_status"].startswith("operator_declaration")


def test_retrieval_represents_both_files_and_reports_actual_coverage():
    pieces, coverage = retrieve(corpus(), scope(), ["产能"])
    assert len({p["source_file"] for p in pieces}) == 2
    assert any("尚未投产" in p["text"] for p in pieces)
    assert coverage["selected_characters"] == sum(len(p["text"]) for p in pieces)
    assert "not_full" in coverage["method"]


def test_support_and_counterevidence_stay_candidates_with_explicit_parameter_link():
    pieces, _ = retrieve(corpus(), scope(), ["产能"])
    result = anchor_assessment(response(pieces), pieces, CONDITION)
    assert result["status"] == "conflicting_candidates"
    assert result["counts"] == {"supports": 1, "contradicts": 1}
    parameter = result["parameter_candidates"][0]
    assert parameter["evidence_id"] == result["evidence"][0]["id"]
    assert parameter["fact_type"] == "forecast" and "confirmation" in parameter["status"]


@pytest.mark.parametrize("edit", ["quote", "piece", "parameter_value", "parameter_index"])
def test_fabricated_citation_or_parameter_is_rejected(edit):
    pieces, _ = retrieve(corpus(), scope(), ["产能"])
    data = response(pieces)
    if edit == "quote":
        data["evidence"][0]["quote"] = "已实现100万台订单"
    elif edit == "piece":
        data["evidence"][0]["piece_id"] = "invented"
    elif edit == "parameter_value":
        data["parameter_candidates"][0]["value_text"] = "900"
    else:
        data["parameter_candidates"][0]["evidence_index"] = 99
    result = anchor_assessment(data, pieces, CONDITION)
    assert not result["parameter_candidates"] and result["rejected"]


def test_empty_in_window_material_does_not_call_model_or_claim_absence_of_real_orders(tmp_path):
    run = Run(tmp_path, "research", [])
    no_data = {"eligible": [], "excluded": scope()["eligible"], "cutoff": "2020-01-01"}
    api = client(lambda *args: pytest.fail("must not call model"))
    result = review_thesis(run, api, {"conditions": [CONDITION]}, corpus(), no_data, {"question": "扩产？"})
    assert api.calls == 0 and not result["assessments"][0]["evidence"]
    assert result["complete"] and "require_human" in result["review_status"]


def test_resume_preserves_completed_condition_without_repaying(tmp_path):
    run = Run(tmp_path, "research", [])
    plan = {"conditions": [CONDITION, {**CONDITION, "id": "C2"}]}
    responder = lambda system, payload: response(payload["pieces"])
    first = client(responder, budget=1)
    with pytest.raises(APIError, match="quota"):
        review_thesis(run, first, plan, corpus(), scope(), {"question": "扩产？"})
    assert run.metadata["status"] == "thesis_review_interrupted"
    assert len(json.loads((run.path / "outputs/thesis_partial.json").read_text(encoding="utf-8"))["assessments"]) == 1
    second = client(responder)
    result = review_thesis(run, second, plan, corpus(), scope(), {"question": "扩产？"})
    assert second.calls == 1 and result["complete"] and len(result["assessments"]) == 2


def test_plan_cached_and_schema_rejects_arbitrary_tools(tmp_path):
    run = Run(tmp_path, "research", [])
    api = client(lambda *args: {"conditions": [CONDITION]})
    first = plan_thesis(run, api, "扩产能否兑现？", "公司甲", "减速器", scope())
    assert plan_thesis(run, api, "扩产能否兑现？", "公司甲", "减速器", scope()) == first
    assert api.calls == 1
    with pytest.raises(ValueError):
        validate_plan({"conditions": [CONDITION], "python": "run code"})
