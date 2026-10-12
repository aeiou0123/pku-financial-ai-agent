"""Offline CSMAR announcement discovery. Metadata never becomes full-text evidence."""
from __future__ import annotations
from .module_stamp import source_stamp
_c2v_loaded_source_hash = source_stamp(__file__)

from collections import Counter
from datetime import date
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re

COMPANIES={'688017':'绿的谐波','002472':'双环传动','688160':'步科股份'}
MAX_FILE_BYTES=20*1024*1024


def valid_date(value):
    if not isinstance(value,str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}',value):
        return ''
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError:
        return ''


def identifier(value):
    # Decimal IDs may arrive as integers, but never round floating-point IDs.
    if isinstance(value,bool) or not isinstance(value,(str,int,Decimal)):
        return ''
    text=str(value)
    return text if re.fullmatch(r'\d+',text) else ''


def _read(root,path):
    if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError('文件必须位于资料目录内。')
    if path.stat().st_size>MAX_FILE_BYTES:
        raise ValueError('单个索引文件超过20MB。')
    raw=path.read_bytes()
    def reject_constant(value):
        raise ValueError('索引包含非有限数值。')
    data=json.loads(raw.decode('utf-8-sig'),parse_float=Decimal,parse_constant=reject_constant)
    if not isinstance(data,dict) or not isinstance(data.get('rows'),list):
        raise ValueError('文件不是包含rows的CSMAR业务JSON。')
    if data.get('row_count') is not None and data['row_count']!=len(data['rows']):
        raise ValueError('记录行数与声明行数不一致。')
    return data,{'file':path.relative_to(root).as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),
        'bytes':len(raw),'rows':len(data['rows']),'partial_response':bool(data.get('error'))}


def load_catalog(root):
    """Read only whitelisted business artifacts; no login, SDK or network access."""
    root=Path(root)
    security,info,receipts,issues={}, {}, [], []
    directory=root/'raw/C_announcements'
    files=sorted(directory.glob('ANN_Security*.business.json'))+sorted(directory.glob('ANN_AnnouncementInfo*.business.json'))
    for path in files:
        name=path.relative_to(root).as_posix()
        try:
            data,receipt=_read(root,path)
        except (ValueError,OSError,UnicodeError,RecursionError):
            issues.append({'file':name,'issue':'文件结构未通过检查；没有采用其中记录。'})
            continue
        receipts.append(receipt)
        if receipt['partial_response']:
            issues.append({'file':name,'issue':'采集文件记录了中断；只登记实际收到的行，不视为整批完成。'})
        expected='ANN_Security' if path.name.startswith('ANN_Security') else 'ANN_AnnouncementInfo'
        declared=data.get('table')
        # The received collector uses an explicit local job label ending _ID;
        # its platform query is ANN_AnnouncementInfo, not a new database table.
        accepted={expected} if expected=='ANN_Security' else {'ANN_AnnouncementInfo','ANN_AnnouncementInfo_ID'}
        receipt['declared_table']=declared
        if not isinstance(declared,str) or declared not in accepted or (declared=='ANN_AnnouncementInfo_ID' and data.get('key_field')!='AnnouncementID'):
            issues.append({'file':name,'issue':'表名与索引文件名不一致；没有采用其中记录。'})
            continue
        for number,row in enumerate(data['rows'],1):
            if not isinstance(row,dict) or not identifier(row.get('AnnouncementID')):
                issues.append({'file':name,'row':number,'issue':'公告ID无效；本行未采用。'})
                continue
            aid=identifier(row['AnnouncementID'])
            provenance={'file':name,'sha256':receipt['sha256'],'row':number,'partial_response':receipt['partial_response']}
            if expected=='ANN_Security':
                if row.get('SecurityTypeID')!='P50100':
                    continue
                symbol=row.get('Symbol')
                if not isinstance(symbol,str) or symbol not in COMPANIES:
                    issues.append({'file':name,'row':number,'issue':'证券代码不在本次三家公司范围内或未保留字符串格式；本行未采用。'})
                    continue
                record={'stock_code':symbol,'published_at':valid_date(row.get('DeclareDate')),
                    'published_at_raw':str(row.get('DeclareDate') or ''),
                    'title':str(row.get('Title') or '')}
                security.setdefault((symbol,aid),[]).append((record,provenance))
            else:
                record={'published_at':valid_date(row.get('DeclareDate')),
                    'published_at_raw':str(row.get('DeclareDate') or ''),
                    'title':str(row.get('Title') or ''),'format':str(row.get('AnnouncementType') or ''),
                    'file_size_raw':str(row.get('FileSize') if row.get('FileSize') is not None else '')}
                info.setdefault(aid,[]).append((record,provenance))
    entries=[]
    for (symbol,aid),versions in sorted(security.items()):
        basic=info.get(aid,[])
        scope_versions={json.dumps(r,sort_keys=True,ensure_ascii=False) for r,_ in versions}
        basic_versions={json.dumps(r,sort_keys=True,ensure_ascii=False) for r,_ in basic}
        dates={r['published_at_raw'] for r,_ in versions+basic}
        titles={r['title'] for r,_ in versions+basic}
        conflict=len(scope_versions)>1 or len(basic_versions)>1 or len(dates)>1 or len(titles)>1
        primary=versions[0][0]
        # Never choose a convenient version of conflicting metadata.
        status='conflict' if conflict else 'metadata_received' if basic else 'index_only'
        entries.append({'announcement_id':aid,'stock_code':symbol,'company':COMPANIES[symbol],
            'title':primary['title'],'published_at':'' if conflict else primary['published_at'],
            'published_at_raw':primary['published_at_raw'],'metadata_status':status,
            'full_text_status':'not_loaded','sources':[p for _,p in versions+basic]})
    summary={'target_ids':len({r['announcement_id'] for r in entries}),
        'target_links':len(entries),'all_received_info_ids':len(info),
        'received_target_info_ids':len({r['announcement_id'] for r in entries if r['announcement_id'] in info}),
        'missing_target_info_ids':len({r['announcement_id'] for r in entries if r['announcement_id'] not in info}),
        'conflicting_links':sum(r['metadata_status']=='conflict' for r in entries),
        'invalid_date_links':sum(not r['published_at'] and r['metadata_status']!='conflict' for r in entries),
        'full_texts_loaded':0,'files':len(receipts),
        'by_year':dict(sorted(Counter(r['published_at'][:4] for r in entries if r['published_at']).items()))}
    return {'entries':entries,'summary':summary,'issues':issues,'receipts':receipts}


