import json
from unittest.mock import patch

import pytest

from src.review_session import demo_cases, run_review, review_markdown


def test_custom_claim_cannot_inherit_demo_financials():
    case = next(iter(demo_cases().values()))
    with patch("src.review_session.run_financial_chain", side_effect=AssertionError("unexpected valuation")):
        result = run_review(case["claim"], case["source"], case["source_url"], "用户提供页码")
    assert result["verification"]["verdict"] == "partially_supported"
    assert result["financial"]["scenarios"] == {}
    assert not result["gate"]["passed"]
    assert result["review_session"]["evidence_status"] == "用户输入，未核对原件"
    assert "用户提供页码" in review_markdown(result)
    json.dumps(result)


def test_missing_evidence_and_no_rule_hit_abstain():
    for source in ("", "公司产品适用于机器人。"):
        result = run_review("公司产品适用于机器人。", source)
        assert result["verification"]["verdict"] == "abstain"
        assert result["financial"]["status"] == "skipped"


@pytest.mark.parametrize("name", list(demo_cases()))
def test_presets_run_correct_company_models_without_llm(name):
    with patch("src.workflow.run_verification", side_effect=AssertionError("LLM invoked")):
        result = run_review(demo_name=name)
    assert result["errors"] == []
    assert result["financial"]["status"] == "ok"
    assert len(result["financial"]["scenarios"]) == 3
    assert result["economics"]["target_company"] == result["review_session"]["company"]
    assert result["review_session"]["external_api_calls"] == 0


@pytest.mark.parametrize("url", ["javascript:alert(1)", "file:///tmp/a", "https://user:secret@example.com", "https://example.com\n/path"])
def test_source_links_cannot_expose_nonweb_or_credentials(url):
    with pytest.raises(ValueError):
        run_review("声明", "原文", url)


def test_streamlit_submit_switch_and_validation():
    from pathlib import Path
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=15).run()
    assert not at.exception
    at.button(key="run_demo").click().run()
    assert not at.exception
    assert at.session_state["review_result"]["financial"]["status"] == "ok"
    at.selectbox(key="demo_name").select("双环传动/环动科技 · 客户覆盖").run()
    at.button(key="run_demo").click().run()
    assert at.session_state["review_result"]["review_session"]["company"] == "双环传动/环动科技"
    at.radio(key="review_mode").set_value("自定义核查").run()
    at.text_area(key="custom_claim").set_value("产品适用于机器人")
    next(b for b in at.button if b.label == "核查声明").click().run()
    assert not at.exception
    assert at.session_state["review_result"]["financial"]["status"] == "skipped"
    assert len(at.get("download_button")) == 2
    at.text_area(key="custom_claim").set_value("   ")
    next(b for b in at.button if b.label == "核查声明").click().run()
    assert len(at.error) == 1
    assert "review_result" not in at.session_state
