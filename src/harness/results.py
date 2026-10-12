"""Bounded local snapshot readers and literal result summaries; no model calls."""
from __future__ import annotations

from .module_stamp import source_stamp
_c2v_loaded_source_hash = source_stamp(__file__)

from datetime import datetime, timedelta, timezone
import json
import math
import hashlib
from pathlib import Path
import re
from .presentation import render_report

WORKFLOWS = {'industry_research':'观点检查', 'financial':'财务整理', 'quant':'策略回测',
    'realization_conditions':'情景估值', 'tutorial_quant':'合成回测样例', 'tutorial_conditions':'合成估值样例',
    'valuation':'现金流估值', 'strategy_diagnostics':'策略诊断', 'quant_data_check':'回测数据体检', 'earnings_diagnostics':'盈利变化解释'}
REPORTS = {'financial_report.md':'财务核验报告', 'quant_report.md':'回测说明', 'thesis_review.md':'观点检查底稿',
    'realization_conditions.md':'情景估值说明', 'valuation.md':'现金流估值说明',
    'earnings_diagnostics.md':'盈利变化底稿', 'strategy_diagnostics.md':'参数比较报告'}
FILES = REPORTS | {'financial.xlsx':'财务数据与历史比率', 'financial_normalized.csv':'标准化财务长表',
    'historical_ratios.csv':'历史比率', 'quality_report.json':'财务校验明细', 'thesis_review.xlsx':'证据与参数候选',
    'research_actions.xlsx':'待核对事项', 'research_actions.json':'待核对事项明细',
    'realization_conditions.xlsx':'预测年度与约束', 'data_readiness.xlsx':'数据体检问题表',
    'data_readiness.json':'数据体检明细', 'daily.csv':'每日净值与费用', 'positions.csv':'持仓明细',
    'rank_ic.csv':'因子相关性明细', 'metrics.json':'回测指标', 'cleaned_data.csv':'回测输入快照',
    'valuation_assumptions.json':'现金流估值假设', 'valuation_sensitivity.csv':'现金流估值敏感性',
    'earnings_diagnostics.xlsx':'盈利变化与原件定位', 'earnings_diagnostics.json':'盈利变化计算明细',
    'strategy_diagnostics.xlsx':'参数比较与年度分段', 'strategy_diagnostics.json':'参数比较明细',
    'strategy_diagnostic_failures.json':'失败参数组明细', 'file_read_issues.json':'文件读取问题清单'}
READABLE = set(FILES) | {'research_input.json','thesis_review.json','thesis_partial.json','extraction_progress.json',
    'realization_conditions.json','example_notice.md','task_settings.json'}
MAX_DOWNLOAD = 12 * 1024 * 1024


def snapshot_path(root: Path, run_id: str) -> Path:
    if not re.fullmatch(r'\d{8}_\d{6}_[a-f0-9]{10}', run_id):
        raise ValueError('运行编号不合法。')
    path = root / run_id
    if root.is_symlink() or path.is_symlink() or path.resolve().parent != root.resolve() or not path.is_dir():
        raise ValueError('记录目录不可读取。')
    if (path/'outputs').is_symlink():
        raise ValueError('结果目录不可读取。')
    return path


def read_output(path: Path, name: str, limit=MAX_DOWNLOAD) -> bytes | None:
    if name not in READABLE:
        raise ValueError('该文件不在成果预览范围内。')
    folder, file = path/'outputs', path/'outputs'/name
    if path.is_symlink() or folder.is_symlink() or file.is_symlink():
        raise ValueError('成果文件不能是链接。')
    if file.resolve().parent != folder.resolve():
        raise ValueError('成果文件位置异常。')
    if not file.is_file():
        return None
    # Read limit+1 so a concurrent write cannot turn the size check into an unbounded read.
    with file.open('rb') as stream:
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise ValueError('文件超过单项预览／下载上限，请使用完整成果 ZIP。')
    return raw


