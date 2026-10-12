import io
import pytest
from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject
from src.harness.documents import parse, page_selection, digest
from src.harness.intake import parse_files


def original():
    # Real text pages, so coverage and original page locators can be inspected.
    stream = io.BytesIO()
    writer = PdfWriter()
    for number in range(1, 5):
        page = writer.add_blank_page(width=612, height=792)
        font = DictionaryObject({NameObject('/Type'):NameObject('/Font'),
                                 NameObject('/Subtype'):NameObject('/Type1'),
                                 NameObject('/BaseFont'):NameObject('/Helvetica')})
        page[NameObject('/Resources')] = DictionaryObject({NameObject('/Font'):
            DictionaryObject({NameObject('/F1'):writer._add_object(font)})})
        content = DecodedStreamObject()
        content.set_data(f'BT /F1 12 Tf 50 700 Td (Original page {number}) Tj ET'.encode())
        page[NameObject('/Contents')] = writer._add_object(content)
    writer.write(stream)
    return stream.getvalue()


def test_selection_preserves_original_bytes_and_page_locators():
    raw = original()
    doc = parse(raw, 'annual.pdf', pdf_pages='1,3-4,3')
    assert [p['locator'] for p in doc['parts']] == ['page:1', 'page:3', 'page:4']
    assert doc['sha256'] == digest(raw)
    assert doc['total_units'] == 4 and doc['parsed_units'] == 3
    assert doc['coverage'] == 'partial' and doc['warnings']
    assert doc['parse_limits']['pdf_pages'] == [1, 3, 4]
    assert parse_files([('annual.pdf',raw)], pdf_pages={'annual.pdf':'2'})[0][0]['parts'][0]['locator'] == 'page:2'


@pytest.mark.parametrize('value', ['0', '3-1', '1,', '1-1000000', '-1', '1.5', '1/3'])
def test_bad_selection_is_rejected(value):
    with pytest.raises(ValueError, match='PDF页码'):
        page_selection(value)


def test_out_of_range_and_non_pdf_not_silently_ignored():
    with pytest.raises(ValueError, match='总页数'):
        parse(original(), 'annual.pdf', pdf_pages='5')
    with pytest.raises(ValueError, match='仅适用于PDF'):
        parse(b'text', 'report.txt', pdf_pages='1')
    assert page_selection('') is None
    assert page_selection('1， 2-3') == [1,2,3]


def test_confirmed_old_candidate_does_not_authorize_changed_candidate(monkeypatch):
    from pathlib import Path
    from types import SimpleNamespace
    import streamlit as st
    from streamlit.testing.v1 import AppTest
    from src.financial_intake import FIELDS
    raw = original()
    monkeypatch.setattr(st, 'file_uploader', lambda *a, **k: [SimpleNamespace(name='annual.pdf', getvalue=lambda: raw)])
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1]/'harness_app.py'), default_timeout=25)
    app.session_state['desk_page'] = '工作区'
    app.session_state['desk_task'] = '财务整理与盈利解释'
    app.session_state['task_text'] = '核查合成测试数字'
    app.run()
    row = dict.fromkeys(FIELDS, '')
    row.update(company='Synthetic', metric_original='收入', value_original='100')
    app.session_state['candidates'] = [row]
    app.session_state['extraction_done'] = True
    app.run()
    confirm = next(c for c in app.checkbox if c.label.startswith('我已对照原件'))
    confirm.set_value(True)
    next(b for b in app.button if b.label=='校验并生成财务成果').click().run()
    # Invalid synthetic fields are rejected, but the checked attestation is saved.
    assert next(c for c in app.checkbox if c.label.startswith('我已对照原件')).value
    app.session_state['candidates'] = [{**row, 'value_original':'200'}]
    app.run()
    assert not app.exception
    assert not next(c for c in app.checkbox if c.label.startswith('我已对照原件')).value
