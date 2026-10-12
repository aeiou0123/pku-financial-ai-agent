"""Human-readable research outputs computed exclusively from saved tool results."""
from __future__ import annotations
from .module_stamp import source_stamp
_c2v_loaded_source_hash = source_stamp(__file__)

import math


def cell(value):
    if value is None:
        return '未提供'
    return str(value).replace('\\','\\\\').replace('|','\\|').replace('\r',' ').replace('\n',' ')


def number(value,percent=False):
    if value is None or isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value):
        return '未计算'
    return f'{value:.2%}' if percent else f'{value:,.2f}'


def table(headers,rows):
    return '\n'.join(['| '+' | '.join(cell(s) for s in headers)+' |','| '+' | '.join('---' for _ in headers)+' |'] +
        ['| '+' | '.join(cell(s) for s in row)+' |' for row in rows])


def financial_report(as_of,normalized,quality,ratios,coverage=None):
    status='格式核验通过' if quality['status']=='checked' else '格式核验通过，存在缺项或未完成的检查'
    lines=['# 财务核验底稿','',table(['项目','本次记录'],[['研究截止日',as_of.isoformat()],['标准化记录',len(normalized)],
        ['状态',status],['缺失提示',len(quality['warnings'])]]),'',
        '本地检查核对格式和文件指纹；来源、摘录、披露日与字段映射仍须对照原件。','', '## 历史比率','',
        '不同披露日、报表范围、更正版本和期间分别计算。没有自动年化、差分或更新预测。','']
    names={'liabilities/assets':'资产负债率','gross_margin':'毛利率','parent_net_margin':'归母净利率'}
    periods={'annual':'年度','cumulative':'累计中期','single_quarter':'单季度','point_in_time':'期末时点'}
    if ratios:
        rows=[[r['company'],r['report_period'],r['published_at'],'合并' if r['statement_scope']=='consolidated' else '母公司',
            r['revision_flag'],periods.get(r['period_type'],r['period_type']),names.get(r['ratio'],r['ratio']),number(r['value'],True)] for r in ratios[:50]]
        lines += [table(['公司','报告期','披露日','报表','版本','期间','比率','结果'],rows)]
        if len(ratios)>50:
            lines += ['', '正文仅列前50项；完整比率在financial.xlsx和historical_ratios.csv。']
    else:
        lines += ['本次字段未形成可计算的历史比率。核对所需收入、成本、利润或资产负债字段，缺值不补零。']
    if coverage:
        lines+=['','## 提取范围','',f"完成{coverage['completed_batches']}／{coverage['total_batches']}批。"+
            ('仍有未完成批次，仅覆盖已确认的部分候选，不是全文审查。' if not coverage['complete'] else '表示解析范围内批次已处理，不认证字段或原件。')]
    lines+=['','## 底稿文件','','财务长表与比率：financial.xlsx；校验明细：quality_report.json；来源索引：source_index.json。上传原件留在本机。']
    return '\n'.join(lines)+'\n'


def quant_report(result):
    m,daily = result['metrics'],result['daily']
    benchmark = float(daily['benchmark_nav'].iloc[-1]-1)
    settings = [['策略','价格动量' if m['strategy']=='momentum' else '已有因子排序'],
        ['动量窗口',str(m['lookback'])+'个样本交易日' if m['strategy']=='momentum' else '不适用'],
        ['持仓数',m['top_n']],['排序','取较高值' if m['direction']=='high' else '取较低值'],
        ['单边费率',number(m['fee_bps_single_side'])+' bps']]
    results = [['评估区间',daily.index[0].date().isoformat()+' 至 '+daily.index[-1].date().isoformat()],
        ['评估日数／股票数',str(m['days'])+'／'+str(m['stocks'])],['策略净收益',number(m['total_return'],True)],
        ['同费率等权基准净收益',number(benchmark,True)],['最大回撤',number(m['max_drawdown'],True)],
        ['年化Sharpe（零无风险利率，252日）',number(m['sharpe_zero_rf_252'])]]
    return '# 回测记录\n\n仅对应上传样本和本次参数，不是样本外收益或比赛测试成绩。\n\n## 本次设置\n\n'+table(['参数','采用值'],settings)+\
        '\n\n## 样本结果\n\n'+table(['指标','结果'],results)+\
        '\n\n## 成交与费用\n\nT日收盘后确定信号，T+1日收盘成交，T+2日计入第一笔持仓收益。策略和基准采用同一单边费率；费用按双向换手扣除。样本末尾不强制清仓。\n\n## 需要核对\n\n'+\
        '\n'.join('- '+cell(s) for s in m['limitations'])+'\n\n## 底稿文件\n\n每日净值与费用：daily.csv；持仓：positions.csv；因子相关性：rank_ic.csv；输入快照：cleaned_data.csv。\n'


