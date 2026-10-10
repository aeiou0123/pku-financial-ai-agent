"""Task-first navigation, local examples and readable saved results."""
from __future__ import annotations

from .module_stamp import source_stamp
_c2v_loaded_source_hash = source_stamp(__file__)

from datetime import date
from html import escape
import io
import json
from pathlib import Path
import re
import zipfile

import pandas as pd
import streamlit as st

from .documents import digest, table
from .quant import prepare, backtest, save
from .conditions import forward, save_conditions
from .store import Run

TASKS = {
    'industry': {'title': '检查研究观点', 'direction': '财务／估值研究', 'mode': '论点审查与兑现条件',
        'audience': '产业研究、投研学习', 'question': '扩产计划能否支持未来两年的增长？',
        'input': '公告、年报、技术材料；实际披露日期',
        'output': '支持材料、反证、缺口和原文定位',
        'files': ['synthetic_industry.txt', 'synthetic_industry_counterevidence.txt'],
        'prompt': '请检查公司甲新增减速器产能能否支持未来两年的增长，核对投产、订单、售价和成本，并列支持材料、反证和缺口。'},
    'financial': {'title': '整理财务数据', 'direction': '财务／估值研究', 'mode': '财务整理与盈利解释',
        'audience': '财务分析、研究助理', 'question': '利润为什么变了，数字来自哪里？',
        'input': '年报，或财务长表及对应原件',
        'output': '核验表、历史比率；字段齐备时分解盈利变化',
        'files': ['synthetic_financial.txt', 'synthetic_financial.csv'],
        'prompt': '核对2024年合并报表的收入、成本、总资产与负债，保留真实披露日期、单位和原文定位。'},
    'quant': {'title': '测试策略表现', 'direction': '量化处理与回测', 'mode': '',
        'audience': '量化研究、课程项目', 'question': '计入费用后，策略表现和风险如何？',
        'input': 'CSV／Excel：日期、股票代码、已复权收盘价',
        'output': '净值、回撤、费用、持仓和同费率基准',
        'files': ['synthetic_prices.csv'],
        'prompt': '用20日价格动量测试策略，持有2只股票，单边费率10bps；对比同费率基准，说明回撤和费用。'}
}

FIELD_LABELS = dict(zip(
    ['stock_code','company','report_period','published_at','statement_scope','period_type','metric_original','canonical_metric',
     'value_original','unit','currency','revision_flag','source_database','source_file','source_locator','source_sha256'],
    ['股票代码','公司','报告期','实际披露日','报表范围','期间口径','原指标名称','标准指标','原始数值','金额单位','币种','更正版本','来源类别','原件文件','原文位置','文件指纹']))

STATUS = {'created':'已建立记录','documents_parsed':'材料已读取','extracting':'正在整理候选',
    'extraction_partial':'部分完成，可继续','extraction_interrupted':'提取中断，已有结果保留',
    'awaiting_review':'候选待核对','financial_completed':'财务结果已生成','financial_blocked':'财务字段待修正',
    'valuation_completed':'假设估值已生成','quant_completed':'回测已完成','quant_failed':'回测未完成',
    'thesis_review_awaiting_human_confirmation':'观点检查已完成，待核对','thesis_review_interrupted':'观点检查部分完成',
    'realization_conditions_computed':'情景计算已完成'}

