"""Historical reference display; no forecast calibration or vendor authentication."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from decimal import Decimal

COMPANIES = {"688017": "绿的谐波", "002472": "双环传动", "688160": "步科股份"}
DEFAULT_SNAPSHOT = Path(__file__).resolve().parents[1] / "data/processed/historical_public_financial.json"


def load_snapshot(path: Path = DEFAULT_SNAPSHOT) -> dict:
    snapshot = json.loads(path.read_text(encoding="utf-8"))
    if snapshot.get("schema") != "historical_public_financial_v1" or snapshot.get("forecast_updated") is not False:
        raise ValueError("Unsupported historical snapshot")
    return snapshot


def company_records(snapshot: dict, stock_code: str, period: str = "全部期间") -> list[dict]:
    return [r for r in snapshot["records"] if r["stock_code"] == stock_code
            and (period == "全部期间" or r["report_period"] == period)]


def presentation_rows(records: list[dict]) -> list[dict]:
    return [{"报告期间": r["report_period"], "实际披露日": r["published_at"],
             "报表": "合并" if r["statement_scope"] == "consolidated" else "母公司",
             "指标": r["metric_original"], "金额（百万元）":
             "缺失" if r["value_status"] == "missing" else str(Decimal(r["value_cny"]) / Decimal(1000000)),
             "期间口径": r["period_type"], "定位": r["source_locator"]} for r in records]


def pending_vendor_records(root: Path, stock_code: str) -> list[dict]:
    """Only read the explicitly supplied local ledger; never include it in deployment."""
    path = root / "derived/codex_review/historical_evidence_ledger.csv"
    if not path.is_file():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return [r for r in csv.DictReader(handle) if r["stock_code"] == stock_code]


def historical_report(snapshot: dict, stock_code: str, records: list[dict]) -> dict:
    return {"schema": "historical_reference_report_v1", "company": COMPANIES[stock_code],
            "stock_code": stock_code, "as_of": snapshot["as_of"], "records": records,
            "source_review": snapshot["source_review"], "limits": snapshot["limits"],
            "forecast_updated": False, "valuation_generated": False}


def historical_markdown(report: dict) -> str:
    lines = [f"# {report['company']} 历史财务核验", "", f"核验截至：{report['as_of']}", "",
             "历史参考，不自动校准预测或生成估值。", "",
             "|期间|披露日|指标|原值（元）|定位|", "|---|---|---|---|---|"]
    for r in report["records"]:
        safe = lambda s: str(s).replace("|", "／").replace("\n", " ")
        lines.append("|" + "|".join(safe(r[k]) for k in
                     ("report_period", "published_at", "metric_original", "value_original", "source_locator")) + "|")
    lines.extend(["", "## 限定", *["- " + x for x in report["limits"]]])
    return "\n".join(lines) + "\n"


def render_history(st, pending_root: Path | None = None) -> None:
    from src.review_ui import page_heading, section_heading, note, facts, financial_comparison
    try:
        snapshot = load_snapshot()
    except (OSError, ValueError, KeyError):
        st.error("财务记录无法读取。请检查样本文件。")
        return
    company_column, period_column = st.columns([2, 1])
    with company_column:
        company = st.selectbox("公司", list(COMPANIES.values()), key="history_company")
    code = next(k for k, v in COMPANIES.items() if v == company)
    all_rows = company_records(snapshot, code)
    with period_column:
        period = st.selectbox("报告期间", ["全部期间"] + sorted({r["report_period"] for r in all_rows}, reverse=True), key="history_period")
    rows = company_records(snapshot, code, period)
    page_heading(st, company, "2025年报 · 年度合并报表 · 披露于2026-04-23" if rows else "还没有完成原页核对的财务数据。", code=code, section="财务记录 / 年度报告")
    if rows:
        latest = max(r['report_period'] for r in rows)
        highlights = []
        for metric, label in [('revenue', '营业收入'), ('net_profit_parent', '归母净利润'), ('operating_cash_flow', '经营净现金流')]:
            item = next((r for r in rows if r['report_period'] == latest and r['canonical_metric'] == metric), None)
            if item:
                value = '—' if item['value_status'] == 'missing' else f"{Decimal(item['value_cny']) / Decimal(1000000):,.2f}"
                highlights.append((latest[:4] + ' ' + label, value, '百万元'))
        facts(st, highlights)
        section_heading(st, "年度财务", f"{len(rows)}项原始记录 · 合并报表")
        st.table(financial_comparison(rows))
        note(st, "2024比较数来自2025年报，披露日为2026-04-23。这些数据不能当作2024年当时已经可得的信息。")
        st.caption("单位：百万元，表格保留三位小数。下载文件保留元单位原值。历史记录不自动改动情景假设。")
    else:
        st.info("尚未收录已核对的公开财务记录。")
        st.write("可以查看公司的覆盖状态。待核数据尚不作为财务事实，也不用于测算。")
    report = historical_report(snapshot, code, rows)
    section_heading(st, "原件与下载" if rows else "保存覆盖记录")
    if rows:
        source = snapshot['source_review']['sample_source']
        st.write("本表取自绿的谐波2025年报，包括其中列示的2024比较数。")
        st.caption(f"披露于{source['published_at']}。原页定位和文件指纹见下载记录。")
        st.link_button("查看2025年报", source['url'])
    left, right = st.columns(2)
    with left:
        st.download_button("下载记录 · JSON", json.dumps(report, ensure_ascii=False, indent=2),
                           f"{code}_historical_reference.json", "application/json", key="history_json")
    with right:
        st.download_button("下载报告 · Markdown", historical_markdown(report),
                           f"{code}_historical_reference.md", "text/markdown", key="history_md")
    with st.expander("口径与核验明细"):
        for limit in snapshot['limits']:
            st.write("• " + limit)
        if rows:
            st.table(presentation_rows(rows))
            st.json(snapshot['validation_summary'])
    if pending_root:
        pending = pending_vendor_records(pending_root, code)
        if pending:
            with st.expander("本机待核资料 · CSMAR"):
                note(st, "字段定义和披露日期还不完整。这里只保留原值，不计算比率、不年化、不用于预测。", attention=True)
                st.table([{k: r[k] for k in ("report_period", "field_code", "field_name", "value_original", "source_locator")} for r in pending])
                st.caption("这部分资料只在授权的本机目录中保存，交付包不含商业数据库原始导出。")
