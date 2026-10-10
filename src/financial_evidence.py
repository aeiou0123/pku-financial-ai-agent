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
    st.subheader("历史财务核验")
    st.caption("公开年报原页核对与文件校验分别记录；历史事实不自动改变固定情景。")
    try:
        snapshot = load_snapshot()
    except (OSError, ValueError, KeyError):
        st.error("历史财务样本缺失或格式不符；未展示财务结论。")
        return
    company = st.selectbox("选择财务公司", list(COMPANIES.values()), key="history_company")
    code = next(k for k, v in COMPANIES.items() if v == company)
    all_rows = company_records(snapshot, code)
    period = st.selectbox("选择报告期间", ["全部期间"] + sorted({r["report_period"] for r in all_rows}), key="history_period")
    rows = company_records(snapshot, code, period)
    if rows:
        st.table(presentation_rows(rows))
    else:
        st.info("这家公司尚无完成原页核对的公开财务样本；不把待核数据当作已核事实。")
    for limit in snapshot["limits"]:
        st.write("• " + limit)
    report = historical_report(snapshot, code, rows)
    st.download_button("下载历史财务核验 JSON", json.dumps(report, ensure_ascii=False, indent=2),
                       f"{code}_historical_reference.json", "application/json")
    st.download_button("下载历史财务报告 Markdown", historical_markdown(report),
                       f"{code}_historical_reference.md", "text/markdown")
    with st.expander("本包公开样本的年报来源与核验记录"):
        for source in snapshot["source_review"].values():
            if isinstance(source, dict) and source.get("url"):
                st.link_button("打开年报：" + source["published_at"], source["url"])
        st.json(snapshot["validation_summary"])
    if pending_root:
        pending = pending_vendor_records(pending_root, code)
        if pending:
            with st.expander("本机 CSMAR 待核原值（未进入已核财务样本）"):
                st.warning("当前正式定义与披露日不完整。原值无单位认证，不计算比率、不年化，不用于预测。")
                st.table([{k: r[k] for k in ("report_period", "field_code", "field_name", "value_original", "source_locator")} for r in pending])
                st.caption("本区仅读取本机授权目录，部署包不包含商业数据库原始导出。")