STYLE = '''<style>
:root { --paper:#f7f8fa; --ink:#182a3a; --muted:#596a79; --line:#dce3ea; --pine:#245b87; }
.stApp { background:#f7f8fa; }
[data-testid="stSidebar"] { background:#fff; }
[data-testid="stMainBlockContainer"] { max-width:1220px; padding:2.4rem 3rem 4rem; }
.c2v-page-title h1 { font:600 30px/1.4 'Microsoft YaHei','PingFang SC',sans-serif; letter-spacing:0; }
.c2v-brand-name { font:600 24px/1.4 'Microsoft YaHei',sans-serif; letter-spacing:-.5px; }
.c2v-brand-sub { letter-spacing:0; font-size:13px; }
.stMain h1 { font:600 30px/1.45 'Microsoft YaHei','PingFang SC',sans-serif; }
.stCaption, [data-testid="stCaptionContainer"] { color:#526575 !important; }
.desk-delivery { min-height:50px; font-size:14px; line-height:1.8; margin:4px 0 10px; }
.c2v-page-code { display:none; }
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap:.8rem; }
[data-testid="stSidebar"] [data-testid="stRadioOption"]:has(input:checked) { background:#eaf1f8; }
[data-testid="stWidgetLabel"] p { font-size:13px; color:#31485a; }
[data-testid="stVerticalBlockBorderWrapper"] { background:#fff; border-radius:9px; }
[data-testid="stBaseButton-primary"], [data-testid="stBaseButton-primaryFormSubmit"] { background:#245b87; border-color:#245b87; border-radius:6px; }
[data-testid="stBaseButton-primary"]:hover { background:#194567; border-color:#194567; }
[data-testid="stForm"] { background:#fff; border-radius:8px; }
[data-testid="stExpander"] { background:#fff; border-radius:7px; }
.desk-task h3 { font-size:19px; margin:8px 0 14px; }
.desk-task .audience { color:#596a79; font-size:12px; }
.desk-task p { font-size:14px; line-height:1.8; }
.desk-steps { display:flex; margin:12px 0 22px; gap:8px; }
.desk-step { flex:1; border-top:3px solid #dce3ea; padding:10px 4px; color:#596a79; font-size:13px; }
.desk-step.current { border-color:#245b87; color:#193d59; font-weight:600; }
.desk-step.done { border-color:#91b2a2; }
@media(max-width:800px) { [data-testid="stMainBlockContainer"] { padding:2rem 1rem; } .desk-steps { flex-wrap:wrap; } .desk-step { min-width:40%; } }
</style>'''


def select_task(task, sample=False):
    settings = TASKS[task]
    st.session_state.update(desk_page='工作区', desk_direction=settings['direction'], desk_task=settings['mode'] or '论点审查与兑现条件',
                            desk_example=task if sample else None, task_text=settings['prompt'] if sample else '')
    st.session_state['desk_upload_generation'] = st.session_state.get('desk_upload_generation', 0) + 1
    for key in ('enable_conditions', 'enable_dcf', 'enable_strategy_diagnostics'):
        st.session_state[key] = False
    if sample and task == 'industry':
        st.session_state.update(research_company='公司甲', research_product='减速器')


def steps(current, labels=('说明问题', '准备材料', '核对与运行', '查看成果')):
    parts = [f'<div class="desk-step {"current" if i == current else "done" if i < current else ""}">{i+1} · {escape(label)}</div>'
             for i, label in enumerate(labels)]
    st.markdown('<div class="desk-steps">' + ''.join(parts) + '</div>', unsafe_allow_html=True)


def stage(state, uploads, question):
    if any(state.get(key) for key in ('result','research_review','candidates','dcf_result','conditions_result','financial_result')):
        return 3
    return 2 if uploads and question.strip() else 1 if question.strip() else 0


def home():
    st.title('从一个研究问题开始')
    st.write('为产业投研、财务分析和量化学习整理可追溯的研究底稿。选择任务后，页面会告诉你需要什么材料、下一步做什么。')
    for column, (key, item) in zip(st.columns(3), TASKS.items()):
        with column.container(border=True):
            st.markdown(f'<div class="desk-task"><div class="audience">{escape(item["audience"])}</div><h3>{escape(item["title"])}</h3><p>{escape(item["question"])}</p></div>', unsafe_allow_html=True)
            st.caption('你提供')
            st.markdown('<div class="desk-delivery">' + escape(item['input']) + '</div>', unsafe_allow_html=True)
            st.caption('你得到')
            st.markdown('<div class="desk-delivery">' + escape(item['output']) + '</div>', unsafe_allow_html=True)
            st.button(item['title'], key='start_' + key, type='primary', width='stretch', on_click=select_task, args=(key,))
    with st.container(border=True):
        st.subheader('第一次使用')
        st.write('先做一次无需API的样例计算，理解输入、输出和限制；再把自己的材料带进工作区。')
        st.button('打开教程与样例', on_click=lambda: st.session_state.update(desk_page='教程与示例'))
    st.caption('本地计算无需模型。自动整理和证据检查需要你配置的模型服务；点击调用时，相关文字会发送给该服务。当前不含在线数据库查询和自动交易。')


