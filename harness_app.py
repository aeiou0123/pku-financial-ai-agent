"""Research desk: own API, uploaded files, two isolated deterministic workflows."""
from __future__ import annotations

import csv
import io
import json
import os
import importlib
import hashlib
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

# Streamlit can rerun this entrypoint while retaining imported modules. Refresh only
# changed local tool files, in dependency order; no process restart or credential reset.
for module_name in ('documents', 'store', 'api', 'exports', 'financial', 'diagnostics', 'research',
                    'conditions', 'quant', 'strategy_diagnostics', 'research_ui', 'engine'):
    module = importlib.import_module('src.harness.' + module_name)
    source_hash = hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()
    if getattr(module, '_c2v_loaded_source_hash', None) != source_hash:
        importlib.reload(module)
        module._c2v_loaded_source_hash = source_hash

from src.financial_intake import FIELDS
from src.harness.api import ModelClient, api_endpoints, redact
from src.harness.documents import parse, table, digest, safe_name
from src.harness.engine import propose_quant, draft_commentary
from src.harness.financial import extract, check_financial, dcf, save_dcf
from src.harness.diagnostics import comparison_groups, earnings_bridge, save_diagnostics
from src.harness.quant import prepare, backtest, save
from src.harness.research_ui import render as render_research
from src.harness.strategy_diagnostics import diagnose
from src.harness.store import Run
from src.review_ui import STYLE, page_heading, section_heading

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title="Claim2Value · 研究工作台", layout="wide")
st.markdown(STYLE, unsafe_allow_html=True)


def client(*, require_model: bool = True) -> ModelClient:
    if require_model and not st.session_state.get('api_model', '').strip():
        raise ValueError('请先获取模型列表并选择，或手动填写模型名称后按Enter。')
    if not st.session_state.get('api_secret', '').strip():
        raise ValueError('API Key尚未保存，请填写后按Enter或离开输入框。')
    return ModelClient(st.session_state["api_base"], st.session_state.get("api_model", ''),
                       st.session_state["api_secret"], max_calls=int(st.session_state.get("api_budget", 12)),
                       protocol=st.session_state.get("api_protocol", "openai"),
                       max_output_tokens=int(st.session_state.get("api_output_limit", 8192)))


def write_sources(run: Run, uploads: list[tuple[str, bytes]]):
    run.write("source_index.json", [{"name": name, "source_file": safe_name(name),
                                      "sha256": digest(data), "bytes": len(data)} for name, data in uploads])


def current_run(uploads, workflow) -> Run:
    if "run" not in st.session_state:
        st.session_state["run"] = Run(ROOT / "work" / "harness_runs", workflow, uploads)
        write_sources(st.session_state["run"], uploads)
    return st.session_state["run"]


def clear_key():
    st.session_state["api_secret"] = ""
    st.session_state['api_secret_widget'] = ''
    invalidate_catalog()


def invalidate_connection():
    st.session_state.pop("connection_result", None)


def invalidate_catalog():
    invalidate_connection()
    for key in ('model_catalog', 'model_catalog_error', 'api_model_choice'):
        st.session_state.pop(key, None)


def choose_model():
    selected = st.session_state.get('api_model_choice')
    if selected:
        st.session_state['api_model'] = selected
        invalidate_connection()


def manual_model_changed():
    invalidate_connection()
    st.session_state.pop('api_model_choice', None)


def save_session_key():
    # Keep the in-memory credential separate from the UI widget's lifecycle.
    st.session_state['api_secret'] = st.session_state.get('api_secret_widget', '')
    invalidate_catalog()


def apply_connection_preset():
    preset = st.session_state["api_preset"]
    if preset == "Kimi Code 订阅":
        st.session_state.update(api_base="https://api.kimi.com/coding/v1", api_model="kimi-for-coding", api_protocol="openai")
    elif preset == "OpenAI":
        st.session_state.update(api_base="https://api.openai.com/v1", api_model="", api_protocol="openai")
    invalidate_catalog()


