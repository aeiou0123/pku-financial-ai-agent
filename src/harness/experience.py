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
:root { --paper:#fff; --ink:#25272b; --muted:#62666b; --line:#dededb; --accent:#763b32; }
.stApp { background:var(--paper); color:var(--ink); }
html, body, [data-testid="stAppViewContainer"] { font-family:'Microsoft YaHei','PingFang SC',sans-serif; }
[data-testid="stHeader"] { background:rgba(255,255,255,.96); }
[data-testid="stAppDeployButton"], #MainMenu { display:none; }
[data-testid="stMainBlockContainer"] { max-width:1140px; padding:2.5rem 3.2rem 4rem; }
[data-testid="stMain"] [data-testid="stVerticalBlock"] { gap:.8rem; }
[data-testid="stMarkdownContainer"] p { font-size:14px; line-height:1.8; }
[data-testid="stMarkdownContainer"], input, textarea, [data-baseweb="select"] { font-family:'Microsoft YaHei','PingFang SC',sans-serif; }
.stMain h1, .c2v-page-title h1 { font:600 28px/1.5 'SimSun','Songti SC',serif; letter-spacing:.5px; color:var(--ink); padding:0 0 10px; }
.stMain h2 { font-size:20px; font-weight:600; }
.stMain h3 { font-size:17px; font-weight:600; }
.c2v-description { color:var(--muted); font-size:14px; margin:0 0 8px; }
.c2v-kicker:empty, .c2v-page-code { display:none; }
.c2v-section { display:flex; align-items:baseline; justify-content:space-between; gap:12px; border-bottom:1px solid var(--line); margin:16px 0 10px; padding-bottom:9px; }
.c2v-section h2 { font-size:17px; margin:0; padding:0; }
.c2v-section span { color:var(--muted); font-size:12px; }
[data-testid="stSidebar"] { background:#f3f3f0; border-right:1px solid var(--line); }
[data-testid="stSidebarContent"] { padding-top:1rem; }
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap:1rem; }
.c2v-brand { padding:8px 0 20px; border-bottom:2px solid var(--ink); }
.c2v-brand-name { font:27px/1.3 Georgia,serif; letter-spacing:-.8px; color:var(--ink); }
.c2v-brand-sub { margin-top:6px; font-size:12px; color:var(--muted); }
[data-testid="stSidebar"] [role="radiogroup"] { gap:3px; }
[data-testid="stSidebar"] [data-testid="stRadio"], [data-testid="stSidebar"] [data-testid="stRadioGroup"] { width:100%; align-items:stretch; }
[data-testid="stSidebar"] [data-testid="stRadioGroup"] > div { min-width:100%; }
[data-testid="stSidebar"] [data-testid="stRadioOption"] { padding:6px 8px; border-left:2px solid transparent; min-width:100%; border-radius:0; }
[data-testid="stSidebar"] .st-key-desk_page [data-testid="stRadioOption"] > div > div:first-child { display:none; }
[data-testid="stSidebar"] .st-key-desk_page [data-testid="stRadioOption"] { padding:8px 12px; }
[data-testid="stRadioOption"][data-selected="true"] > div > div:first-child { background:var(--accent); }
[data-testid="stSidebar"] [data-testid="stRadioOption"]:has(input:checked) { background:#e7e7e2; border-left-color:var(--accent); }
[data-testid="stSidebar"] [data-testid="stRadioOption"]:focus-within { outline:2px solid var(--accent); outline-offset:2px; }
[data-testid="stWidgetLabel"] p { font-size:13px; color:var(--ink); }
[data-testid="stCaptionContainer"], .desk-meta { color:var(--muted); font-size:12px; }
[data-baseweb="select"] > div, [data-baseweb="input"], [data-baseweb="textarea"] { background:#fafaf8; border-color:#c9cbc7; border-radius:3px; }
[data-baseweb="input"] > div, [data-baseweb="textarea"] > div { background:#fafaf8; }
[data-baseweb="textarea"] textarea { font-size:14px; line-height:1.7; }
[data-testid="stBaseButton-primary"], [data-testid="stBaseButton-primaryFormSubmit"] { background:var(--ink); color:#fff; border-color:var(--ink); border-radius:3px; }
[data-testid="stBaseButton-primary"]:hover, [data-testid="stBaseButton-primaryFormSubmit"]:hover { background:#45474a; color:#fff; border-color:#45474a; }
[data-testid="stBaseButton-secondary"], [data-testid="stBaseButton-secondaryFormSubmit"] { background:transparent; border-color:#bfc1be; border-radius:3px; color:var(--ink); }
[data-testid^="stBaseButton"]:focus-visible { outline:2px solid var(--accent); outline-offset:3px; box-shadow:none; }
[data-testid="stBaseButton-primary"] [data-testid="stMarkdownContainer"], [data-testid="stBaseButton-primaryFormSubmit"] [data-testid="stMarkdownContainer"] { color:inherit; }
[data-testid="stForm"], [data-testid="stExpander"], [data-testid="stVerticalBlockBorderWrapper"] { border-radius:3px; border-color:var(--line); box-shadow:none; }
[data-testid="stForm"] { padding:18px; }
[data-testid="stFileUploaderDropzone"] { border-radius:3px; background:#fafaf8; border:1px dashed #bec1bb; }
[data-testid="stAlert"] { border-radius:3px; }
[data-testid="stMetricValue"] { font-variant-numeric:tabular-nums; font-size:28px; }
.desk-home-rule { border-top:2px solid var(--ink); margin:12px 0 0; }
.desk-list-label { color:var(--muted); font-size:12px; padding:9px 0; border-bottom:1px solid var(--line); }
.desk-row-index { color:var(--accent); font:12px/1.6 Consolas,'Microsoft YaHei',sans-serif; margin-bottom:8px; }
.desk-row-question { color:var(--muted); font-size:13px; line-height:1.8; margin:8px 0 0; }
.desk-row-label { color:var(--muted); font-size:12px; margin:1px 0 8px; }
.desk-row-value { font-size:14px; line-height:1.8; }
[class*="st-key-task_row_"] { padding:18px 0; border-bottom:1px solid var(--line); }
[class*="st-key-start_"] button { border:none; padding:0; min-height:28px; background:transparent; border-radius:0; text-align:left; justify-content:flex-start; }
[class*="st-key-start_"] button p { font-size:18px; font-weight:600; text-decoration:underline; text-decoration-color:#b1b3ae; text-underline-offset:6px; }
[class*="st-key-start_"] button:hover { background:transparent; color:var(--accent); }
.desk-steps { display:flex; margin:8px 0 16px; gap:12px; }
.desk-step { flex:1; border-bottom:1px solid var(--line); padding:8px 0; color:var(--muted); font-size:12px; }
.desk-step.current { border-color:var(--ink); color:var(--ink); font-weight:600; }
.desk-step.done { color:#414b41; }
.st-key-first_use { padding:18px 0 8px; }
.st-key-tutorial_steps, .st-key-tutorial_calculation { padding:12px 0 20px; border-top:1px solid var(--line); }
.desk-intro-title { font-size:15px; font-weight:600; margin-bottom:6px; }
.desk-intro-copy { font-size:13px; color:var(--muted); line-height:1.8; }
@media(max-width:800px) {
 [data-testid="stMainBlockContainer"] { padding:2rem 1.2rem 3rem; }
 .stMain h1, .c2v-page-title h1 { font-size:26px; }
 .desk-steps { flex-wrap:wrap; gap:4px 16px; }
 .desk-step { min-width:40%; }
 [class*="st-key-task_row_"] [data-testid="stHorizontalBlock"] { gap:16px; }
 .desk-row-label { margin-bottom:3px; }
 .c2v-section { flex-wrap:wrap; }
}
@media(prefers-reduced-motion:reduce) { *, *::before, *::after { transition:none !important; animation:none !important; } }
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
    st.title('研究工作台')
    st.write('上传资料，核对出处，保存研究底稿。')
    st.markdown('<div class="desk-home-rule"></div><div class="desk-list-label">新建研究 · 选择一项任务</div>', unsafe_allow_html=True)
    for index, (key, item) in enumerate(TASKS.items(), 1):
        with st.container(key='task_row_' + key):
            task, materials, outputs = st.columns([1.2, 1.2, 1.4], gap='large')
            with task:
                st.markdown(f'<div class="desk-row-index">0{index} / {escape(item["audience"].split("、")[0])}</div>', unsafe_allow_html=True)
                st.button(item['title'], key='start_' + key, on_click=select_task, args=(key,))
                st.markdown('<div class="desk-row-question">' + escape(item['question']) + '</div>', unsafe_allow_html=True)
            for column, label, text in [(materials, '所需材料', item['input']), (outputs, '输出内容', item['output'])]:
                with column:
                    st.markdown(f'<div class="desk-row-label">{label}</div><div class="desk-row-value">{escape(text)}</div>', unsafe_allow_html=True)
    with st.container(key='first_use'):
        text, action = st.columns([3, 1.4], vertical_alignment='center')
        with text:
            st.markdown('<div class="desk-intro-title">第一次使用</div><div class="desk-intro-copy">用合成材料走一遍流程。教程包含样例文件、可复制的提问和无需 API 的计算。</div>', unsafe_allow_html=True)
        with action:
            st.button('打开教程与样例', on_click=lambda: st.session_state.update(desk_page='教程与示例'))
    with st.expander('使用范围与数据去向'):
        st.write('本地核验和回测无需模型。自动整理和证据检查使用你配置的模型；点击调用时，相关文字会发送给该服务。上传原件保存在本机。当前不含在线数据库查询和自动交易。')


def guide(root):
    st.title('教程与示例')
    st.write('先看一遍流程，再用样例走通。所有示例均为合成数据，不代表任何公司的研究结论或真实收益。')
    selected = st.selectbox('我想学习的任务', list(TASKS), format_func=lambda k: TASKS[k]['title'])
    item = TASKS[selected]
    steps(0)
    with st.container(key='tutorial_steps'):
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
        with st.container(key='tutorial_calculation'):
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
