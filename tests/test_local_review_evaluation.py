import pytest
from src.review_session import run_review
from scripts.evaluate_local_review import aggregate


@pytest.mark.parametrize("claim_term,source_term", [
    ("扣非净利润", "扣非后净利润"), ("扣非后净利润", "扣非净利润")])
def test_profit_wording_alias_is_not_a_conflict(claim_term, source_term):
    claim, source = f"公司{claim_term}为47.31亿元", f"年报：公司{source_term}为47.31亿元"
    result = run_review(claim, source)
    assert result['verification']['verdict'] == 'abstain'
    assert result['verification']['rule_flags'] == []
    assert result['source'] == source
    assert result['financial']['status'] == 'skipped'


def test_profit_alias_keeps_real_accounting_distinction():
    result = run_review('公司归母净利润为47.31亿元', '年报：公司扣非后净利润为47.31亿元')
    assert result['verification']['verdict'] == 'definition_mismatch'


def test_family_macro_does_not_count_many_mutations_as_independent_families():
    rows = [{"case_id": str(i), "family": "a", "category": "mutated", "expected": "refuted", "actual": "refuted"} for i in range(9)]
    rows.append({"case_id": "b", "family": "b", "category": "mutated", "expected": "refuted", "actual": "abstain"})
    result = aggregate(rows)
    assert result['exact_rate'] == 0.9
    assert result['family_macro_rate'] == 0.5
    with pytest.raises(ValueError, match='Duplicate'):
        aggregate(rows + [rows[0]])