def guide(root):
    st.title('教程与示例')
    st.write('先看一遍流程，再用样例走通。所有示例均为合成数据，不代表任何公司的研究结论或真实收益。')
    selected = st.selectbox('我想学习的任务', list(TASKS), format_func=lambda k: TASKS[k]['title'])
    item = TASKS[selected]
    steps(0)
    with st.container(border=True):
        st.subheader(item['title'])
        st.write('1. 准备：' + item['input'] + '。')
        st.write('2. 写清公司、期间或策略规则，按提示核对来源和字段。')
        st.write('3. 运行后检查缺口；模型候选需对照原件，未来参数需自行确认。')
        st.write('4. 下载：' + item['output'] + '；在“成果记录”找回本机已保存的输出。')
        st.code(item['prompt'], language=None)
        st.button('用这组样例进入工作区', type='primary', on_click=select_task, args=(selected, True))
        for name in item['files']:
            st.download_button('下载样例 · ' + name, (root/'docs/harness/examples'/name).read_bytes(), file_name=name)
    if selected in {'industry', 'quant'}:
        with st.container(border=True):
            st.subheader('无需API，先做一次实际计算')
            st.caption('使用现有本地计算工具，不产生模型证据；点击后保留合成输入、参数和结果。')
            if selected == 'industry':
                multiplier = st.slider('销量相对基准的倍数', .5, 2., 1., .1)
                st.write('假设原有产能10万台／年；基准首年销量6万台，未来每年增长10%。其他现金流参数固定为演示假设。')
            else:
                multiplier = None
                st.write('合成价格表，20日价格动量，持有2只股票，单边费率10bps；按工作台既有交易与扣费规则计算。')
            if st.button('运行本地样例', key='offline_' + selected):
                run = offline_example(root, selected, multiplier)
                st.session_state['tutorial_result'] = (selected, multiplier, run.path.name)
            result = st.session_state.get('tutorial_result')
            if result and result[:2] == (selected, multiplier):
                path = root/'work/harness_runs'/result[2]
                if selected == 'industry':
                    data = json.loads((path/'outputs/realization_conditions.json').read_text(encoding='utf-8'))['forward']
                    if data['enterprise_value'] is None:
                        st.error('当前销量假设触及约束，暂缓估值。')
                    else:
                        st.metric('假设业务价值（元）', f"{data['enterprise_value']:,.0f}")
                    for conflict in data['conflicts']:
                        st.write(conflict)
                    st.caption('降低销量或提供真实可核对的新增产能依据后，才能检查新的情景。')
                else:
                    metrics = json.loads((path/'outputs/metrics.json').read_text(encoding='utf-8'))
                    st.metric('合成样本净收益', f"{metrics['total_return']:.2%}")
                    st.metric('最大回撤', f"{metrics['max_drawdown']:.2%}")
                st.download_button('下载样例计算记录', saved_bundle(root/'work/harness_runs', result[2]), file_name='合成样例计算.zip')
    with st.expander('常见问题与术语'):
        for question, answer in [
            ('没有API能做什么？','编辑研究清单、导入标准财务表进行本地核验、计算自行确认的情景、运行回测。自动提取和证据检查需要模型。'),
            ('为什么要填实际披露日？','它决定信息在研究截止日是否已公开。2024-12-31可能是报告期，不能当年报实际发布日。找不到日期就留空。'),
            ('按钮灰色怎么办？','按钮旁会列出缺项。通常需补公司、真实日期、可用材料，或确认本次清单；修改输入后要重新确认。'),
            ('模型连接成功，但研究失败？','小测试与长任务不同。查看脱敏说明和批次缺口；可调等待时间，继续会复用相同输入的成功部分。'),
            ('回测费率bps是什么意思？','1bps是0.01%；10bps是0.10%的单边费率。费用按实际双向换手计算。'),
            ('FCFF、折现率和永续增长率是什么？','FCFF是企业自由现金流。折现率表示把未来现金流换算成今天价值的比率；永续增长率用于末年之后，必须低于折现率。'),
            ('能直接得到投资建议吗？','当前输出是研究底稿和用户假设下的计算。证据匹配不保证语义正确，回测也未模拟所有交易约束。'),
            ('材料和密钥存在哪里？','上传原件与结果保存在本机。密钥只在当前会话中使用；研究调用会发送相关文字。成果ZIP排除原件和密钥，仍可能含原文摘录。')]:
            st.markdown('**' + question + '**')
            st.write(answer)