with st.sidebar:
    st.markdown('<div class="c2v-brand"><div class="c2v-brand-name">Claim2Value</div><div class="c2v-brand-sub">研究工作台</div></div>', unsafe_allow_html=True)
    workflow = st.radio("研究方向", ["财务／估值研究", "量化处理与回测"])
    with st.expander("模型连接", expanded=False):
        st.selectbox("配置预设", ["自定义", "Kimi Code 订阅", "OpenAI"], key="api_preset", on_change=apply_connection_preset)
        st.selectbox("接口协议", ["openai", "anthropic"], key="api_protocol", on_change=invalidate_catalog,
                     format_func=lambda value: "OpenAI · Chat Completions" if value == "openai" else "Anthropic · Messages")
        st.text_input("API Base URL", value=os.environ.get("C2V_API_BASE", "https://api.openai.com/v1"), key="api_base", on_change=invalidate_catalog,
                      help='可填服务根地址、以 /v1 结尾的基础地址，或完整接口地址；末尾 / 可保留。')
        with st.expander('地址填写示例'):
            st.caption('OpenAI 协议：以下写法都会使用同一个 Chat Completions 地址。')
            st.code('https://api.openai.com\nhttps://api.openai.com/\nhttps://api.openai.com/v1\nhttps://api.openai.com/v1/\nhttps://api.openai.com/v1/chat/completions\nhttps://api.openai.com/v1/completions', language=None)
            st.caption('末尾 /completions 仅作为地址输入兼容，实际使用 /chat/completions。服务须支持所选协议。')
            st.caption('Kimi Code 订阅：')
            st.code('https://api.kimi.com/coding/v1\nhttps://api.kimi.com/coding/v1/chat/completions', language=None)
            st.caption('Anthropic 协议：')
            st.code('https://api.anthropic.com\nhttps://api.anthropic.com/v1\nhttps://api.anthropic.com/v1/messages', language=None)
            st.caption('其他服务请替换为服务商给出的域名和路径；自定义路径会保留。')
        # Explicit assignment also preserves credentials when migrating the old widget key.
        st.session_state['api_secret'] = st.session_state.get('api_secret', os.environ.get('C2V_API_KEY', ''))
        st.text_input("API Key", value=st.session_state['api_secret'], type="password", key="api_secret_widget", on_change=save_session_key)
        try:
            endpoints = api_endpoints(st.session_state['api_base'], st.session_state['api_protocol'])
            st.caption('实际请求地址：')
            preview = '生成：' + endpoints['completion'] + '\n模型列表：' + endpoints['models']
            st.code(redact(preview, st.session_state['api_secret']) if st.session_state['api_secret'] else preview, language=None)
        except ValueError as exc:
            st.warning(str(exc))
        if st.button('获取模型列表'):
            invalidate_catalog()
            try:
                with st.spinner('正在获取模型列表…'):
                    st.session_state['model_catalog'] = client(require_model=False).list_models()
            except (ValueError, RuntimeError) as exc:
                st.session_state['model_catalog_error'] = str(exc)
        catalog = st.session_state.get('model_catalog')
        if catalog:
            models = catalog['models']
            st.success(f"已获取 {len(models)} 个模型名称。请选择后测试连接。")
            if catalog['partial']:
                st.caption('服务返回的列表尚有后续页或超过显示上限；未列出的模型可手动填写。')
            current = st.session_state.get('api_model', '')
            options = [None] + models
            st.selectbox('从列表选择模型', options, index=options.index(current) if current in models else 0,
                         format_func=lambda value: '请选择模型' if value is None else value,
                         key='api_model_choice', on_change=choose_model)
            st.caption('列表可能包含音频、嵌入等模型；请选择支持当前文本协议的模型，再测试连接。')
        if st.session_state.get('model_catalog_error'):
            st.warning('获取模型列表失败，仍可手动填写模型名称。 ' + st.session_state['model_catalog_error'])
        st.text_input("模型名称", value=os.environ.get("C2V_MODEL", ""), key="api_model", placeholder="先获取并选择，或手动填写模型 ID", on_change=manual_model_changed)
        st.caption('获取列表仅在点击时请求一次，不发送研究材料、不调用文本生成。改地址、协议或密钥后需重新获取。')
        st.number_input("每次操作最多请求数", min_value=1, max_value=40, value=12, key="api_budget")
        st.number_input("每次响应输出 token 上限", min_value=256, max_value=32768, value=8192, step=256, key="api_output_limit")
        st.caption("密钥仅在本次会话中使用，不写入文件。测试只发一条小请求，不包含上传材料，会使用少量额度。")
        if st.button("测试连接", type="primary"):
            invalidate_connection()
            try:
                with st.spinner("正在测试接口…"):
                    result = client().test_connection()
                st.session_state["connection_result"] = {"ok": True, "details": result}
            except (ValueError, RuntimeError) as exc:
                st.session_state["connection_result"] = {"ok": False, "message": str(exc)}
        connection = st.session_state.get("connection_result")
        if connection:
            if connection["ok"]:
                details = connection["details"]
                if details["text_response_received"]:
                    st.success(f"连接成功 · HTTP 200 · {details['elapsed_seconds']} 秒")
                else:
                    st.warning("接口已响应 HTTP 200，但没有生成文本。请检查思考设置或输出上限。")
                st.json(details)
            else:
                st.error(connection["message"])
        if st.session_state["api_preset"] == "Kimi Code 订阅":
            st.caption("使用 Kimi Code 控制台的密钥，不能与 Moonshot 开放平台密钥混用。")
            st.markdown("[Kimi Code 官方配置与使用范围](https://www.kimi.com/code/docs/)")
    st.caption("模型只在点击相应按钮后调用。计算由本地工具执行；上传原件留在本机。")
    st.button("清除本次会话的密钥", on_click=clear_key)