def read_json(path, name, notices):
    try:
        raw = read_output(path, name, 1024*1024)
        if raw is None:
            return None
        value = json.loads(raw.decode('utf-8'), parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
        if not isinstance(value, dict):
            raise ValueError('预期对象')
        shapes = {
            'quality_report.json': ('errors','warnings'),
            'thesis_review.json': ('assessments',), 'thesis_partial.json': ('assessments',),
            'data_readiness.json': ('issues',),
            'earnings_diagnostics.json': ('bridge',), 'strategy_diagnostics.json': ('comparisons','failures'),
        }
        if any(not isinstance(value.get(k),list) for k in shapes.get(name,())):
            raise ValueError('结果结构不完整')
        if name == 'quality_report.json' and any(not isinstance(e,dict) for e in value['errors']):
            raise ValueError('校验问题结构无效')
        if name in {'thesis_review.json','thesis_partial.json','extraction_progress.json'} and not isinstance(value.get('complete'),bool):
            raise ValueError('完成状态缺失')
        if name == 'data_readiness.json' and not isinstance(value.get('ready'),bool):
            raise ValueError('体检状态缺失')
        if name == 'metrics.json' and any(
            isinstance(value.get(k),bool) or not isinstance(value.get(k),(int,float)) or not math.isfinite(value[k])
            for k in ('days','stocks','total_return','max_drawdown','fee_bps_single_side')):
            raise ValueError('指标不完整或无效')
        if name == 'realization_conditions.json' and (not isinstance(value.get('forward'),dict) or any(
                not isinstance(value['forward'].get(k),list) for k in ('conflicts','gaps'))):
            raise ValueError('情景结构不完整')
        return value
    except (ValueError, OSError, UnicodeError, RecursionError):
        notices.append(f'{name} 未能读取，相关概况没有生成；请检查下载文件。')
        return None


def record_title(meta, path):
    notices = []
    research = read_json(path, 'research_input.json', notices) or {}
    context = research.get('context')
    question = context.get('question') if isinstance(context, dict) else None
    names = [str(item.get('name','')) for item in meta.get('inputs',[]) if item.get('name')]
    return str(question or '、'.join(names) or WORKFLOWS.get(meta.get('workflow'), '研究记录'))[:160]


def local_time(meta):
    try:
        dt = datetime.fromisoformat(meta['created_at'])
        if dt.tzinfo is None:
            raise ValueError('没有时区')
        return dt.astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M')
    except (KeyError, TypeError, ValueError):
        return '时间未记录'


def overview(path, meta):
    """Never upgrade format checks or model candidates to confirmed financial facts."""
    notices, facts, next_steps = [], [], []
    synthetic = meta.get('workflow','').startswith('tutorial_')
    examples = Path(__file__).resolve().parents[2]/'docs/harness/examples'
    for item in meta.get('inputs',[]):
        name = item.get('name','')
        if name in {'synthetic_prices.csv','synthetic_financial.csv','synthetic_financial.txt',
                    'synthetic_industry.txt','synthetic_industry_counterevidence.txt'}:
            try:
                synthetic = synthetic or item.get('sha256') == hashlib.sha256((examples/name).read_bytes()).hexdigest()
            except OSError:
                pass
    try:
        synthetic = synthetic or read_output(path,'example_notice.md',65536) is not None
    except (ValueError, OSError):
        notices.append('样例标记未能读取。')
    def fact(label, value):
        facts.append({'项目':label, '本次记录':str(value)})
    def count(value):
        return len(value) if isinstance(value,list) else 0
    def number(value, percent=False):
        if isinstance(value, bool) or not isinstance(value,(int,float)) or not math.isfinite(value):
            return '未记录'
        return f'{value:.2%}' if percent else f'{value:,.2f}'
    try:
        raw_issues = read_output(path,'file_read_issues.json',1024*1024)
        if raw_issues is not None:
            issues = json.loads(raw_issues.decode('utf-8'))
            if not isinstance(issues,list) or any(not isinstance(i,dict) for i in issues):
                raise ValueError('读取问题结构无效')
            if issues:
                fact('未能读取的文件',len(issues))
                next_steps.append('下载文件读取问题清单，替换或移除失败文件后重新读取。此次材料读取未完成，没有发送模型请求。')
    except (ValueError,OSError,UnicodeError,RecursionError):
        notices.append('文件读取问题清单未能读取，请检查下载文件。')
    quality = read_json(path,'quality_report.json',notices)
    if quality is not None:
        fact('标准化记录', quality.get('normalized_rows','未记录'))
        fact('校验错误／缺失提示', f"{count(quality.get('errors'))}／{count(quality.get('warnings'))}")
        next_steps.append('对照原件核对披露日、单位、报表范围及更正版本；本地格式与指纹检查不认证出处。')
        if quality.get('errors'):
            next_steps.insert(0,'回到财务确认表修正校验错误，再重新生成成果；本记录不是可用财务结果。')
        if quality.get('extraction_complete') is False:
            next_steps.insert(0,'仅覆盖部分已确认候选。保留原浏览器会话继续提取，或重新上传原件开启新任务。')
    progress = read_json(path,'extraction_progress.json',notices)
    if progress:
        fact('模型提取批次', f"{progress.get('completed_batches','?')}／{progress.get('total_batches','?')}（不认证原件或字段）")
        if progress.get('complete') is not True and quality is None:
            next_steps.append('提取尚未完成；已有候选需人工核对，不能当作全文审查。')
    review = read_json(path,'thesis_review.json',notices)
    if review is None:
        review = read_json(path,'thesis_partial.json',notices)
    if review is not None:
        assessments = review.get('assessments',[])
        assessments = assessments if isinstance(assessments,list) else []
        fact('已处理的研究条件', len(assessments))
        fact('材料缺口提示', sum(count(a.get('missing_in_supplied_material')) for a in assessments if isinstance(a,dict)))
        fact('审查范围', '所选文本片段已处理，摘录与判断待核对' if review.get('complete') is True else '部分完成，仍有未处理条件')
        next_steps.append('先查看待核对事项，逐条检查支持材料、反证、原文位置和未来陈述；模型不裁决论点成立。')
    audit = read_json(path,'data_readiness.json',notices)
    if audit is not None:
        fact('回测数据体检', '格式通过，仍须确认口径' if audit.get('ready') is True else '需要修正，暂不回测')
        fact('体检问题类别', count(audit.get('issues')))
        next_steps.append('按体检问题表回到源数据修正；体检不自动补值、删行或认证复权。')
    metrics = read_json(path,'metrics.json',notices)
    if metrics is not None:
        fact('回测评估日／股票数', f"{metrics.get('days','未记录')}／{metrics.get('stocks','未记录')}")
        fact('本次样本净收益', number(metrics.get('total_return'),True))
        fact('本次最大回撤', number(metrics.get('max_drawdown'),True))
        fact('单边费率（bps）', number(metrics.get('fee_bps_single_side')))
        next_steps.append('查看每日净值、费用和持仓，核对复权与交易约束；这些是上传样本的表现，不是样本外或比赛成绩。')
    conditions = read_json(path,'realization_conditions.json',notices)
    if conditions is not None and isinstance(conditions.get('forward'),dict):
        forward = conditions['forward']
        conflicts = count(forward.get('conflicts'))
        fact('情景约束冲突／证据缺口', f"{conflicts}／{count(forward.get('gaps'))}")
        fact('假设企业价值（元）', '约束冲突，暂缓估值' if conflicts else number(forward.get('enterprise_value')))
        next_steps.append('先检查约束冲突和证据缺口，再确认销量、售价及成本假设；情景数值不是历史事实或投资结论。')
    valuation = read_json(path,'valuation_assumptions.json',notices)
    if valuation is not None:
        fact('假设现金流企业价值（元）',number(valuation.get('enterprise_value')))
        fact('假设股权价值（元）',number(valuation.get('equity_value')))
        next_steps.append('对照现金流假设和敏感性表复核折现率、增长率及净债务；没有净债务时不计算股权价值。')
    earnings=read_json(path,'earnings_diagnostics.json',notices)
    if earnings is not None:
        fact('年度比较',str(earnings.get('earlier','未记录'))+' 至 '+str(earnings.get('later','未记录')))
        fact('会计变化金额（元）',earnings.get('target_change_cny','未记录'))
        next_steps.append('查看收入、毛利率和其余项目的贡献，核对两期原件与比较口径。会计分解不是技术进步的因果贡献。')
    strategy=read_json(path,'strategy_diagnostics.json',notices)
    if strategy is not None:
        fact('成功／失败参数组',f"{len(strategy['comparisons'])}／{len(strategy['failures'])}")
        next_steps.append('在共同持仓区间比较全部声明参数组，保留失败组及已查看样本登记；不把最佳组当作新留出结果。')
    if not facts:
        next_steps.append('这条记录没有可读取的结构化结果。查看状态与已保存文件；修正问题后从工作区重新运行。')
    if meta.get('status') in {'quant_failed','financial_blocked','thesis_review_interrupted','extraction_interrupted','extraction_partial','strategy_diagnostic_failed'}:
        next_steps.insert(0,'本次处理存在中断或待修正项目。历史页只能查看快照；继续模型处理需要原会话，或重新上传原件。')
    return {'synthetic':synthetic, 'facts':facts, 'next_steps':list(dict.fromkeys(next_steps)), 'notices':notices,
            'financial_problems':financial_problems(quality['errors']) if quality is not None else []}


def financial_problems(errors):
    explanations = {
        'stock_code_requires_six_digits':'股票代码须保留六位文本。回到源数据恢复前导零，不猜测代码。',
        'publication_or_period_after_cutoff':'报告期、实际披露日和截止日的先后关系无效。核对实际日期或调整研究范围，不倒填日期。',
        'unknown_statement_scope':'报表范围须区分合并与母公司，按模板选 consolidated 或 parent。',
        'unknown_canonical_metric':'标准指标不受支持，请对照财务模板映射原指标，不猜口径。',
        'stock_metric_requires_point_in_time':'资产、负债、权益等时点值须选 point_in_time，不作累计或年度流量。',
        'invalid_flow_period_type':'收入与利润等流量须区分 annual、cumulative 和 single_quarter。',
        'invalid_published_at':'实际披露日须为有效的 YYYY-MM-DD 日期。',
        'invalid_report_period':'报告期须为有效的 YYYY-MM-DD 日期。',
        'annual_flow_requires_december_31':'年度流量须对应12月31日期末；中期流量保留中期口径。',
        'unsupported_unit_or_currency':'核对金额单位与币种。仅使用模板支持的单位，不混用万元、亿元。',
        'source_file_missing':'对应原件没有上传。请上传原件并核对财务长表的文件名。',
        'source_hash_mismatch':'原件指纹不匹配。核对是否上传了不同版本，不直接改指纹绕过检查。',
        'duplicate_metric_requires_review':'同口径指标重复。检查更正版本及重复行，再人工决定保留哪条。',
        'balance_sheet_mismatch':'资产负债表不平衡。核对资产、负债、权益是否同期间、同版本、同报表范围。',
        'invalid_number':'原始数值不能解析。核对数字与单位，缺失值不填零。',
        'nonfinite_number':'数值不能是无穷大或NaN。回到原件核对，缺失值保留为空。',
    }
    rows = []
    for error in errors:
        issue = str(error.get('issue','unknown'))
        rows.append({'位置': 'CSV第'+str(error['line'])+'行（含表头）' if 'line' in error else '同口径记录组',
            '需要处理':explanations.get(issue,'核对模板必填字段、日期、期间口径和来源。详细问题代码：'+issue)})
    return rows


def render_snapshot(path, meta, key):
    import pandas as pd
    import streamlit as st
    summary = overview(path,meta)
    if summary['synthetic']:
        st.warning('这条记录含合成样例：样例部分仅演示流程和计算，不代表真实公司、真实数据或收益。')
    overview_tab, report_tab, files_tab = st.tabs(['结果与下一步','报告正文','下载文件'])
    with overview_tab:
        if summary['facts']:
            st.table(pd.DataFrame(summary['facts']))
        if summary['financial_problems']:
            st.markdown('**待修正的财务字段**')
            st.table(pd.DataFrame(summary['financial_problems'][:10]))
            if len(summary['financial_problems']) > 10:
                st.caption('这里显示前10项；完整问题见下载文件中的财务校验明细。')
        st.markdown('**下一步**')
        for step in summary['next_steps']:
            st.write('• ' + step)
        for notice in summary['notices']:
            st.warning(notice)
    with report_tab:
        found = False
        for name,label in REPORTS.items():
            try:
                raw = read_output(path,name,256*1024)
                if raw is None:
                    continue
                found = True
                if not raw.decode('utf-8').lstrip().startswith('#'):
                    st.markdown('**'+label+'**')
                render_report(raw.decode('utf-8'))
                st.caption('预览最多20,000字符；下载文件保留全文。')
            except (ValueError,OSError,UnicodeError):
                st.warning(label+' 未能预览，请核对成果文件。')
        if not found:
            st.info('这次没有生成报告正文。可在“下载文件”查看已保存的表格或明细。')
    with files_tab:
        found = False
        for name,label in FILES.items():
            try:
                raw = read_output(path,name)
                if raw is None:
                    continue
                found = True
                st.download_button('下载'+label,raw,file_name=name,key=key+'_'+name,
                    help=f'{name} · {len(raw):,} 字节')
            except (ValueError,OSError):
                st.warning(label+' 无法单独下载，请检查文件或使用成果 ZIP。')
        if not found:
            st.info('尚无可单独下载的成果文件。完整 ZIP 仍可保留本次记录。')
