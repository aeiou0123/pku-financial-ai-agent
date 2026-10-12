"""Local, reviewable next actions and data problems; no model calls or repairs."""
from __future__ import annotations

from .module_stamp import source_stamp
_c2v_loaded_source_hash = source_stamp(__file__)

import numpy as np
import pandas as pd

from .exports import workbook

ACTION_COLUMNS = ['检查条件','事项','需要补充／核对','现有定位','状态']
FACT_TYPES = {'historical':'历史事实候选','forecast':'预测或目标','commitment':'承诺','opinion':'意见'}
REVIEW_STATUS = {'conflicting_candidates':'支持与反证并存，待核对', 'candidate_review_required':'已有摘录候选，待核对', 'not_covered_in_selected_material':'本次选中材料未覆盖'}


def evidence_actions(review, plan):
    """Preserve draft gaps, conflicts and unprocessed conditions as distinct work."""
    assessments = review.get('assessments', [])
    lookup = {a['condition']['id']: a for a in assessments}
    if len(lookup) != len(assessments):
        raise ValueError('条件记录重复，不能生成事项清单。')
    rows = []
    for condition in plan['conditions']:
        label = condition['label']
        assessment = lookup.get(condition['id'])
        def add(kind, text, loc='', status='待人工核对'):
            rows.append(dict(zip(ACTION_COLUMNS, [label, kind, text, loc, status])))
        if assessment is None:
            add('尚未运行的条件', '继续本次审查；当前没有这一条件的模型结果。', status='尚未处理')
            continue
        evidence = assessment.get('evidence', [])
        locations = '；'.join(dict.fromkeys(e.get('source_file','') + ' · ' + e.get('source_locator','') for e in evidence))
        stances = {e.get('stance') for e in evidence}
        if {'supports','contradicts'} <= stances:
            add('支持与反证冲突', '逐条核对公司、产品、时期与口径；冲突尚未裁决。', locations)
        for missing in dict.fromkeys(assessment.get('missing_in_supplied_material', [])):
            add('模型提出的材料缺口', missing, status='待核实缺口')
        if not evidence and not assessment.get('missing_in_supplied_material'):
            add('未找到引用候选', '检查检索词和材料范围；本次未覆盖不表示现实中不存在。')
        if evidence:
            add('摘录与判断核对', '对照原件检查摘录、语义和来源；文字匹配不等于论点成立。', locations)
        if any(e.get('fact_type') in {'forecast','commitment'} for e in evidence):
            add('未来陈述的性质', '区分目标、预测、承诺与已经实现的结果，不能当成历史业绩。', locations)
        if assessment.get('parameter_candidates'):
            add('参数候选确认', '核对数值、单位、产品范围和期间，再决定是否用于情景。', locations)
    return pd.DataFrame(rows, columns=ACTION_COLUMNS)


