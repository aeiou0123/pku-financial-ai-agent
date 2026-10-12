"""Announcement metadata prepares originals; it cannot authenticate or replace them."""
import io
import json
from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest
from openpyxl import load_workbook

from src.harness.catalog import load_catalog,search_catalog,shortlist_tables,synthetic_catalog,identifier
from src.harness.exports import workbook


def put(root,name,table,rows,**extra):
    folder=root/'raw/C_announcements'
    folder.mkdir(parents=True,exist_ok=True)
    (folder/name).write_text(json.dumps({'table':table,'row_count':len(rows),'rows':rows,**extra}),encoding='utf-8')


def security(aid='1',symbol='002472',kind='P50100',day='2026-01-01',title='扩产计划'):
    return {'AnnouncementID':aid,'Symbol':symbol,'SecurityTypeID':kind,'DeclareDate':day,'Title':title}


def basic(aid='1',day='2026-01-01',title='扩产计划'):
    return {'AnnouncementID':aid,'DeclareDate':day,'Title':title,'FileSize':None,'AnnouncementType':'pdf'}


def test_scope_deduplicates_retain_sources_and_never_loads_full_text(tmp_path):
    put(tmp_path,'ANN_Security_a.business.json','ANN_Security',[security(),security(),security('2',kind='P50302'),security('3',symbol='600000')])
    put(tmp_path,'ANN_AnnouncementInfo_a.business.json','ANN_AnnouncementInfo',[basic()])
    put(tmp_path,'ANN_AnnouncementInfo_b.business.json','ANN_AnnouncementInfo_ID',[basic()],key_field='AnnouncementID',error='partial query stopped')
    (tmp_path/'private_runtime').mkdir()
    (tmp_path/'private_runtime/token.json').write_text('this is not JSON',encoding='utf-8')
    result=load_catalog(tmp_path)
    assert result['summary']['target_ids']==1 and result['summary']['received_target_info_ids']==1
    row=result['entries'][0]
    assert row['stock_code']=='002472' and len(row['sources'])==4
    assert row['metadata_status']=='metadata_received' and row['full_text_status']=='not_loaded'
    assert result['summary']['full_texts_loaded']==0 and result['issues']
    assert all('private_runtime' not in r['file'] for r in result['receipts'])


@pytest.mark.parametrize('change',[{'Title':'不同标题'},{'DeclareDate':'2026-01-02'}])
def test_metadata_conflicts_are_not_resolved_by_latest_file_or_convenient_date(tmp_path,change):
    put(tmp_path,'ANN_Security_a.business.json','ANN_Security',[security()])
    put(tmp_path,'ANN_AnnouncementInfo_a.business.json','ANN_AnnouncementInfo',[basic()])
    put(tmp_path,'ANN_AnnouncementInfo_b.business.json','ANN_AnnouncementInfo',[{**basic(),**change}])
    result=load_catalog(tmp_path)
    assert result['entries'][0]['metadata_status']=='conflict'
    assert result['entries'][0]['published_at']==''
    assert search_catalog(result,'002472','2026-01-31')==[]


def test_cutoff_is_inclusive_invalid_dates_excluded_terms_literal_or(tmp_path):
    put(tmp_path,'ANN_Security_a.business.json','ANN_Security',[
        security('1'),security('2',day='2026-01-02',title='订单风险'),
        security('3',day='2026-00-00'),security('4',title='abc[def')])
    result=load_catalog(tmp_path)
    assert [r['announcement_id'] for r in search_catalog(result,'002472','2026-01-01','扩产，订单')]==['1']
    assert [r['announcement_id'] for r in search_catalog(result,'002472','2026-01-01','[')]==['4']
    assert result['summary']['invalid_date_links']==1
    assert all(r['metadata_status']=='index_only' for r in result['entries'])


def test_unknown_job_alias_bad_id_and_wrong_count_fail_explicitly(tmp_path):
    put(tmp_path,'ANN_Security_a.business.json','ANN_Security',[security(aid=1.5),security(aid=True),security('3')])
    put(tmp_path,'ANN_AnnouncementInfo_a.business.json','ANN_Unknown',[basic('3')])
    result=load_catalog(tmp_path)
    assert result['summary']['target_ids']==1 and result['summary']['received_target_info_ids']==0
    assert len(result['issues'])==3
    put(tmp_path,'ANN_AnnouncementInfo_b.business.json','ANN_AnnouncementInfo',[basic('3')])
    file=tmp_path/'raw/C_announcements/ANN_AnnouncementInfo_b.business.json'
    data=json.loads(file.read_text());data['row_count']=2
    file.write_text(json.dumps(data))
    assert load_catalog(tmp_path)['summary']['received_target_info_ids']==0
    assert identifier(1.0)=='' and identifier('0001')=='0001'


def test_bad_metadata_types_do_not_abort_valid_received_records(tmp_path):
    put(tmp_path,'ANN_Security_a.business.json','ANN_Security',[
        security(),security('2',symbol={'code':'002472'}),
        {key:value for key,value in security('3').items() if key!='Symbol'}])
    put(tmp_path,'ANN_AnnouncementInfo_a.business.json',{'wrong':'table'},[basic()])
    result=load_catalog(tmp_path)
    assert result['summary']['target_ids']==1 and result['summary']['received_target_info_ids']==0
    assert len(result['issues'])==3


def test_export_keeps_stock_text_formula_literal_and_original_followup(tmp_path):
    put(tmp_path,'ANN_Security_a.business.json','ANN_Security',[security(title='=1+1')])
    row=load_catalog(tmp_path)['entries'][0]
    tables=shortlist_tables([row])
    data=load_workbook(io.BytesIO(workbook(tables)))
    assert data['待找原件']['A2'].value=='002472'
    assert data['待找原件']['E2'].value=='=1+1' and data['待找原件']['E2'].data_type=='s'
    assert data['待找原件']['G2'].value=='尚未接入原件'
    assert data['目录溯源']['C2'].value==row['sources'][0]['sha256']


def test_deployed_empty_workspace_has_usable_synthetic_directory_without_model(tmp_path):
    app=AppTest.from_string('''
from pathlib import Path
from src.harness.catalog_ui import render
render(Path(ROOT))
'''.replace('ROOT',repr(str(tmp_path)))).run()
    assert not app.exception
    assert any('合成示例' in e.value for e in app.info)
    assert len(app.get('download_button'))==2
    app.text_input(key='catalog_terms').set_value('不存在的关键词').run()
    assert not app.exception and not app.get('download_button')
