import csv
import json
import pytest
from src.evidence_batch import read_cases,review_batch


def write_csv(path,rows):
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(['case_id','claim','source','source_url','source_locator']);w.writerows(rows)


def test_batch_records_missing_evidence_and_invalid_url_separately(tmp_path):
    source='产品手册：产品额定扭矩为0.172kNm\n原文第二行'
    f=tmp_path/'input.csv';write_csv(f,[['ok','产品额定扭矩为172Nm',source,'https://example.com/manual','第2页'],['bad','声明','原文','javascript:bad',''],['empty','公司产品适用机器人','','','']])
    out=tmp_path/'result';r=review_batch(f,out)
    assert (r['total'],r['reviewed'],r['invalid_input'])==(3,2,1)
    assert r['records'][0]['verdict']=='abstain'
    assert json.loads((out/'ok.json').read_text())['source']==source
    assert not (out/'bad.json').exists()
    assert json.loads((out/'empty.json').read_text())['financial']['status']=='skipped'
    with pytest.raises(FileExistsError):review_batch(f,out)


@pytest.mark.parametrize('rows',[
    [['same','声明','原文','',''],['same','第二声明','原文','','']],
    [['../escape','声明','原文','','']],[['/absolute','声明','原文','','']],
])
def test_invalid_ids_do_not_create_output_or_escape(tmp_path,rows):
    f=tmp_path/'input.csv';write_csv(f,rows);out=tmp_path/'output'
    with pytest.raises(ValueError):review_batch(f,out)
    assert not out.exists()


def test_encoding_columns_and_size_validation():
    for data in [b'case_id,claim,source,claim\na,b,c,d\n',b'case_id,claim\na,b\n',b'case_id,claim,source\na,b,c,extra\n',b'\xff',b' '*(5*1024*1024+1),b'case_id,claim,source\n']:
        with pytest.raises(ValueError):read_cases(data)


def test_batch_limit():
    text='case_id,claim,source\n'+''.join(f'c{i},claim,source\n' for i in range(101))
    with pytest.raises(ValueError,match='100'):read_cases(text.encode())


def test_malformed_header_returns_readable_validation_error():
    with pytest.raises(ValueError,match='表头'):
        read_cases(b'"case_id,claim,source\n')
