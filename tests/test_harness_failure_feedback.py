"""Failed input is visible, bounded and cannot silently become complete evidence."""
import hashlib
import io
import json
import urllib.parse

import pandas as pd
import pytest
from pypdf import PdfWriter
from streamlit.testing.v1 import AppTest

from src.harness.api import APIError,redact
from src.harness.feedback import describe_error
from src.harness.intake import parse_files,read_table,table_sheets,FileReadError,file_error
from src.harness.results import overview
from src.harness.store import Run


def test_mixed_upload_keeps_success_and_records_each_failed_bytes():
    uploads=[('valid.txt','合成材料，收入100元。'.encode()),('broken.docx',b'not a workbook'),('broken.xlsx',b'bad')]
    documents,issues=parse_files(uploads)
    assert [d['name'] for d in documents]==['valid.txt']
    assert [i['name'] for i in issues]==['broken.docx','broken.xlsx']
    for issue,(_,raw) in zip(issues,uploads[1:]):
        assert issue['sha256']==hashlib.sha256(raw).hexdigest()
        assert issue['read_status']=='failed' and issue['bytes']==len(raw)
        assert '不要只修改扩展名' in issue['action']
    assert parse_files(uploads[:1])[1]==[]


@pytest.mark.parametrize('encrypted',[False,True])
def test_pdf_without_accessible_text_names_the_required_action(encrypted):
    writer=PdfWriter()
    writer.add_blank_page(width=200,height=200)
    if encrypted:
        writer.encrypt('synthetic_password')
    raw=io.BytesIO()
    writer.write(raw)
    documents,issues=parse_files([('source.pdf',raw.getvalue())])
    assert not documents and len(issues)==1
    assert ('未加密' if encrypted else 'OCR') in issues[0]['action']


def test_corrupt_table_hides_parser_body_and_preserves_specific_filename():
    with pytest.raises(FileReadError) as exc:
        read_table(b'a,b\n"unterminated','broken.csv')
    assert exc.value.filename=='broken.csv'
    assert '引号' in exc.value.action and 'unterminated' not in exc.value.reason
    error=file_error(ValueError('arbitrary private parser content'),'file.docx')
    assert 'private' not in error.reason
    with pytest.raises(FileReadError):
        table_sheets(b'bad zip','broken.xlsx')


def test_valid_workbook_retains_sheet_names_and_leading_zero():
    raw=io.BytesIO()
    with pd.ExcelWriter(raw,engine='openpyxl') as writer:
        pd.DataFrame({'股票':['000001'],'金额':['10']}).to_excel(writer,sheet_name='报表',index=False)
    assert table_sheets(raw.getvalue(),'source.xlsx')==['报表']
    assert read_table(raw.getvalue(),'source.xlsx','报表').iloc[0,0]=='000001'


@pytest.mark.parametrize('kind,title',[
    ('auth','权限'),('quota','额度'),('budget','请求数'),('timeout','超时'),
    ('network','中断'),('context_limit','上限'),('output_limit','上限'),('empty_response','正文'),
    ('json_format','未能采纳'),('credentials','凭据')])
def test_typed_model_failures_explain_action_without_exposing_secret(kind,title):
    secret='synthetic secret/+='
    issue=describe_error(APIError(secret+' '+urllib.parse.quote(secret,safe=''),kind=kind),secret)
    assert title in issue['title'] and issue['action']
    assert secret not in json.dumps(issue) and urllib.parse.quote(secret,safe='') not in issue['detail']
    assert '[已隐藏]' in issue['detail']


def test_empty_secret_does_not_damage_error_message_and_other_tokens_still_redact():
    assert redact('请填写模型名称。','')=='请填写模型名称。'
    assert 'sk-private' not in redact('Bearer abc sk-private','')
    issue=describe_error(RuntimeError('private source content'))
    assert 'private' not in json.dumps(issue) and issue['detail']=='RuntimeError'


def test_error_ui_keeps_server_markup_literal_and_redacted():
    app=AppTest.from_string('''
from src.harness.feedback import show_error
from src.harness.api import APIError
show_error(APIError('![bad](https://example.org/probe) <script>bad</script> synthetic_key',status_code=503),'synthetic_key')
''').run()
    assert not app.exception
    assert any('HTTP 503' in e.value for e in app.error)
    assert all('<script>' not in e.value for e in app.markdown)
    assert any('[已隐藏]' in e.value for e in app.text)
    assert not any('synthetic_key' in e.value for e in app.text)


def test_blocked_intake_history_has_local_recovery_guidance(tmp_path):
    run=Run(tmp_path,'financial',[('bad.docx',b'bad')])
    _,issues=parse_files([('bad.docx',b'bad')])
    run.write('file_read_issues.json',issues)
    run.event('documents_blocked',failed_files=1)
    summary=overview(run.path,run.metadata)
    assert {'项目':'未能读取的文件','本次记录':'1'} in summary['facts']
    assert any('替换或移除' in step for step in summary['next_steps'])
    assert not any('继续模型处理需要原会话' in step for step in summary['next_steps'])


def test_module_refresh_keeps_imported_exception_types_current_and_session_key():
    # Isolate reload from pytest's own already-imported classes and monkeypatches.
    import os
    import subprocess
    import sys
    from pathlib import Path
    code='''
from streamlit.testing.v1 import AppTest
from src.harness import api,financial,engine,feedback
app=AppTest.from_file('harness_app.py').run(timeout=25)
app.text_input(key='api_secret_widget').set_value('synthetic_refresh_key').run()
old=api.APIError
api._c2v_loaded_source_hash='synthetic_changed_stamp'
app.run()
assert not app.exception
assert api.APIError is not old
assert financial.APIError is api.APIError
assert engine.ModelClient is api.ModelClient
assert feedback.redact is api.redact
assert app.session_state['api_secret']=='synthetic_refresh_key'
# Recover mismatched bindings left by an older refresh implementation even when
# no file has changed since that refresh.
financial.APIError=old
app.run()
assert not app.exception
assert financial.APIError is api.APIError
assert app.session_state['api_secret']=='synthetic_refresh_key'
'''
    env={**os.environ,'PYTHONUTF8':'1'}
    result=subprocess.run([sys.executable,'-c',code],cwd=Path(__file__).resolve().parents[1],
        env=env,capture_output=True,text=True,encoding='utf-8',timeout=60)
    assert result.returncode==0,result.stderr[-3000:]
