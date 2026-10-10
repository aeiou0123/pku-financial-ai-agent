"""Industry research desk: explicit scope, reviewed citations and assumption-based conditions."""
from __future__ import annotations

from .module_stamp import source_stamp
_c2v_loaded_source_hash = source_stamp(__file__)

from copy import deepcopy
from datetime import date
import json

import pandas as pd
import streamlit as st

from .conditions import confirm_parameter, forward, reverse, sensitivity, save_conditions, market_cap_to_ev
from .documents import parse, digest, MAX_CHARS, MAX_PAGES
from .research import document_scope, plan_thesis, review_thesis, validate_plan, local_plan
from .store import Run


def render(root, uploads, question, make_client):
    left, right = st.columns(2)
    company = left.text_input('研究公司', placeholder='例如：某公司；与原件名称一致', key='research_company')
    product = right.text_input('产品／业务范围', placeholder='例如：耳机、减速器', key='research_product')
    cutoff = st.date_input('研究信息截止日', value=date.today(), key='research_cutoff')
    file_binding = digest(json.dumps({'files': [(name, digest(data)) for name, data in uploads], 'parse_limits': [MAX_CHARS, MAX_PAGES]}).encode())
    if st.session_state.get('research_parsed_files_binding') != file_binding:
        st.session_state['research_parsed_files'] = [parse(data, name) for name, data in uploads]
        st.session_state['research_parsed_files_binding'] = file_binding
    documents = st.session_state['research_parsed_files']
    st.subheader('文件来源登记')
    st.caption('文件可读取不等于日期已确认。实际披露日期是报告公开的日期，例如半年报的2026-06-30通常是报告期，不是披露日。未知日期留空；下方填写日期和范围并确认后，才进入按截止日审查。')
    if st.session_state.get('desk_example') == 'industry':
        st.info('这组样例的登记信息：公司甲／减速器；第一份披露日2026-01-01，counterevidence文件披露日2026-02-01；来源选“合成测试”。请读过两份材料后分别确认。')
    metadata = []
    # File declarations belong to the uploaded bytes, not the editable research question.
    # Migrate the previous widget keys without asking an existing session to re-enter them.
    legacy_metadata_key = digest(json.dumps([st.session_state['binding'], company, product], ensure_ascii=False).encode())
    for doc in documents:
        suffix = digest(json.dumps([doc['name'], doc['sha256']], ensure_ascii=False).encode()) + doc['source_file']
        legacy_suffix = legacy_metadata_key + doc['source_file']
        for prefix in ('published_', 'kind_', 'source_company_', 'source_product_', 'source_confirm_'):
            if prefix + suffix not in st.session_state and prefix + legacy_suffix in st.session_state:
                st.session_state[prefix + suffix] = st.session_state[prefix + legacy_suffix]
        st.session_state.setdefault('source_company_' + suffix, company)
        st.session_state.setdefault('source_product_' + suffix, product)
        if not st.session_state.get('source_confirm_' + suffix, False):
            if not st.session_state.get('source_company_' + suffix):
                st.session_state['source_company_' + suffix] = company
            if not st.session_state.get('source_product_' + suffix):
                st.session_state['source_product_' + suffix] = product
        with st.container(border=True):
            st.write(doc['name'])
            date_column, kind_column = st.columns(2)
            published = date_column.text_input('披露日期 · ' + doc['name'], placeholder='YYYY-MM-DD；未知则留空', key='published_' + suffix)
            kind = kind_column.selectbox('来源类型 · ' + doc['name'], ['未声明', '公司公告／年报', '技术手册', '研究报告', '其他', '合成测试'], key='kind_' + suffix)
            with st.expander('材料适用范围 · ' + doc['name']):
                st.caption('默认沿用上面的研究公司和产品。同行资料或全公司资料，请按原件调整，避免错误绑定参数。')
                source_company = st.text_input('材料公司 · ' + doc['name'], key='source_company_' + suffix)
                source_product = st.text_input('材料产品 · ' + doc['name'], key='source_product_' + suffix)
            confirmed = st.checkbox('已核对日期和适用范围 · ' + doc['name'], key='source_confirm_' + suffix)
            metadata.append({'name':doc['name'],'published_at':published,'source_kind':kind,'company':source_company,
                             'product':source_product,'confirmed':confirmed})
    scope = document_scope(documents, metadata, cutoff)
    st.caption(f"可用于本次审查的材料：{len(scope['eligible'])}／{len(documents)} 份。研究计划确认和文件来源确认是两个步骤。")
    if scope['excluded']:
        st.warning('以下文件尚未通过日期／来源登记，不能进入按截止日审查；这不表示文件损坏。请在上方“文件来源登记”中处理：\n\n' + '\n\n'.join(
            f"- {item['name']}：{item['reason']}。" for item in scope['excluded']))
    with st.expander('信息范围与文字覆盖'):
        st.json(scope)
        st.caption('元数据由操作人声明；日期确认不等于原件出处已认证。扫描版无文字的PDF需要另行提供可核对文本。')
    context = {'question': question, 'company': company, 'product': product, 'cutoff': cutoff.isoformat()}
    secret = st.session_state.get('api_secret', '')
    if secret and secret in json.dumps({'context': context, 'scope': scope, 'documents': documents}, ensure_ascii=False):
        st.error('材料或研究输入包含本次API密钥，请移除后再运行。')
        return
    binding = digest(json.dumps({'context': context, 'scope': scope}, sort_keys=True, ensure_ascii=False).encode())
    if st.session_state.get('research_context_binding') != binding:
        for key in ('research_run', 'research_plan', 'research_review', 'research_confirmed_parameters', 'conditions_result', 'conditions_binding', 'run'):
            st.session_state.pop(key, None)
        st.session_state['research_context_binding'] = binding
    def get_run():
        if 'research_run' not in st.session_state:
            st.session_state['research_run'] = Run(root / 'work' / 'harness_runs', 'industry_research', uploads)
            st.session_state['research_run'].write('research_input.json', {'context': context, 'scope': scope})
        st.session_state['run'] = st.session_state['research_run']
        return st.session_state['research_run']

    st.subheader('检查清单')
    st.caption('先看下面的条件是否覆盖你的问题。可以直接用本地清单，也可以让模型起草；确认后再检查材料。')
    st.caption('点击模型按钮会把研究问题、元数据或检索片段发给所配置的服务商。可以自行编辑计划；模型意见均待核。')
    if st.button('拟定研究计划', disabled=not company.strip() or not question.strip()):
        try:
            st.session_state['research_plan'] = plan_thesis(get_run(), make_client(), question, company, product, scope)
        except Exception as exc:
            st.error(str(exc))
            st.info('模型拟定计划没有成功。仍可使用下方本地模板，编辑并确认后继续；模板不代表模型已经完成研究。')
    if st.button('使用本地研究模板（不调用模型）'):
        st.session_state['research_plan'] = local_plan(question, product)
    initial = st.session_state.get('research_plan', local_plan(question, product))
    if initial.get('notes'):
        st.caption(initial['notes'])
    for condition in initial['conditions']:
        st.write('· ' + condition['label'])
    plan_rows = [{'id': c['id'], 'type': c['type'], 'label': c['label'], 'query_terms': '，'.join(c['query_terms'])} for c in initial['conditions']]
    with st.expander('编辑检查清单与检索词'):
        edited = st.data_editor(pd.DataFrame(plan_rows), num_rows='dynamic', hide_index=True,
                                key='thesis_conditions_' + binding + digest(json.dumps(initial, ensure_ascii=False).encode()),
                                column_config={'type': st.column_config.SelectboxColumn('条件类型', options=['technical', 'capacity', 'demand', 'price', 'cost', 'financial']),
                                               'label': st.column_config.TextColumn('待检查条件'), 'query_terms': st.column_config.TextColumn('检索词（中文逗号分隔）')})
    plan = {'conditions': [{**r, 'query_terms': [s.strip() for s in str(r['query_terms']).replace(',', '，').split('，') if s.strip()]}
                           for r in edited.fillna('').to_dict('records')], 'notes': initial.get('notes', '')}
    review_binding = digest(json.dumps(plan, sort_keys=True, ensure_ascii=False).encode())
    if st.session_state.get('research_review_binding') != review_binding:
        for key in ('research_review', 'research_confirmed_parameters', 'conditions_result', 'run'):
            st.session_state.pop(key, None)
        st.session_state['research_review_binding'] = review_binding
    plan_confirmed = st.checkbox('我确认这些条件及检索词，并会核对模型返回的支持材料和反证。', key='plan_confirm_' + binding + review_binding)
    blockers = []
    if not question.strip():
        blockers.append('填写上方“研究要求”')
    if not company.strip():
        blockers.append('填写“研究公司”')
    if not scope['eligible']:
        blockers.append('至少一份材料须填写有效披露日期、不晚于信息截止日，并勾选该文件的“已核对日期和适用范围”')
    if not plan_confirmed:
        blockers.append('勾选上方研究计划确认框')
    if blockers:
        st.info('“审查证据／继续”尚未启用，需要：\n\n' + '\n\n'.join(f'- {item}。' for item in blockers))
    if st.button('审查证据／继续', disabled=bool(blockers)):
        try:
            validate_plan(plan)
            get_run().write('operator_confirmed_thesis_plan.json', plan)
            get_run().event('thesis_conditions_operator_confirmed')
            with st.spinner('逐个条件检索和审查，已完成条件会缓存…'):
                st.session_state['research_review'] = review_thesis(get_run(), make_client(), plan, documents, scope, context)
        except Exception as exc:
            st.error(str(exc))
            st.warning('本次尚未全部完成。下方已完成条件可核对和导出，下次点击将继续未完成条件。')
            partial_path = get_run().path / 'outputs' / 'thesis_partial.json'
            if partial_path.exists():
                st.session_state['research_review'] = json.loads(partial_path.read_text(encoding='utf-8'))
    reviewed = st.session_state.get('research_review')
    parameters, evidence = [], {}
    if reviewed:
        if not reviewed.get('complete', False):
            st.warning('这里只展示已完成条件，不能将结果称为完整论点审查。')
        st.subheader('2　核对支持材料、反证与参数候选')
        for assessment in reviewed['assessments']:
            with st.expander(assessment['condition']['label'] + ' · ' + assessment['status'], expanded=True):
                for row in assessment['evidence']:
                    evidence[row['id']] = row
                    st.markdown('**' + {'supports': '支持候选', 'contradicts': '反证候选', 'context': '背景'}[row['stance']] + '** · ' + row['fact_type'])
                    st.text(row['quote'])
                    st.caption(row['id'] + ' · ' + row['source_file'] + ' · ' + row['source_locator'] + ' · ' + row['metadata']['published_at'])
                    st.write(row['explanation'])
                    if row['rule_flags']:
                        st.json(row['rule_flags'])
                st.caption('待核的模型判断：' + assessment['model_conclusion_draft'])
                for text in assessment['missing_in_supplied_material']:
                    st.write('待查：' + text)
                with st.expander('检索覆盖与拒绝的摘录'):
                    st.json({'coverage': assessment['retrieval_coverage'], 'rejected': assessment['rejected']})
                parameters.extend(assessment['parameter_candidates'])
        if parameters:
            st.caption('勾选表示你核对了引用、数值、单位、语义和产品范围。摘录存在不等于预测已实现。')
            approval = []
            # A repeated model reference remains one candidate, with one explicit confirmation control.
            parameters = list({p['id']: p for p in parameters}.values())
            for parameter in parameters:
                suffix = binding + review_binding + parameter['id']
                st.text(parameter['key'] + ' · ' + parameter['value_text'] + ' ' + parameter['unit'] + ' · ' + parameter['quote'])
                fact_type = st.selectbox('原文性质 · ' + parameter['id'], ['historical', 'forecast', 'commitment', 'opinion'],
                                        index=['historical', 'forecast', 'commitment', 'opinion'].index(parameter['fact_type']), key='fact_' + suffix)
                approved = st.checkbox('确认参数 · ' + parameter['id'], key='approve_' + suffix)
                approval.append({'id': parameter['id'], 'fact_type': fact_type, '确认': approved})
            approval_hash = digest(json.dumps(approval, sort_keys=True, ensure_ascii=False).encode())
            if st.session_state.get('research_saved_approval_hash') != approval_hash:
                st.session_state.pop('research_confirmed_parameters', None)
                st.session_state.pop('conditions_result', None)
            if st.button('保存已核对的参数候选'):
                try:
                    selected = []
                    for row in approval:
                        if row['确认']:
                            candidate = deepcopy(next(p for p in parameters if p['id'] == row['id']))
                            candidate['fact_type'] = row['fact_type']
                            if row['fact_type'] == 'opinion':
                                raise ValueError('意见不能直接确认为数值参数。')
                            selected.append(confirm_parameter(candidate, evidence[candidate['evidence_id']], company, product, True))
                    st.session_state['research_confirmed_parameters'] = selected
                    st.session_state['research_saved_approval_hash'] = approval_hash
                    get_run().write('operator_confirmed_parameter_candidates.json', selected)
                    get_run().event('selected_parameters_operator_confirmed', parameter_ids=[p['id'] for p in selected])
                    st.session_state.pop('conditions_result', None)
                    st.success('已保存确认候选；在下方选择适用字段和年度后才进入模型。')
                except Exception as exc:
                    st.error(str(exc))

    if reviewed:
        counts = [row.get('evidence', []) for row in reviewed['assessments']]
        support = sum(e.get('stance') == 'supports' for rows in counts for e in rows)
        counter = sum(e.get('stance') == 'contradicts' for rows in counts for e in rows)
        st.caption(f'本次整理：支持候选{support}条，反证候选{counter}条。它们需要原件核对，不代表论点成立概率。')
    if not st.toggle('继续做盈利与估值情景（可选）', key='enable_conditions'):
        st.caption('只检查观点时，在下方下载研究记录即可。需要计算时再开启；未来参数仍需由你确认。')
        if reviewed and 'run' not in st.session_state:
            get_run()
        return
    st.subheader('盈利与估值情景')
    st.caption('下方默认数值均为合成假设，须替换为你的模型。完整预测年度从截止日下一年开始；此模型不从技术指标自动推导财务增长。')
    default_rows = [{'year': cutoff.year + i, 'units': 60000.0 * 1.1 ** (i - 1), 'asp_yuan': 2000.0,
                     'unit_cost_yuan': 1200.0, 'existing_capacity': 100000.0, 'incremental_capacity': 0.0,
                     'commissioning_date': '', 'confirmed_orders': ''} for i in range(1, 6)]
    rows = st.data_editor(pd.DataFrame(default_rows), disabled=['year'], hide_index=True, key='forecast_' + binding,
                         column_config={'units': st.column_config.NumberColumn('销量（台）'), 'asp_yuan': st.column_config.NumberColumn('售价（元/台）'),
                                        'unit_cost_yuan': st.column_config.NumberColumn('单位成本（元/台）'), 'existing_capacity': st.column_config.NumberColumn('原有年产能（台/年）'),
                                        'incremental_capacity': st.column_config.NumberColumn('新增年产能（台/年）'),
                                        'commissioning_date': st.column_config.TextColumn('新增产能投产日 YYYY-MM-DD'),
                                        'confirmed_orders': st.column_config.TextColumn('该年已确认订单（台，可空）')}).fillna('').to_dict('records')
    volume_multiplier = st.number_input('销量情景倍数（作用于上表）', .001, 50., 1.)
    for row in rows:
        row['units'] *= volume_multiplier
    bindings = []
    confirmed = st.session_state.get('research_confirmed_parameters', [])
    if confirmed:
        with st.expander('把已确认候选绑定到模型（每项明确选择）', expanded=True):
            choices = {'annual_capacity': ['existing_capacity', 'incremental_capacity'], 'commissioning_date': ['commissioning_date'],
                       'asp_yuan': ['asp_yuan'], 'unit_cost_yuan': ['unit_cost_yuan'], 'orders_units': ['confirmed_orders']}
            for item in confirmed:
                st.caption(f"{item['key']} · {item['normalized_value']} · {item['source_locator']} · {item['fact_type']}")
                field = st.selectbox('适用字段', ['不采用'] + choices[item['key']], key='bind_field_' + binding + item['id'],
                    format_func=lambda k: {'existing_capacity': '原有年产能', 'incremental_capacity': '新增年产能',
                                          'commissioning_date': '新增产能投产日', 'asp_yuan': '售价', 'unit_cost_yuan': '单位成本',
                                          'confirmed_orders': '该年已确认订单'}.get(k, k))
                years = st.multiselect('适用预测年', [r['year'] for r in rows], key='bind_years_' + binding + item['id'])
                if field != '不采用' and years:
                    for row in rows:
                        if row['year'] in years:
                            row[field] = item['normalized_value']
                    bindings.append({**item, 'application': {'field': field, 'years': years}})
            st.caption('来源支持的是原始陈述，向未来沿用价格／产能仍是你的情景假设；订单只允许绑定明确匹配的年度。')
    a, b, c = st.columns(3)
    opex = a.number_input('费用率（%）', 0., 100., 15.) / 100
    dep = b.number_input('折旧／收入（%）', 0., 100., 3.) / 100
    tax = c.number_input('正经营利润税率（%）', 0., 100., 25.) / 100
    a, b, c = st.columns(3)
    capex = a.number_input('资本支出／收入（%）', 0., 100., 5.) / 100
    nwc = b.number_input('营运资本／收入（%）', 0., 100., 20.) / 100
    opening = c.number_input('期初营运资本（元）', 0., value=20000000.)
    stub = st.number_input('截止日至本年末FCFF（元；零也是需确认的假设）', value=0.)
    a, b = st.columns(2)
    discount = a.number_input('条件模型折现率（%）', .1, 99., 10.) / 100
    growth = b.number_input('条件模型永续增长（%）', -20., 50., 2.) / 100
    whole_company = st.checkbox('这个业务模型覆盖全公司所有经营业务（否则仅为指定业务价值）。')
    model = {'company': company, 'product': product, 'cutoff': cutoff.isoformat(), 'rows': rows,
             'opex_ratio': opex, 'depreciation_ratio': dep, 'tax_rate': tax, 'capex_ratio': capex, 'nwc_ratio': nwc,
             'opening_nwc': opening, 'stub_fcff': stub, 'discount_rate': discount, 'terminal_growth': growth, 'whole_company': whole_company, 'bindings': bindings}
    with st.expander('目标、反推与预先声明的情景范围'):
        target_kind = st.selectbox('目标口径', ['不反推', '企业价值', '第五年经营NOPAT', '公司市值'])
        target = st.number_input('目标金额（元）', 0., value=300000000.)
        conversion = None
        if target_kind == '公司市值':
            st.caption('比较需要同一日口径；这些调整数必须明确输入，可确认零值，不自动补零。')
            debt = st.text_input('同日净债务（元）')
            minority = st.text_input('同日少数股东价值（元）')
            nonop = st.text_input('同日非经营资产（元）')
            dates = [st.text_input(label) for label in ['市值日期', '净债务日期', '少数股东价值日期', '非经营资产日期']]
            conversion = (debt, minority, nonop, dates)
        lever = st.selectbox('反推变量', ['volume_scale', 'price_scale', 'cost_scale'], format_func=lambda k: {'volume_scale': '销量倍数', 'price_scale': '售价倍数', 'cost_scale': '单位成本倍数'}[k])
        lo, hi = st.columns(2)
        lower = lo.number_input('反推倍数下界', .001, 50., .5)
        upper = hi.number_input('反推倍数上界', .001, 50., 2.)
        ranges = st.data_editor(pd.DataFrame([{'key': 'price_scale', 'low': .9, 'high': 1.0},
                                             {'key': 'cost_scale', 'low': .9, 'high': 1.1},
                                             {'key': 'commissioning_delay_days', 'low': 0., 'high': 180.}]),
                                disabled=['key'], hide_index=True, key='sensitivity_' + binding).to_dict('records')
    assumed = st.checkbox('我确认这些未来参数是情景假设，已检查采用的证据、单位、产能与订单期间。')
    input_key = digest(json.dumps([model, target_kind, target, lever, lower, upper, conversion, ranges], sort_keys=True, ensure_ascii=False).encode())
    if st.session_state.get('conditions_binding') != input_key:
        st.session_state.pop('conditions_result', None)
        st.session_state['conditions_binding'] = input_key
        st.session_state.pop('run', None)
    if st.button('计算兑现条件', disabled=not assumed or not company.strip() or not product.strip()):
        try:
            result = forward(model)
            reverse_result = None
            if target_kind != '不反推':
                target_ev = target
                if conversion:
                    debt, minority, nonop, dates = conversion
                    result['target_conversion'] = market_cap_to_ev(model, target, debt, minority, nonop, dates)
                    target_ev = result['target_conversion']['target_ev']
                reverse_result = reverse(model, target_ev, 'nopat' if target_kind == '第五年经营NOPAT' else 'enterprise_value', lever, lower, upper)
            sensitivities = sensitivity(model, ranges)
            run = Run(root / 'work' / 'harness_runs', 'realization_conditions', uploads)
            run.write('research_context.json', context)
            if reviewed:
                run.write('related_thesis_review.json', reviewed)
            save_conditions(run, result, reverse_result, sensitivities)
            st.session_state['run'] = run
            st.session_state['conditions_result'] = (result, reverse_result, sensitivities)
        except Exception as exc:
            st.error(str(exc))
    if 'conditions_result' in st.session_state:
        result, reversed_result, sensitivities = st.session_state['conditions_result']
        if result['enterprise_value'] is not None:
            st.metric('条件企业价值（元）', f"{result['enterprise_value']:,.0f}")
        for text in result['conflicts']:
            st.error(text)
        for text in result['gaps']:
            st.caption('待补：' + text)
        st.dataframe(pd.DataFrame(result['years']), hide_index=True)
        if reversed_result:
            st.json(reversed_result)
        st.dataframe(pd.DataFrame(sensitivities), hide_index=True)
        st.caption('敏感性按你声明的范围比较，不是事实概率或预测准确率。缺口与假设保留在下载成果中。')
    elif reviewed and 'run' not in st.session_state:
        get_run()