def conditions_report(result,reverse_result=None):
    m=result['model']
    conflict=bool(result['conflicts'])
    values=[['研究截止日',m['cutoff']],['公司／业务',m['company']+'／'+m['product']],
        ['状态','约束冲突，暂缓估值' if conflict else '用户假设下的情景计算'],
        ['假设企业价值（元）','未计算：存在约束冲突' if conflict else number(result['enterprise_value'])],
        ['折现率',number(m['discount_rate'],True)],['永续增长率',number(m['terminal_growth'],True)]]
    years=[[r['year'],number(r['units']),number(r['available_capacity']),number(r['revenue']),number(r['fcff'])] for r in result['years']]
    text='# 盈利与估值情景\n\n销量、售价、成本和现金流来自用户确认的假设，不是已经实现的业绩。\n\n'+table(['项目','本次采用'],values)+\
        '\n\n## 年度预测\n\n金额单位为元；产量和可售产能单位为台。缺失产能显示为未计算。\n\n'+table(['年度','假设销量','可售产能','收入','企业自由现金流'],years)
    for heading,items,empty in [('约束冲突',result['conflicts'],'本次规则没有发现约束冲突；仍需核对假设。'),
                               ('证据缺口',result['gaps'],'本次计算没有记录证据缺口；这不认证来源。'),
                               ('口径与局限',result['limitations'],'未记录')]:
        text+='\n\n## '+heading+'\n\n'+('\n'.join('- '+cell(s) for s in items) if items else empty)
    if reverse_result:
        labels={'conditional_feasible_target':'在声明的搜索范围内找到条件解','no_feasible_search_interval':'没有可行搜索区间',
            'target_outside_feasible_sampled_range':'目标超出本次可行抽样范围'}
        text+='\n\n## 目标反推\n\n'+table(['项目','结果'],[['状态',labels.get(reverse_result['status'],'请查看反推明细')],
            ['用户目标',number(reverse_result.get('target'))],['条件解对应值',number(reverse_result.get('achieved'))]])
        text+='\n\n反推依赖本次假设和搜索范围，不表示现实中可以实现。完整参数与敏感性保存在realization_conditions.xlsx和realization_conditions.json。'
    return text+'\n'


def dcf_report(result):
    rows=[[i+1,number(value),number(result['discounted_fcf'][i])] for i,value in enumerate(result['fcf'])]
    values=[['折现率',number(result['discount_rate'],True)],['永续增长率',number(result['terminal_growth'],True)],
        ['企业价值（元）',number(result['enterprise_value'])],['净债务（元）','未提供' if result['net_debt'] is None else number(result['net_debt'])],
        ['股权价值（元）','未计算：未提供净债务' if result['net_debt'] is None else number(result['equity_value'])]]
    return '# 现金流假设估值\n\n五年企业自由现金流由用户输入，不是从历史报表直接推算的预测。金额单位为元。\n\n'+\
        table(['项目','本次采用'],values)+'\n\n## 五年现金流\n\n'+table(['预测年序','假设现金流','折现值'],rows)+\
        '\n\n## 估值口径\n\n第1年至第5年按完整年度折现，末年后采用永续增长。未计入非经营资产、少数股东权益等调整；不自动计算每股目标价。\n\n## 敏感性底稿\n\n假设与中间值：valuation_assumptions.json；折现率与增长率组合：valuation_sensitivity.csv。\n'


def strategy_report(report):
    interval=report['common_interval']
    rows=[[r['index']+1,r['lookback'],r['top_n'],number(r['fee_bps']),number(r['net_return'],True),
           number(r['benchmark_net_return'],True),number(r['max_drawdown'],True)] for r in report['comparisons']]
    text='# 策略参数比较\n\n参数按事先声明的顺序列出，没有挑选最佳组。比较不是样本外有效性的证据。\n\n'+\
        table(['共同持仓收益区间','记录'],[['起止日期',interval['start']+' 至 '+interval['end']],['共同日数',interval['days']],['失败参数组',len(report['failures'])]])+\
        '\n\n## 参数与共同区间结果\n\n'+table(['组号','窗口','持仓数','单边bps','策略净收益','等权基准','最大回撤'],rows)
    if report['failures']:
        text+='\n\n## 失败组\n\n'+table(['组号','失败原因'],[[r['index']+1,r['reason']] for r in report['failures']])
    text+='\n\n## 比较边界\n\n'+'\n'.join('- '+cell(s) for s in report['limitations'])
    return text+'\n\n年度分段、完整生命周期收益和共同区间净值见strategy_diagnostics.xlsx；完整设置与已查看区间登记见strategy_diagnostics.json。\n'


def thesis_report(context,assessments):
    statuses={'conflicting_candidates':'支持与反证并存，待核对','candidate_review_required':'有摘录候选，待核对',
              'not_covered_in_selected_material':'本次所选材料未覆盖'}
    stances={'supports':'支持候选','contradicts':'反证候选','context':'背景材料'}
    types={'historical':'历史事实候选','forecast':'预测或目标','commitment':'承诺','opinion':'意见'}
    lines=['# 研究观点检查底稿','',cell(context['question']),'','模型摘录和判断均待人工核对。检索只覆盖所选文本片段。','']
    scope=[[label,context[key]] for key,label in [('company','研究公司'),('product','产品／业务'),('cutoff','信息截止日')] if key in context]
    if scope:
        lines += [table(['研究范围','本次采用'],scope),'']
    for a in assessments:
        lines+=['## '+cell(a['condition']['label']),'','状态：'+statuses.get(a['status'],'待核对'),'']
        for row in a['evidence']:
            lines += [stances.get(row['stance'],'待核对')+' · '+types.get(row['fact_type'],'待核对'),
                '', '> '+cell(row['quote']), '', '定位：'+cell(row['source_file'])+' · '+cell(row['source_locator'])+
                (' · 披露日：'+cell(row['metadata']['published_at']) if isinstance(row.get('metadata'),dict) and row['metadata'].get('published_at') else ''),'']
        if not a['evidence']:
            lines+=['没有找到可列出的摘录候选。','']
        lines+=['待补充或核对：']+(['- '+cell(s) for s in a['missing_in_supplied_material']] or ['本条件没有记录材料缺口；仍需核对摘录。'])+['']
    return '\n'.join(lines)