page_heading(st, workflow, "上传自己的材料，核对输入，执行任务，下载结果。", code="RESEARCH")
research_mode = st.radio('财务研究任务', ['论点审查与兑现条件', '财务整理与盈利解释'], horizontal=True) if workflow.startswith('财务') else ''
uploaded = st.file_uploader("研究文件", type=["pdf", "docx", "txt", "md", "csv", "xlsx"], accept_multiple_files=True,
                            help="单个 20 MB；合计 60 MB；每次最多 10 个文件。", key='research_uploads')
uploads = [(file.name, file.getvalue()) for file in uploaded]
task = st.text_area("研究要求", placeholder="例如：扩产能否支持未来两年的收入增长？请检查投产、订单、售价和成本。" if research_mode == '论点审查与兑现条件' else "例如：核对 2024 年合并报表的收入、成本和归母净利润，列出来源和缺口。" if workflow.startswith("财务") else
                    "例如：用复权收盘价计算 20 日动量，每日选 10 只等权持有，单边费用 10 bps。", height=90)
binding = digest(json.dumps({"files": [(n, digest(b)) for n, b in uploads], "workflow": workflow, "mode": research_mode, "task": task}, ensure_ascii=False).encode())
if st.session_state.get("binding") != binding:
    for key in ("run", "extraction_run", "candidates", "parsed", "result", "financial_result", "proposal", "draft", "extraction_done", "dcf_result", "diagnostic_result", "diagnostic_binding", 'research_run', 'research_plan', 'research_review', 'research_context_binding', 'research_review_binding', 'research_confirmed_parameters', 'conditions_result', 'conditions_binding', 'strategy_diagnostic_result', 'strategy_diagnostic_binding'):
        st.session_state.pop(key, None)
    st.session_state["binding"] = binding


def show_outputs():
    run = st.session_state.get("run")
    if run is None:
        return
    section_heading(st, "运行记录与成果", run.path.name)
    st.caption(str(run.path))
    st.caption("下载对应这次已经执行的快照；编辑输入或参数后，请再次运行以生成新成果。")
    st.download_button("下载本次成果 ZIP", run.bundle(), file_name="Claim2Value_" + run.path.name + ".zip", mime="application/zip",
                       key="download_" + run.path.name)
    st.caption("成果状态：" + run.metadata["status"])
    st.caption("ZIP 包含输出、输入指纹和运行步骤；不包含上传原件或密钥。财务输出可能包含原文摘录，请自行确认分享范围。")
    with st.expander("查看处理步骤"):
        events = [json.loads(line) for line in (run.path / "events.jsonl").read_text(encoding="utf-8").splitlines()]
        st.json(events)


