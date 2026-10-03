"""CSV intake for offline text review; no source authentication or valuations."""
import csv
import hashlib
import io
import json
from pathlib import Path
import re
from src.review_session import run_review, review_markdown

REQUIRED={'case_id','claim','source'}
ALLOWED=REQUIRED|{'source_url','source_locator'}


def read_cases(data):
    if len(data)>5*1024*1024:
        raise ValueError('批次文件最多5MB')
    try:
        text=data.decode('utf-8-sig')
    except UnicodeDecodeError as exc:
        raise ValueError('请将CSV导出为UTF-8编码') from exc
    reader=csv.DictReader(io.StringIO(text,newline=''),strict=True)
    try:
        fields=reader.fieldnames or []
    except csv.Error as exc:
        raise ValueError('CSV表头引号格式错误') from exc
    if len(fields)!=len(set(fields)) or not REQUIRED<=set(fields) or set(fields)-ALLOWED:
        raise ValueError('须含case_id、claim、source；可选source_url、source_locator，不接受重复或未知列')
    rows,ids=[],set()
    try:
        for line,row in enumerate(reader,2):
            if len(rows)>=100:raise ValueError('每批最多100条')
            if None in row or any(v is None for v in row.values()):raise ValueError(f'记录{line}列数不一致')
            case_id=row['case_id'].strip()
            if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}',case_id) or case_id in ids:
                raise ValueError(f'记录{line}case_id须唯一、仅含字母数字下划线或短横线，最多64字符')
            ids.add(case_id);row['case_id']=case_id;rows.append(row)
    except csv.Error as exc:
        raise ValueError('CSV引号或换行格式错误') from exc
    if not rows:raise ValueError('CSV没有案例')
    return rows


def review_batch(input_path,output_dir):
    data=Path(input_path).read_bytes();cases=read_cases(data)
    out=Path(output_dir);out.mkdir(parents=True,exist_ok=False)
    records=[]
    for row in cases:
        case_id=row['case_id']
        try:
            result=run_review(row['claim'],row['source'],row.get('source_url',''),row.get('source_locator',''))
        except ValueError as exc:
            records.append({'case_id':case_id,'status':'invalid_input','error':str(exc)});continue
        (out/f'{case_id}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        (out/f'{case_id}.md').write_text(review_markdown(result),encoding='utf-8')
        records.append({'case_id':case_id,'status':'reviewed','verdict':result['verification']['verdict'],
                        'source_sha256':result['review_session']['source_sha256'],
                        'json_file':f'{case_id}.json','markdown_file':f'{case_id}.md'})
    root=Path(__file__).resolve().parents[1]
    fingerprints={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in [Path(__file__),root/'src/quantity_text.py',root/'src/state_verifier.py',root/'src/review_session.py',root/'src/workflow.py',root/'src/evidence_ledger.py']}
    index={'scope':'USER_SUPPLIED_TEXT_OFFLINE_RULE_REVIEW_NOT_SOURCE_AUTHENTICATION',
           'input_sha256':hashlib.sha256(data).hexdigest(),'code_sha256':fingerprints,
           'total':len(records),'reviewed':sum(r['status']=='reviewed' for r in records),
           'invalid_input':sum(r['status']=='invalid_input' for r in records),
           'external_api_calls':0,'financial_scope':'No valuations for custom evidence','records':records}
    (out/'batch_index.json').write_text(json.dumps(index,ensure_ascii=False,indent=2),encoding='utf-8')
    return index
