"""Presentation only: source values, rule outputs and scenario models stay intact."""
from __future__ import annotations

from decimal import Decimal
from html import escape

NAV_LABELS = {"示例情景": "情景测算", "自定义核查": "声明核查", "历史财务核验": "财务记录"}

STYLE = """
<style>
:root { --paper:#f6f5f0; --ink:#24322d; --muted:#737971; --line:#dcded5; --pine:#285b4c; }
.stApp { background:var(--paper); color:var(--ink); }
html, body, [data-testid="stAppViewContainer"] { font-family:'Microsoft YaHei','PingFang SC',sans-serif; }
[data-testid="stHeader"] { background:transparent; }
[data-testid="stToolbar"], [data-testid="stAppDeployButton"], #MainMenu { display:none; }
[data-testid="stMainBlockContainer"] { max-width:1240px; padding:3.1rem 3.5rem 4rem; }
[data-testid="stSidebar"] { background:#eeefe8; border-right:1px solid var(--line); }
[data-testid="stSidebarContent"] { padding-top:1.25rem; }
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap:1.2rem; }
.c2v-brand { padding:6px 0 25px; border-bottom:1px solid #c8cfc2; }
.c2v-brand-name { font:26px/1.2 Georgia,serif; letter-spacing:-.8px; }
.c2v-brand-sub { color:#6b766b; font-size:12px; margin-top:9px; letter-spacing:2px; }
[data-testid="stSidebar"] [data-testid="stRadioOption"] { padding:12px 16px; border-left:2px solid transparent; border-radius:0; width:100%; }
[data-testid="stSidebar"] [data-testid="stRadioOption"]:has(input:checked) { background:#dfe8dc; border-left-color:var(--pine); }
[data-testid="stSidebar"] [data-testid="stRadioOption"] > div > div:first-child { display:none; }
[data-testid="stSidebar"] [data-testid="stRadioOption"]:focus-within { outline:2px solid var(--pine); outline-offset:2px; }
[data-testid="stSidebar"] [data-testid="stRadioGroup"] > div { width:100%; }
[data-testid="stSidebar"] [data-testid="stRadioGroup"] { width:100%; align-items:stretch; }
[data-testid="stSidebar"] [data-testid="stRadioOption"] { min-width:100%; }
[data-testid="stSidebar"] [role="radiogroup"] { gap:4px; }
.c2v-side-note { margin-top:25px; border-top:1px solid #c8cfc2; padding-top:18px; font-size:12px; color:#6b766b; line-height:1.8; }
.c2v-kicker { font:11px/1.6 Consolas,monospace; letter-spacing:2px; color:var(--pine); margin-bottom:10px; text-transform:uppercase; }
.c2v-page-title { display:flex; align-items:baseline; justify-content:space-between; gap:16px; margin-bottom:7px; }
.c2v-page-title h1 { font:36px/1.35 'SimSun','Songti SC',Georgia,serif; color:var(--ink); margin:0; padding:0; letter-spacing:.5px; }
.c2v-page-code { font:13px Consolas,monospace; color:var(--muted); letter-spacing:1px; }
.c2v-description { margin:0 0 20px; color:#677266; font-size:14px; line-height:1.7; }
.c2v-rule { height:1px; background:var(--line); margin:8px 0 20px; }
.c2v-note { padding:11px 14px; border-left:2px solid #869b7f; background:#eeefe6; font-size:13px; color:#586452; line-height:1.7; margin:8px 0 12px; }
.c2v-note.attention { border-left-color:#997845; background:#f0ede3; color:#756346; }
.c2v-section { display:flex; align-items:baseline; justify-content:space-between; margin:20px 0 12px; padding-bottom:9px; border-bottom:1px solid #bcc8b8; }
.c2v-section h2 { font-size:17px; font-weight:600; margin:0; padding:0; color:var(--ink); }
.c2v-section span { font-size:12px; color:var(--muted); }
.c2v-empty { padding:38px 0 45px; border-top:1px solid var(--line); border-bottom:1px solid var(--line); }
.c2v-empty strong { font-size:20px; font-weight:500; }
.c2v-empty p { max-width:640px; font-size:14px; color:var(--muted); line-height:1.9; margin-top:12px; }
.c2v-verdict { padding:18px 0; border-top:2px solid #80947c; border-bottom:1px solid var(--line); margin-top:14px; }
.c2v-verdict-label { font-size:12px; letter-spacing:1px; color:var(--muted); }
.c2v-verdict h3 { font:25px/1.45 'SimSun','Songti SC',serif; margin:9px 0; padding:0; }
.c2v-verdict p { font-size:14px; color:#596558; margin:0; line-height:1.7; }
.c2v-facts { display:flex; gap:28px; border-top:1px solid var(--line); border-bottom:1px solid var(--line); padding:17px 0; margin:8px 0 10px; }
.c2v-fact { flex:1; padding-right:14px; }
.c2v-fact + .c2v-fact { border-left:1px solid var(--line); padding-left:24px; }
.c2v-fact-label { font-size:12px; color:var(--muted); margin-bottom:8px; }
.c2v-fact-value { font:29px/1.15 Georgia,'SimSun',serif; font-variant-numeric:tabular-nums; }
.c2v-fact-unit { font-size:11px; color:var(--muted); margin-left:7px; }
[data-testid="stMarkdownContainer"] { color:var(--ink); font-family:'Microsoft YaHei','PingFang SC',sans-serif; }
[data-testid="stMarkdownContainer"] p { line-height:1.7; }
[data-testid="stWidgetLabel"] p { font-size:12px; color:#667260; }
[data-testid="stCaptionContainer"] { color:var(--muted); font-size:12px; }
[data-baseweb="select"] > div, [data-baseweb="input"], [data-baseweb="textarea"] { background:#fbfbf7; border-color:#cdd3c7; border-radius:3px; }
[data-testid="stSelectbox"] [role="combobox"] { color:var(--ink); font-family:'Microsoft YaHei','PingFang SC',sans-serif; }
[data-baseweb="textarea"] textarea { font-size:14px; }
[data-testid="stForm"] { padding:22px; border:1px solid var(--line); border-radius:2px; background:#fafaf6; }
[data-testid="stBaseButton-secondary"], [data-testid="stBaseButton-secondaryFormSubmit"], [data-testid="stBaseButton-primary"] { border-radius:3px; font-size:13px; min-height:38px; }
[data-testid="stBaseButton-primary"], [data-testid="stBaseButton-primaryFormSubmit"] { background:var(--pine); color:#fff; border-color:var(--pine); border-radius:3px; }
[data-testid="stBaseButton-primary"] [data-testid="stMarkdownContainer"], [data-testid="stBaseButton-primaryFormSubmit"] [data-testid="stMarkdownContainer"] { color:inherit; }
[data-testid="stBaseButton-primary"]:hover, [data-testid="stBaseButton-primaryFormSubmit"]:hover { background:#20493d; color:#fff; border-color:#20493d; }
[data-testid="stBaseButton-primary"]:focus, [data-testid="stBaseButton-primaryFormSubmit"]:focus { color:#fff; border-color:#20493d; box-shadow:0 0 0 2px #c0cfc0; }
[data-testid="stBaseButton-secondary"] { background:transparent; border-color:#bdc8b5; color:var(--ink); }
[data-testid="stExpander"] { border-color:var(--line); border-radius:2px; }
[data-testid="stTabs"] [role="tablist"] { border-bottom:1px solid var(--line); gap:24px; }
[data-testid="stTabs"] [role="tab"] { font-size:13px; }
[data-testid="stTabs"] [role="tab"][aria-selected="true"] { color:var(--pine); }
[data-baseweb="tab-highlight"] { background:var(--pine); }
[data-testid="stTabs"] .react-aria-SelectionIndicator { background:var(--pine) !important; }
[data-testid="stTable"] { font-size:13px; }
[data-testid="stTable"] th { background:#e9ede3; color:#53644e; font-weight:500; }
[data-testid="stTable"] td, [data-testid="stTable"] th { border-bottom:1px solid var(--line); padding:9px 12px; }
[data-testid="stTable"] td:not(:first-child) { text-align:right; font-variant-numeric:tabular-nums; }
[data-testid="stTable"] td p, [data-testid="stTable"] th p { font-size:13px; }
[data-testid="stTable"] td:not(:first-child) p { text-align:right; }
[data-testid="stAlert"] { border-radius:2px; font-size:14px; }
@media(max-width:800px) {
 [data-testid="stMainBlockContainer"] { padding:2.8rem 1.2rem 3rem; }
 .c2v-page-title h1 { font-size:29px; }
 .c2v-facts { display:block; }
 .c2v-fact { display:flex; align-items:baseline; justify-content:space-between; padding:8px 0; }
 .c2v-fact-value { font-size:23px; }
 .c2v-fact + .c2v-fact { padding-left:0; border-left:none; }
 .c2v-fact-unit { white-space:nowrap; }
}
@media(prefers-reduced-motion:reduce) { *, *::before, *::after { transition:none !important; animation:none !important; } }
</style>
"""