if not uploads:
    st.info("先上传研究文件。下方示例都是合成数据，用于熟悉操作。")
    examples = ROOT / "docs" / "harness" / "examples"
    for name in (["synthetic_industry.txt", "synthetic_industry_counterevidence.txt"] if research_mode == '论点审查与兑现条件' else ["synthetic_financial.txt", "synthetic_financial.csv"] if workflow.startswith("财务") else ["synthetic_prices.csv"]):
        path = examples / name
        if path.exists():
            st.download_button("下载示例 · " + name, path.read_bytes(), file_name=name)
    st.stop()

if workflow.startswith("财务"):
    if research_mode == '论点审查与兑现条件':
        try:
            render_research(ROOT, uploads, task, client)
        except Exception as exc:
            st.error(str(exc))
        show_outputs()
        st.stop()
    mode = st.radio("输入方式", ["从文件提取候选", "导入已整理财务长表"], horizontal=True)
    section_heading(st, "01　整理证据", "模型候选须人工核对")
    if mode == "从文件提取候选":
        if st.button("读取文件", type="primary"):
            try:
                run = current_run(uploads, "financial")
                with st.spinner("读取可提取的文字…"):
                    parsed = [parse(data, name) for name, data in uploads]
                st.session_state["parsed"] = parsed
                run.write("source_index.json", [{k: v for k, v in doc.items() if k != "parts"} for doc in parsed])
                run.event("documents_parsed", files=len(parsed))
            except Exception as exc:
                st.error(str(exc))
        parsed = st.session_state.get("parsed")
        if parsed:
            st.dataframe(pd.DataFrame([{k: v for k, v in doc.items() if k not in {"parts", "warnings"}} for doc in parsed]), hide_index=True)
            for doc in parsed:
                for warning in doc["warnings"]:
                    st.warning(doc["name"] + "：" + warning)
            with st.expander("查看文字和定位"):
                for doc in parsed:
                    st.write(doc["name"])
                    # A bounded UI preview; extraction itself uses all parsed pieces.
                    st.json(doc["parts"][:8])
                st.caption("界面预览各文件前 8 个片段；模型按解析覆盖范围分批读取。")
            st.caption("点击下一按钮，会把已解析的文字和研究要求发给所配置的模型服务商。已完成批次会缓存，失败后可继续。")
            if st.button("提取／继续财务候选", disabled=not task.strip()):
                try:
                    st.session_state.pop("financial_result", None)
                    st.session_state["extraction_done"] = False
                    run = st.session_state.get("extraction_run") or current_run(uploads, "financial")
                    st.session_state["extraction_run"] = run
                    st.session_state["run"] = run
                    with st.spinner("分批提取并检查原文定位…"):
                        st.session_state["candidates"] = extract(run, parsed, task, client())
                    st.session_state["extraction_done"] = True
                    st.success("提取结束。原文匹配只能证明摘录存在，字段、日期与单位仍需核对。")
                except Exception as exc:
                    st.error(str(exc))
                    if "run" in st.session_state:
                        path = st.session_state["run"].path / "outputs" / "candidates.json"
                        if path.exists():
                            st.session_state["candidates"] = json.loads(path.read_text(encoding="utf-8"))
                    st.warning("本次提取没有全部完成；已完成候选可查看，继续提取后再完成研究。")
    else:
        csvs = [name for name, _ in uploads if name.lower().endswith(".csv")]
        if csvs:
            chosen = st.selectbox("16 列财务长表文件", csvs)
            if st.button("读取财务长表", type="primary"):
                try:
                    raw = next(data for name, data in uploads if name == chosen)
                    frame = table(raw, chosen)
                    if list(frame.columns) != FIELDS:
                        raise ValueError("列名和顺序须与示例中的 16 列一致。")
                    rows = frame.to_dict("records")
                    names = {name: safe_name(name) for name, _ in uploads}
                    for row in rows:
                        row["source_file"] = names.get(row["source_file"], row["source_file"])
                    st.session_state["candidates"] = rows
                    st.session_state["extraction_done"] = True
                    current_run(uploads, "financial").write("imported_records.json", rows)
                    st.session_state.pop("financial_result", None)
                except Exception as exc:
                    st.error(str(exc))
        else:
            st.info("请同时上传财务长表 CSV 和被引用的原件。示例可在空白页面下载。")
    candidates = st.session_state.get("candidates")
    if candidates:
        section_heading(st, "02　核对并计算", "缺少披露日期或口径会阻止计算")
        with st.expander("候选摘录与状态", expanded=True):
            st.dataframe(pd.DataFrame(candidates), hide_index=True, width="stretch")
        with st.form("financial_confirmation"):
            editor = st.data_editor(pd.DataFrame([{k: row.get(k, "") for k in FIELDS} for row in candidates]),
                                    num_rows="dynamic", width="stretch", key="financial_editor_" + binding,
                                    column_config={key: st.column_config.TextColumn(key) for key in FIELDS})
            cutoff = st.date_input("信息截止日", value=date.today())
            confirm = st.checkbox("我已对照原件核对字段、披露日期、单位、报表口径和更正版本。")
            submitted = st.form_submit_button("校验并生成财务成果", disabled=not st.session_state.get("extraction_done", False))
        if submitted:
            st.session_state.pop("financial_result", None)
            st.session_state.pop("diagnostic_result", None)
            if not confirm:
                st.error("请先完成原件核对，并勾选确认。")
            else:
                try:
                    old_run = st.session_state.get("run")
                    run = Run(ROOT / "work" / "harness_runs", "financial", uploads)
                    st.session_state["run"] = run
                    write_sources(run, uploads)
                    run.write("reviewed_candidates.json", candidates)
                    if old_run:
                        run.write("candidate_history.json", {"source_run_id": old_run.path.name,
                                  "events": [json.loads(line) for line in (old_run.path / "events.jsonl").read_text(encoding="utf-8").splitlines()]})
                    if st.session_state.get("parsed"):
                        run.write("source_index.json", [{k: v for k, v in doc.items() if k != "parts"} for doc in st.session_state["parsed"]])
                    run.event("human_fields_confirmed", note="operator_attestation_not_independent_review")
                    normalized, quality = check_financial(run, editor.fillna("").astype(str).to_dict("records"), cutoff)
                    st.session_state["financial_result"] = (normalized, quality)
                except Exception as exc:
                    st.error(str(exc))
        if "financial_result" in st.session_state:
            normalized, quality = st.session_state["financial_result"]
            if quality["errors"]:
                st.error("校验未通过。请修正后再次生成。")
                st.json(quality["errors"])
            else:
                st.success(f"已生成 {len(normalized)} 条标准化记录。来源真实性仍以原件核对为准。")
                st.dataframe(pd.DataFrame(normalized), hide_index=True)
                st.json(quality["checks"])
                section_heading(st, "解释盈利变化", "收入、毛利率与其余项目分别贡献了多少")
                groups = [g for g in comparison_groups(normalized) if len(g["periods"]) >= 2]
                if not groups:
                    st.info("需要同公司、同披露日、同报表口径和同修订版本的两期年度数据。单期或中期数据不能生成年度变化解释。")
                else:
                    group_index = st.selectbox("财务比较口径", range(len(groups)), format_func=lambda i:
                        " · ".join(str(groups[i]["identity"][key]) for key in ("stock_code", "company", "statement_scope", "published_at", "revision_flag", "source_database")))
                    group = groups[group_index]
                    left, right = st.columns(2)
                    earlier = left.selectbox("比较前期", group["periods"], index=len(group["periods"]) - 2)
                    later = right.selectbox("比较本期", group["periods"], index=len(group["periods"]) - 1)
                    diagnostic_binding = digest(json.dumps({"records": group["records"], "earlier": earlier, "later": later}, sort_keys=True).encode())
                    if st.session_state.get("diagnostic_binding") != diagnostic_binding:
                        st.session_state.pop("diagnostic_result", None)
                        st.session_state["diagnostic_binding"] = diagnostic_binding
                    st.caption("解释已确认的报表变化，并列出待查问题。会计贡献不代表技术进步的因果贡献；合并范围等可比性仍须查看附注。")
                    if st.button("生成盈利变化研究底稿"):
                        try:
                            diagnosis = earnings_bridge(group["records"], earlier, later)
                            previous_run = st.session_state.get("run")
                            run = Run(ROOT / "work" / "harness_runs", "earnings_diagnostics", uploads)
                            write_sources(run, uploads)
                            run.write("confirmed_financial_input.json", group["records"])
                            if previous_run:
                                run.write("related_run.json", {"id": previous_run.path.name, "relationship": "confirmed_financial_data"})
                            save_diagnostics(run, diagnosis)
                            st.session_state["run"] = run
                            st.session_state["diagnostic_result"] = diagnosis
                        except Exception as exc:
                            st.session_state.pop("diagnostic_result", None)
                            st.error(str(exc))
                    if "diagnostic_result" in st.session_state:
                        diagnosis = st.session_state["diagnostic_result"]
                        st.metric(diagnosis["bridge_target"] + "变化（元）", f"{float(diagnosis['target_change_cny']):,.2f}")
                        st.dataframe(pd.DataFrame([{k: v for k, v in row.items() if k != "sources"} for row in diagnosis["indicators"]]), hide_index=True)
                        st.dataframe(pd.DataFrame([{k: v for k, v in row.items() if k != "sources"} for row in diagnosis["bridge"]]), hide_index=True)
                        for finding in diagnosis["findings"]:
                            st.write(finding)
                        for warning in diagnosis["warnings"]:
                            st.warning(warning)
                        with st.expander("原件定位、未取得字段与分解边界"):
                            st.json(diagnosis)
    elif candidates == []:
        st.info("未得到符合原文定位要求的候选，请查看拒绝记录或调整研究要求。")
    section_heading(st, "03　可选估值", "五年 FCFF 必须由你明确输入")
    with st.form("valuation"):
        forecasts = st.text_input("未来五年企业自由现金流，单位：元，逗号分隔", placeholder="不从历史表自动推断预测")
        left, right = st.columns(2)
        rate = left.number_input("折现率（%）", min_value=0.1, max_value=99.0, value=10.0)
        growth = right.number_input("永续增长率（%）", min_value=-20.0, max_value=50.0, value=2.0)
        debt = st.text_input("净债务（元，可留空）", help="留空只计算企业价值。正数为净债务，负数为净现金。")
        assumed = st.checkbox("这些现金流、折现率和增长率是我确认的假设。")
        valued = st.form_submit_button("计算假设 DCF")
    if valued:
        st.session_state.pop("dcf_result", None)
        try:
            if not assumed:
                raise ValueError("请先确认估值假设。")
            result = dcf([float(v.strip()) for v in forecasts.split(",")], rate / 100, growth / 100,
                         None if not debt.strip() else float(debt))
            previous_run = st.session_state.get("run")
            run = Run(ROOT / "work" / "harness_runs", "valuation", uploads)
            st.session_state["run"] = run
            write_sources(run, uploads)
            if previous_run:
                run.write("related_run.json", {"id": previous_run.path.name, "relationship": "context_only_no_automatic_forecast_link"})
            sensitivity = save_dcf(run, result)
            st.session_state["dcf_result"] = (result, sensitivity)
        except Exception as exc:
            st.error(str(exc))
    if "dcf_result" in st.session_state:
        result, sensitivity = st.session_state["dcf_result"]
        st.metric("假设企业价值（元）", f"{result['enterprise_value']:,.2f}")
        st.caption("估值由输入假设计算，未证明技术声明导致财务变化。")
        st.dataframe(sensitivity, hide_index=True)