def offline_example(root, task, multiplier=None):
    examples = root/'docs/harness/examples'
    if task == 'quant':
        name = 'synthetic_prices.csv'
        raw = (examples/name).read_bytes()
        run = Run(root/'work/harness_runs', 'tutorial_quant', [(name, raw)])
        data = prepare(table(raw, name), {'date':'date','stock':'stock','close':'close'}, 'momentum')
        result = backtest(data, strategy='momentum', lookback=20, top_n=2, fee_bps=10., direction='high')
        save(run, data, result)
    else:
        run = Run(root/'work/harness_runs', 'tutorial_conditions', [])
        model = {'company':'合成示例公司','product':'合成减速器业务','cutoff':'2026-10-10',
            'rows':[{'year':2026+i,'units':60000*1.1**(i-1)*float(multiplier),'asp_yuan':2000.,'unit_cost_yuan':1200.,
                     'existing_capacity':100000.,'incremental_capacity':0.,'commissioning_date':'','confirmed_orders':''} for i in range(1,6)],
            'opex_ratio':.15,'depreciation_ratio':.03,'tax_rate':.25,'capex_ratio':.05,'nwc_ratio':.2,'opening_nwc':20000000.,
            'stub_fcff':0.,'discount_rate':.1,'terminal_growth':.02,'whole_company':False,'bindings':[]}
        save_conditions(run, forward(model), None, [])
    run.write('example_notice.md', '# 合成样例\n\n仅使用本地工具演示计算；没有模型证据，不代表真实公司或收益。')
    return run


def saved_runs(root, limit=40):
    rows = []
    if not root.exists():
        return rows
    for path in sorted(root.iterdir(), reverse=True):
        if not re.fullmatch(r'\d{8}_\d{6}_[a-f0-9]{10}', path.name) or path.is_symlink() or not path.is_dir():
            continue
        meta = path/'run.json'
        if meta.is_symlink() or not meta.is_file() or meta.stat().st_size > 100000:
            continue
        try:
            data = json.loads(meta.read_text(encoding='utf-8'))
            if (data.get('id') != path.name or not isinstance(data.get('inputs'), list)
                    or not all(isinstance(item, dict) for item in data['inputs'])
                    or not isinstance(data.get('workflow'), str) or not isinstance(data.get('status'), str)):
                continue
            rows.append(data)
        except (ValueError, OSError, AttributeError):
            continue
        if len(rows) >= limit:
            break
    return rows


def saved_bundle(root, run_id):
    if not re.fullmatch(r'\d{8}_\d{6}_[a-f0-9]{10}', run_id):
        raise ValueError('运行编号不合法。')
    path = root/run_id
    if path.is_symlink() or path.resolve().parent != root.resolve():
        raise ValueError('运行目录不可读取。')
    outputs = path/'outputs'
    if outputs.is_symlink():
        raise ValueError('结果目录不可读取。')
    files = list(outputs.glob('*')) + [path/'run.json', path/'events.jsonl']
    files = [p for p in files if p.is_file() and not p.is_symlink() and p.resolve().is_relative_to(path.resolve())]
    manifest, buffer = {}, io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
        for file in files:
            name, raw = file.relative_to(path).as_posix(), file.read_bytes()
            archive.writestr(name, raw)
            manifest[name] = {'sha256':digest(raw),'bytes':len(raw)}
        archive.writestr('manifest.json', json.dumps(manifest, ensure_ascii=False, indent=2))
    return buffer.getvalue()


def history(root):
    st.title('成果记录')
    st.write('找回这台电脑保存的研究输出。这里可以下载历史快照；继续模型任务仍需保留原来的浏览器会话。')
    runs_root = root/'work/harness_runs'
    records = saved_runs(runs_root)
    if not records:
        st.info('还没有成果。先打开教程运行一次本地样例，或进入工作区处理自己的材料。')
        return
    labels = {'industry_research':'观点检查','financial':'财务整理','quant':'策略回测','realization_conditions':'情景估值',
              'tutorial_quant':'合成回测样例','tutorial_conditions':'合成估值样例','valuation':'现金流估值','strategy_diagnostics':'策略诊断'}
    chosen = st.selectbox('选择本机保存的记录（最近40条）', range(len(records)),
        format_func=lambda i: records[i]['id'] + ' · ' + labels.get(records[i]['workflow'],'研究记录') + ' · ' + STATUS.get(records[i]['status'],'处理记录'))
    metadata = records[chosen]
    st.write('输入：' + ('、'.join(str(item.get('name','')) for item in metadata['inputs']) or '本地合成假设'))
    st.caption('输出只对应这次快照。分享前请核对商业数据和原文摘录的权限。')
    st.download_button('下载这次记录', saved_bundle(runs_root, metadata['id']), file_name='Claim2Value_' + metadata['id'] + '.zip')


def task_help(task):
    item = TASKS[task]
    st.caption('预期成果：' + item['output'] + '。')
    with st.expander('这一步怎么做？'):
        st.write('准备：' + item['input'] + '。')
        st.write('问题示例：' + item['prompt'])
        st.write('上传后按页面提示核对。没有字段或证据就保留缺口；不把未来计划改写成已发生的事实。')