def quant_audit(frame, mapping, strategy):
    """Collect actionable failures before the strict preparation function; never impute."""
    issues = []
    def issue(kind, count, text, examples=None, blocking=True):
        if count:
            issues.append({'问题':kind, '数量':int(count), '怎么处理':text, '示例':examples or [], '阻挡运行':blocking})
    required = ['date','stock','close'] + (['factor','available_at'] if strategy == 'factor' else [])
    if frame.empty:
        issue('空表',1,'上传有数据行的 CSV 或 Excel。')
    if len(frame)>1000000:
        issue('超过行数上限',len(frame),'本版最多100万行；缩小研究范围后重新体检。')
        return {'ready':False,'rows':len(frame),'issues':issues,'summary':{},'sample_limit':20}
    if len(set(mapping.get(k) for k in required)) != len(required) or any(mapping.get(k) not in frame for k in required):
        issue('列对应缺失或重复',1,'展开“表格列对应”，为日期、股票、价格及因子时间选择不同的实际列。')
        return {'ready':False,'rows':len(frame),'issues':issues,'summary':{},'sample_limit':20}
    data = frame[[mapping[k] for k in required]].copy().reset_index(drop=True)
    data.columns = required
    def samples(mask, columns):
        selected = data.loc[mask, columns].head(20).astype(str)
        return [{'数据行':int(i)+1, **row} for i,row in selected.to_dict('index').items()]
    stocks = data['stock'].astype(str).str.strip()
    stock_ok = stocks.str.fullmatch(r'[0-9]{6}')
    issue('股票代码不是六位文本', (~stock_ok).sum(), '从原始数据恢复前导零；不自动补零或猜代码。',samples(~stock_ok,['stock']))
    dates = pd.to_datetime(data['date'].astype(str),format='%Y-%m-%d',errors='coerce')
    date_ok = data['date'].astype(str).str.fullmatch(r'\d{4}-\d{2}-\d{2}') & dates.notna()
    issue('日期格式或日期无效', (~date_ok).sum(), '使用 YYYY-MM-DD，核对不存在的日期；不要把报告期当交易日期。',samples(~date_ok,['date']))
    prices = pd.to_numeric(data['close'],errors='coerce')
    price_ok = np.isfinite(prices) & prices.gt(0)
    issue('价格缺失或不是正数', (~price_ok).sum(), '回到原始行情核对价格和复权口径；不填零、不前向填充。',samples(~price_ok,['date','stock','close']))
    keys = pd.DataFrame({'date':data['date'].astype(str),'stock':stocks})
    duplicate = keys.duplicated(['date','stock'],keep=False)
    issue('同日同股重复数据行',duplicate.sum(),'对照更正版本和原件决定保留哪条；体检不自动删除。',samples(duplicate,['date','stock','close']))
    valid_keys = keys.loc[date_ok & stock_ok].drop_duplicates()
    nstocks = valid_keys['stock'].nunique()
    counts = valid_keys.groupby('date')['stock'].nunique()
    missing = (nstocks-counts).clip(lower=0)
    issue('日期与股票组合缺失',missing.sum(),'本版要求上传范围内的完整面板。核对停牌、上市退出或数据遗漏，再自行选择共同覆盖范围；未核实官方交易日历。',
          [{'日期':dt,'缺少股票数':int(n)} for dt,n in missing[missing>0].head(20).items()])
    if strategy == 'factor':
        raw_factor = data['factor'].astype(str)
        factors = pd.to_numeric(data['factor'].replace('',np.nan),errors='coerce')
        factor_bad = np.isinf(factors) | (factors.isna() & raw_factor.str.strip().ne('') & ~data['factor'].isna())
        issue('因子值无法解析或无穷',factor_bad.sum(),'修正原始因子值；空因子仍按缺失处理，不当作零。',samples(factor_bad,['date','stock','factor']))
        times = pd.to_datetime(data['available_at'],errors='coerce',utc=True,format='mixed')
        raw_times = data['available_at'].astype(str)
        time_ok = raw_times.str.contains(r'[T ]\d{2}:\d{2}') & raw_times.str.contains(r'(?:Z|[+-]\d{2}:?\d{2})$') & times.notna()
        issue('因子可得时间无效',(~time_ok).sum(),'填写真实时分与时区，例如 2025-01-02T14:30:00+08:00；不能把事后信息改成早已可得。',samples(~time_ok,['available_at']))
        cutoff = (dates + pd.Timedelta(hours=15)).dt.tz_localize('Asia/Shanghai').dt.tz_convert('UTC')
        late = time_ok & date_ok & (times > cutoff)
        issue('当日收盘尚不可用的因子',late.sum(),'既有回测会屏蔽这些当日信号；如日期标错，请对照真实发布时间修正，不向前移动信息。',samples(late,['date','stock','available_at']),blocking=False)
    summary = {'股票数':int(nstocks),'上传表中的日期数':int(len(counts)),
               '最早日期':dates[date_ok].min().date().isoformat() if date_ok.any() else None,
               '最晚日期':dates[date_ok].max().date().isoformat() if date_ok.any() else None}
    return {'ready':not any(i['阻挡运行'] for i in issues),'rows':len(frame),'issues':issues,'summary':summary,'sample_limit':20}


def audit_tables(audit):
    overview = pd.DataFrame([{k:v for k,v in item.items() if k!='示例'} for item in audit['issues']],columns=['问题','数量','怎么处理','阻挡运行'])
    samples = pd.DataFrame([{'问题':item['问题'],**row} for item in audit['issues'] for row in item['示例']])
    return {'检查概况':pd.DataFrame([audit['summary']|{'数据行数':audit['rows'],'格式检查通过':audit['ready']}]),'问题清单':overview,'问题示例':samples}


def save_audit(run, audit):
    run.write('data_readiness.json',audit)
    run.write('data_readiness.xlsx',workbook(audit_tables(audit)))
    run.event('quant_data_checked', ready=audit['ready'], issue_types=len(audit['issues']))


def render_quant_audit(audit):
    import streamlit as st
    if audit['ready']:
        st.success('数据格式检查通过。运行前仍须确认复权口径和交易假设。')
    else:
        st.warning('数据体检发现问题。先修正下面的项目，再运行回测；不会自动补值或删行。')
    st.write('数据行数：' + str(audit['rows']) + '；股票数：' + str(audit['summary'].get('股票数','尚未确定')))
    for item in audit['issues']:
        st.markdown('**' + item['问题'] + '：' + str(item['数量']) + '**')
        st.write(item['怎么处理'])
        if item['示例']:
            st.dataframe(pd.DataFrame(item['示例']),hide_index=True)
    st.caption('示例每类最多20条，数量按本次全表统计。体检不认证复权、官方交易日历或因子来源，也不代表回测将获利。')