else:
    section_heading(st, "01　选择数据与任务", "CSV／XLSX 日频完整面板")
    names = [name for name, _ in uploads if Path(name).suffix.lower() in {".csv", ".xlsx"}]
    if not names:
        st.error("量化流程需要 CSV 或 XLSX 表格。")
        st.stop()
    chosen = st.selectbox("行情／因子表", names)
    raw = next(data for name, data in uploads if name == chosen)
    sheet = 0
    if chosen.lower().endswith(".xlsx"):
        try:
            with pd.ExcelFile(io.BytesIO(raw)) as workbook:
                sheet = st.selectbox("工作表", workbook.sheet_names)
        except Exception:
            st.error("无法读取 XLSX。")
            st.stop()
    try:
        frame = table(raw, chosen, sheet)
    except Exception as exc:
        st.error(str(exc))
        st.stop()
    st.caption(f"{len(frame):,} 行 · {len(frame.columns)} 列；预览前 12 行。")
    st.dataframe(frame.head(12), hide_index=True)
    if st.button("让模型拟定任务", disabled=not task.strip()):
        try:
            run = Run(ROOT / "work" / "harness_runs", "quant_plan", uploads)
            st.session_state["run"] = run
            write_sources(run, uploads)
            with st.spinner("模型根据列名和研究要求拟定参数…"):
                proposal = propose_quant(run, client(), task, list(frame.columns), len(frame))
            st.session_state["proposal"] = proposal
            st.session_state["proposal_table"] = (chosen, str(sheet))
        except Exception as exc:
            st.error(str(exc))
    proposal = st.session_state.get("proposal", {}) if st.session_state.get("proposal_table") == (chosen, str(sheet)) else {}
    if proposal:
        st.json(proposal)
        st.caption("这是待确认计划。下面的列映射和参数决定实际执行。")
    config_key = digest(json.dumps([binding, chosen, str(sheet), proposal], sort_keys=True).encode())
    strategy = st.selectbox("信号来源", ["momentum", "factor"],
                            index=1 if proposal.get("strategy") == "factor" else 0,
                            format_func=lambda value: "价格动量" if value == "momentum" else "上传的已有因子", key="strategy_" + config_key)
    mapping = {}
    fields = ["date", "stock", "close"] + (["factor", "available_at"] if strategy == "factor" else [])
    labels = {"date": "交易日期", "stock": "六位股票代码", "close": "已复权收盘价", "factor": "因子值", "available_at": "因子真实可得时间（含时区）"}
    options = [""] + list(frame.columns)
    for field in fields:
        default = proposal.get("mapping", {}).get(field, field if field in frame else "")
        mapping[field] = st.selectbox(labels[field], options, index=options.index(default) if default in options else 0,
                                     key="map_" + field + "_" + config_key + strategy)
    a, b, c, d = st.columns(4)
    lookback = a.number_input("动量窗口（交易日）", min_value=1, max_value=252, value=int(proposal.get("lookback", 20)), key="lb_" + config_key)
    top_n = b.number_input("持仓数", min_value=1, max_value=1000, value=int(proposal.get("top_n", min(10, len(frame[mapping['stock']].unique())) if mapping.get("stock") else 10)), key="tn_" + config_key)
    fee = c.number_input("单边费率（bps）", min_value=0.0, max_value=1000.0, value=float(proposal.get("fee_bps", 10.0)), key="fee_" + config_key)
    direction = d.selectbox("排序方向", ["high", "low"], index=1 if proposal.get("direction") == "low" else 0,
                            format_func=lambda v: "由高到低" if v == "high" else "由低到高", key="direction_" + config_key)
    adjusted = st.checkbox("我确认价格已经复权，因子可得时间真实；本次按完整面板、下一交易日收盘成交研究。")
    settings = {"mapping": mapping, "strategy": strategy, "lookback": int(lookback), "top_n": int(top_n), "fee_bps": fee, "direction": direction,
                "file": chosen, "sheet": str(sheet)}
    result_binding = digest(json.dumps(settings, sort_keys=True).encode())
    if st.session_state.get("result_binding") != result_binding:
        st.session_state.pop("result", None)
        st.session_state.pop("draft", None)
        st.session_state.pop('strategy_diagnostic_result', None)
        st.session_state.pop('run', None)
    if st.button("校验数据并运行回测", type="primary"):
        st.session_state.pop("result", None)
        try:
            if not adjusted:
                raise ValueError("请先核对价格和信号可得时间，并勾选确认。")
            # Every computation snapshots settings in a fresh run; old outputs cannot masquerade as new settings.
            run = Run(ROOT / "work" / "harness_runs", "quant", uploads)
            st.session_state["run"] = run
            write_sources(run, uploads)
            run.write("task_settings.json", settings)
            if proposal:
                run.write("task_proposal.json", proposal)
            run.event("quant_validating", adjustment="operator_attestation")
            with st.spinner("检查数据、计算信号、成交、费用和净值…"):
                data = prepare(frame, mapping, strategy)
                result = backtest(data, strategy=strategy, lookback=int(lookback), top_n=int(top_n), fee_bps=fee, direction=direction)
                save(run, data, result)
            st.session_state["result"] = result
            st.session_state["result_binding"] = result_binding
        except Exception as exc:
            if "run" in st.session_state:
                st.session_state["run"].event("quant_failed", reason=type(exc).__name__)
            st.error(str(exc))
    result = st.session_state.get("result")
    if result:
        section_heading(st, "02　研究结果", "仅对应上传样本")
        a, b, c = st.columns(3)
        a.metric("样本净收益", f"{result['metrics']['total_return']:.2%}")
        b.metric("最大回撤", f"{result['metrics']['max_drawdown']:.2%}")
        c.metric("计入收益的交易日", result["metrics"]["days"])
        st.line_chart(result["daily"][["nav", "benchmark_nav"]])
        st.dataframe(result["positions"], hide_index=True)
        st.json(result["metrics"])
        section_heading(st, '策略诊断', '共同区间、费用、年度分段与预先声明的参数扰动')
        st.caption('先编辑并确认参数组，再运行。全部尝试都会登记，失败组也保留；不自动选收益最好的一组。')
        default_grid = [{'lookback': int(lookback), 'top_n': int(top_n), 'fee_bps': float(fee), 'direction': direction}]
        if strategy == 'momentum' and lookback < 252:
            default_grid.append({**default_grid[0], 'lookback': min(252, int(lookback) + 5)})
        if fee < 1000:
            default_grid.append({**default_grid[0], 'fee_bps': min(1000., float(fee) + 10)})
        grid = st.data_editor(pd.DataFrame(default_grid), num_rows='dynamic', hide_index=True, key='diagnostic_grid_' + result_binding,
                              column_config={'direction': st.column_config.SelectboxColumn('排序方向', options=['high', 'low'])}).to_dict('records')
        grid_binding = digest(json.dumps([result_binding, grid], sort_keys=True).encode())
        if st.session_state.get('strategy_diagnostic_binding') != grid_binding:
            st.session_state.pop('strategy_diagnostic_result', None)
            st.session_state['strategy_diagnostic_binding'] = grid_binding
            # Keep the completed base run available, but never expose a previous diagnostic as current.
            if st.session_state.get('run') and st.session_state['run'].metadata['workflow'] == 'strategy_diagnostics':
                st.session_state.pop('run', None)
        declared = st.checkbox('我预先声明这些参数；本次是已查看样本的研究，不称未触碰留出集。', key='grid_confirm_' + grid_binding)
        if st.button('运行策略诊断', disabled=not declared):
            try:
                diagnostic_run = Run(ROOT / 'work' / 'harness_runs', 'strategy_diagnostics', uploads)
                st.session_state['run'] = diagnostic_run
                write_sources(diagnostic_run, uploads)
                diagnostic_run.write('task_settings.json', settings)
                report, navs = diagnose(diagnostic_run, prepare(frame, mapping, strategy), strategy, grid,
                                        ROOT / 'work' / 'harness_runs' / 'experiment_registry.jsonl')
                st.session_state['strategy_diagnostic_result'] = (report, navs)
            except Exception as exc:
                st.error(str(exc))
        if 'strategy_diagnostic_result' in st.session_state:
            report, navs = st.session_state['strategy_diagnostic_result']
            st.json(report['common_interval'])
            st.dataframe(pd.DataFrame(report['comparisons']), hide_index=True)
            st.dataframe(pd.DataFrame(report['year_segments']), hide_index=True)
            st.line_chart(navs)
            st.json({'timing': report['timing'], 'failed_parameters': report['failures'], 'history': report['declaration']})
            for note in report['limitations']:
                st.caption(note)
        if st.button("让模型解读本次数字"):
            try:
                st.session_state["draft"] = draft_commentary(st.session_state["run"], client(), result["metrics"])["draft"]
            except Exception as exc:
                st.error(str(exc))
        if "draft" in st.session_state:
            st.caption("模型解读草稿 · 尚未人工审阅")
            st.write(st.session_state["draft"])
show_outputs()
