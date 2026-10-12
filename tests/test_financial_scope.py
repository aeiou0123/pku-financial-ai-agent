import json

from src.harness.api import ModelClient
from src.harness.financial import extract, scope_conflict, statement_marks
from src.harness.store import Run
from tests.test_harness import local_api  # noqa: F401  (shared mock server fixture)


def _statement_doc(pages):
    return {"name": "report.pdf", "source_file": "source_report.pdf", "sha256": "0" * 64, "bytes": 1,
            "parts": [{"locator": locator, "text": text} for locator, text in pages], "warnings": [],
            "total_units": 120, "parsed_units": len(pages), "characters": sum(len(t) for _, t in pages),
            "coverage": "partial"}


PAGES = [("page:112", "合并利润表\n2024 年 1—12 月\n一、营业收入 100 90\n"),
         ("page:113", "三、利润总额 50 40\n母公司利润表\n一、营业收入 80 70\n"),
         ("page:114", "三、利润总额 30 20\n四、净利润 25 18\n"),
         ("page:116", "四、净利润 25 18\n")]


def _check(locator, quote, scope):
    doc = _statement_doc(PAGES)
    marks = statement_marks([doc])
    text = dict(PAGES)[locator]
    return scope_conflict({"statement_scope": scope, "quote": quote}, text, marks[(doc["source_file"], locator)])


def test_parent_statement_continued_on_next_page_is_not_consolidated():
    assert _check("page:114", "三、利润总额 30 20", "consolidated") == "parent"
    assert _check("page:114", "三、利润总额 30 20", "parent") is None
    assert _check("page:113", "一、营业收入 80 70", "consolidated") == "parent"
    assert _check("page:113", "三、利润总额 50 40", "consolidated") is None
    assert _check("page:112", "一、营业收入 100 90", "consolidated") is None


def test_unknown_or_ambiguous_heading_is_not_rejected():
    # Page 116 does not follow 114 directly, so no heading is carried and nothing is decided.
    assert _check("page:116", "四、净利润 25 18", "consolidated") is None
    assert scope_conflict({"statement_scope": "", "quote": "x"}, "x", []) is None
    narrative = [("page:1", "子公司损益在合并利润表中列示。\n营业收入 5 4\n")]
    doc = _statement_doc(narrative)
    unit = statement_marks([doc])[(doc["source_file"], "page:1")]
    assert unit == [] and scope_conflict({"statement_scope": "parent", "quote": "营业收入 5 4"}, narrative[0][1], unit) is None


def test_extract_sends_title_in_effect_and_rejects_scope_conflict(tmp_path, local_api):
    url, handler = local_api
    handler.requests.clear()
    doc = _statement_doc(PAGES[:3])
    handler.content = {"records": [
        {"source_file": doc["source_file"], "source_locator": "page:114", "quote": "三、利润总额 30 20",
         "statement_scope": "consolidated", "canonical_metric": "pretax_profit", "report_period": "2024-12-31",
         "value_original": "30"},
        {"source_file": doc["source_file"], "source_locator": "page:113", "quote": "三、利润总额 50 40",
         "statement_scope": "consolidated", "canonical_metric": "pretax_profit", "report_period": "2024-12-31",
         "value_original": "50"}]}
    run = Run(tmp_path, "financial", [("report.pdf", b"x")])
    accepted = extract(run, [doc], "pretax profit", ModelClient(url, "mock", "credential_32_chars_for_test_only"))
    assert [row["value_original"] for row in accepted] == ["50"]
    rejected = json.loads((run.path / "outputs/rejected_candidates.json").read_text(encoding="utf-8"))
    assert rejected[0]["reason"] == "statement_scope_conflicts_with_heading"
    assert rejected[0]["heading_scope"] == "parent" and rejected[0]["value_original"] == "30"
    pieces = json.loads(handler.requests[0]["body"]["messages"][-1]["content"])["pieces"]
    titles = {piece["source_locator"]: piece.get("statement_title_in_effect") for piece in pieces}
    assert titles == {"page:112": "合并利润表", "page:113": "合并利润表", "page:114": "母公司利润表"}
