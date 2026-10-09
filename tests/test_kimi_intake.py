import copy
import hashlib
import json
import pytest
from src.kimi_intake import CLAIMS, prepare_candidates


def payload():
    return {'schema_version': 1, 'candidates': [
        {'claim_id': k, 'claim_text': v, 'status': 'not_started'} for k, v in CLAIMS.items()]}


def run(tmp_path, data):
    f = tmp_path / 'input.json'
    f.write_text(json.dumps(data, ensure_ascii=False))
    return prepare_candidates(f, tmp_path, tmp_path / 'out')


def original(tmp_path):
    # Synthetic header is intentional: this intake does not claim to parse PDFs.
    content = b'%PDF-1.7\nsynthetic provenance fixture\n'
    (tmp_path / 'original.pdf').write_bytes(content)
    data = payload()
    data['candidates'][0].update(status='read_original', file_name='original.pdf',
        sha256=hashlib.sha256(content).hexdigest(), pdf_page=1, printed_page='',
        title='合成测试，不是真实原件', excerpt='合成测试原文，不是业务证据',
        source_url='https://example.com/original.pdf')
    return data


def test_not_started_does_not_invent_evidence(tmp_path):
    r = run(tmp_path, payload())
    assert r['text_review_count'] == 0 and r['requires_human_review']
    assert not r['claim_bank_modified'] and r['external_api_calls'] == 0


def test_local_provenance_intake_does_not_certify_excerpt_or_page(tmp_path):
    r = run(tmp_path, original(tmp_path))
    assert r['text_review_count'] == 1
    assert r['records'][0]['human_review'] == 'pending'
    assert 'NOT_SOURCE_AUTHENTICATION' in r['scope']
    with pytest.raises(FileExistsError):
        prepare_candidates(tmp_path / 'input.json', tmp_path, tmp_path / 'out')


@pytest.mark.parametrize('field,value', [
    ('sha256', '0' * 64), ('file_name', '../original.pdf'),
    ('pdf_page', True), ('pdf_page', 0), ('excerpt', ''),
    ('source_url', 'javascript:bad'), ('source_url', 'https://user:password@example.com/x'),
    ('source_url', 'https://example.com/a\nb'),
    ('claim_text', '改写原始声明'),
])
def test_invalid_return_is_rejected_before_output(tmp_path, field, value):
    data = original(tmp_path)
    data['candidates'][0][field] = value
    with pytest.raises(ValueError):
        run(tmp_path, data)
    assert not (tmp_path / 'out').exists()


def test_duplicate_id_and_missing_search_scope(tmp_path):
    data = payload()
    data['candidates'][1] = copy.deepcopy(data['candidates'][0])
    with pytest.raises(ValueError):
        run(tmp_path, data)
    data = payload(); data['candidates'][0]['status'] = 'not_found'
    with pytest.raises(ValueError):
        run(tmp_path, data)
    data['candidates'][0]['search_scope'] = '实际检查指定文件，未联网'
    assert run(tmp_path, data)['text_review_count'] == 0


def test_symlink_cannot_escape_original_directory(tmp_path):
    source = tmp_path / 'sources'; source.mkdir()
    data = original(tmp_path)
    (source / 'original.pdf').symlink_to(tmp_path / 'original.pdf')
    f = tmp_path / 'input.json'; f.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        prepare_candidates(f, source, tmp_path / 'out')
    assert not (tmp_path / 'out').exists()


def test_prepared_batch_enters_existing_review_without_valuation(tmp_path):
    from src.evidence_batch import review_batch
    run(tmp_path, original(tmp_path))
    result = review_batch(tmp_path / 'out/evidence_batch.csv', tmp_path / 'rule_review')
    assert result['reviewed'] == 1 and result['invalid_input'] == 0
    review = json.loads((tmp_path / 'rule_review/GH_007.json').read_text())
    assert review['financial']['status'] == 'skipped'
    assert review['review_session']['mode'] == 'custom_rule_review'