def search_catalog(catalog,stock_code,cutoff,keywords=''):
    if stock_code not in COMPANIES or not valid_date(cutoff):
        raise ValueError('请选择支持的公司并填写有效研究截止日。')
    terms=[t.casefold() for t in re.split(r'[\s,，;；]+',keywords.strip()) if t]
    return [r for r in catalog['entries'] if r['stock_code']==stock_code and r['published_at']
        and r['published_at']<=cutoff and r['metadata_status']!='conflict'
        and (not terms or any(t in r['title'].casefold() for t in terms))]


def shortlist_tables(rows):
    import pandas as pd
    index=[{'证券代码':r['stock_code'],'公司':r['company'],'公告ID':r['announcement_id'],
        '公告日期':r['published_at'],'公告标题':r['title'],
        '目录状态':{'metadata_received':'基本信息已收','index_only':'仅证券索引','conflict':'元数据冲突待核'}[r['metadata_status']],
        '全文状态':'尚未接入原件','下一步':'按公司公告页或交易所检索标题与日期；下载原件并核对实际披露日。'} for r in rows]
    locations=[{'公告ID':r['announcement_id'],'来源文件':p['file'],'SHA256':p['sha256'],
        '业务JSON行号':p['row'],'来源采集中断':p['partial_response']} for r in rows for p in r['sources']]
    index_columns=['证券代码','公司','公告ID','公告日期','公告标题','目录状态','全文状态','下一步']
    location_columns=['公告ID','来源文件','SHA256','业务JSON行号','来源采集中断']
    return {'待找原件':pd.DataFrame(index,columns=index_columns),'目录溯源':pd.DataFrame(locations,columns=location_columns)}


def synthetic_catalog():
    rows=[]
    for aid,published,title in [('1','2026-01-10','合成示例：扩产计划公告'),('2','2026-02-10','合成示例：客户订单风险提示')]:
        rows.append({'announcement_id':aid,'stock_code':'688017','company':'合成示例公司',
            'title':title,'published_at':published,'metadata_status':'index_only','full_text_status':'not_loaded',
            'sources':[{'file':'synthetic_example','sha256':'','row':int(aid),'partial_response':False}]})
    return {'entries':rows,'summary':{'target_ids':2,'missing_target_info_ids':2,'full_texts_loaded':0},'issues':[],'receipts':[]}