def page_heading(st, title: str, description: str, *, code: str = "", section: str = "") -> None:
    st.markdown(f'<div class="c2v-kicker">{escape(section)}</div>'
                f'<div class="c2v-page-title"><h1>{escape(title)}</h1>'
                f'<span class="c2v-page-code">{escape(code)}</span></div>'
                f'<p class="c2v-description">{escape(description)}</p>', unsafe_allow_html=True)


def section_heading(st, title: str, detail: str = "") -> None:
    st.markdown(f'<div class="c2v-section"><h2>{escape(title)}</h2><span>{escape(detail)}</span></div>', unsafe_allow_html=True)


def note(st, text: str, *, attention: bool = False) -> None:
    css = "c2v-note attention" if attention else "c2v-note"
    st.markdown(f'<div class="{css}">{escape(text)}</div>', unsafe_allow_html=True)


def verdict_html(title: str, detail: str) -> str:
    return ('<div class="c2v-verdict"><div class="c2v-verdict-label">核查结果</div>'
            f'<h3>{escape(title)}</h3><p>{escape(detail)}</p></div>')


def facts(st, entries: list[tuple[str, str, str]]) -> None:
    parts = [f'<div class="c2v-fact"><div class="c2v-fact-label">{escape(label)}</div>'
             f'<div class="c2v-fact-value">{escape(value)}<span class="c2v-fact-unit">{escape(unit)}</span></div></div>'
             for label, value, unit in entries]
    st.markdown('<div class="c2v-facts">' + ''.join(parts) + '</div>', unsafe_allow_html=True)


