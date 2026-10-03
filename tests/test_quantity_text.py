import pytest
from src.quantity_text import normalize_quantities, model_numeric_scope
from src.review_session import run_review
from src.state_verifier import StateVerifier


@pytest.mark.parametrize('claim,source', [
    ('产品额定扭矩为172Nm','产品手册：产品额定扭矩为0.172kNm'),
    ('产品额定扭矩为0.172kN·m','产品手册：产品额定扭矩为172N*m'),
    ('产品重量为2.5kg','产品手册：产品重量为2500g'),
    ('公司扣非净利润为47.31亿元','年报：公司扣非后净利润为473100万元'),
    ('产品年度出货1000台','公告：产品年度出货1,000台'),
    ('产品年度出货1234567.89台','公告：产品年度出货1,234,567.89台'),
    ('公司毛利率37.54%，同比下降3.60个百分点','年报：公司毛利率37.54%，同比-3.60pct'),
])
def test_equivalence_preserves_raw_evidence(claim,source):
    r=run_review(claim,source)
    assert r['verification']['verdict']=='abstain'
    assert r['source']==source and r['claim']==claim
    assert r['financial']['status']=='skipped'


@pytest.mark.parametrize('claim,source', [
    ('产品额定扭矩为172Nm','产品手册：产品额定扭矩为0.180kNm'),
    ('产品重量为2.5kg','产品手册：产品重量为2600g'),
    ('公司扣非净利润为47.31亿元','年报：公司扣非净利润为473200万元'),
    ('产品年度出货1001台','公告：产品年度出货1,000台'),
    ('产品重量为2kg','产品手册：产品重量为3kg'),
    ('公司净利润为-47.31亿元','年报：公司净利润为47.31亿元'),
    ('产品额定扭矩为172Nm','手册：产品额定扭矩为180Nm，重量172kg'),
    ('A型号额定扭矩为172Nm','产品手册：A型号额定扭矩为180Nm，B型号额定扭矩为172Nm'),
    ('A型号额定扭矩为172Nm','产品手册：B型号额定扭矩为172Nm，A型号额定扭矩为180Nm'),
])
def test_real_change_still_conflicts(claim,source):
    assert run_review(claim,source)['verification']['verdict']=='refuted'


def test_location_background_and_metric_qualifier_are_distinct():
    assert run_review('公司毛利率为30%','公告：公司毛利率为30%；公司在国内开展业务')['verification']['verdict']=='abstain'
    assert run_review('公司市场份额为30%','公告：公司国内市场份额为30%')['verification']['verdict']=='partially_supported'


def test_model_scope_preserves_reliability_and_missing_model_abstention():
    assert run_review('A型号额定扭矩为172Nm','网传：A型号额定扭矩为172Nm，B型号额定扭矩为180Nm')['verification']['verdict']=='low_confidence'
    assert run_review('A型号额定扭矩为172Nm','手册：B型号额定扭矩为180Nm')['verification']['verdict']=='abstain'


def test_repeated_model_segments_are_all_retained():
    scoped=model_numeric_scope('A型号值172','A型号值172，B型号值180，A型号值175')
    assert '172' in scoped and '175' in scoped and '180' not in scoped


def test_incomparable_dimension_does_not_create_numeric_refutation():
    r=StateVerifier().verify('产品重量为172kg','手册：产品额定扭矩为180Nm')
    assert not r.value_contradictions and r.verdict_override!='refuted'


def test_decrease_amount_is_not_negative_profit_level():
    assert normalize_quantities('公司利润下降3亿元')=='公司利润下降300000000 元'


@pytest.mark.parametrize('value',['12,34台','1,000,12台','1.000,00台','172nm','2.5kgf'])
def test_unsupported_format_is_not_normalized(value):
    assert normalize_quantities(value)==value