def financial_comparison(records: list[dict]) -> list[dict]:
    periods = sorted({r['report_period'] for r in records}, reverse=True)
    result = {}
    for r in records:
        key = (r['statement_scope'], r['period_type'], r['canonical_metric'])
        if key not in result:
            result[key] = {'指标': r['metric_original']}
        column = r['report_period'][:4]
        if column in result[key]:
            raise ValueError('Multiple revisions cannot be combined in a display row')
        result[key][column] = '—' if r['value_status'] == 'missing' else f"{Decimal(r['value_cny']) / Decimal(1000000):,.3f}"
    return [{'指标': row['指标'], **{p[:4]: row.get(p[:4], '—') for p in periods}} for row in result.values()]


def scenario_rows(scenarios: dict) -> list[dict]:
    labels = {'base': '基准', 'upside': '上行', 'downside': '下行'}
    return [{'情景': labels.get(name, name), **{
        label: f"{Decimal(str(s[key])) * 10:,.2f}" for label, key in (
            ('企业价值（亿元）', 'enterprise_value_bn'), ('2027收入（亿元）', 'revenue_2027_bn'),
            ('2027自由现金流（亿元）', 'fcf_2027_bn'))}} for name, s in scenarios.items()]


def assumption_rows(economics: dict | None) -> list[dict]:
    rows = []
    for a in (economics or {}).get('assumption_set', {}).get('assumptions', []):
        value = '仅定性判断' if a.get('qualitative_only') else (
            f"{a['delta_pct'] * 100:+.2f}%" if a.get('delta_pct') is not None else '未给出')
        rows.append({'变量': a.get('variable_label') or a.get('variable', ''), '模型中的改动': value,
                     '依据': a.get('rule_name', ''), '规则证据等级': {'high': '高', 'medium': '中', 'low': '低'}.get(a.get('evidence_grade'), '未提供')})
    return rows
