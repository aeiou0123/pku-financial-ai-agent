"""Annual earnings bridges from confirmed facts; accounting is not causality."""
from __future__ import annotations

from collections import defaultdict
from decimal import Decimal, localcontext
import io

import pandas as pd

from .store import Run

GROUP_FIELDS = ("stock_code", "company", "statement_scope", "published_at", "revision_flag", "source_database")
LABELS = {"revenue": "营业收入", "cost_of_revenue": "营业成本", "net_profit_parent": "归母净利润",
          "pretax_profit": "利润总额", "income_tax_expense": "所得税费用", "net_profit": "合并净利润",
          "operating_cash_flow": "经营现金流", "capex_cash_paid": "购建长期资产支付现金"}


def comparison_groups(records: list[dict]) -> list[dict]:
    groups = defaultdict(list)
    for row in records:
        if row.get("period_type") == "annual":
            groups[tuple(row.get(k, "") for k in GROUP_FIELDS)].append(row)
    return [{"identity": dict(zip(GROUP_FIELDS, key)), "periods": sorted({r["report_period"] for r in rows}),
             "records": rows} for key, rows in sorted(groups.items())]


def earnings_bridge(records: list[dict], earlier: str, later: str) -> dict:
    """Compare one annual disclosure vintage, never choose a restatement silently."""
    if len(earlier) != 10 or len(later) != 10 or not earlier.endswith("-12-31") or not later.endswith("-12-31"):
        raise ValueError("本版只比较连续两个自然年度的年度报表，不比较中期或非自然年。")
    if int(later[:4]) - int(earlier[:4]) != 1:
        raise ValueError("请选择连续两年，前期须早于本期。")
    selected = [r for r in records if r.get("period_type") == "annual" and r.get("report_period") in {earlier, later}]
    groups = comparison_groups(selected)
    if len(groups) != 1:
        raise ValueError("两期须为同公司、同披露日、同报表口径、同修订版本和同来源类型；请先选择一组。")
    values, refs = {}, {}
    for row in selected:
        if row.get("canonical_metric") not in LABELS:
            continue
        key = (row["report_period"], row["canonical_metric"])
        if key in values:
            raise ValueError("同一期指标有多条记录；请先人工解决重复或更正，不能自动择一。")
        amount = row.get("value_cny", "")
        if row.get("value_status") != "observed" or amount in {"", None}:
            continue
        value = Decimal(str(amount))
        if not value.is_finite():
            raise ValueError("财务金额须为有限值。")
        values[key] = value
        refs[key] = {k: row.get(k, "") for k in ("report_period", "canonical_metric", "metric_original", "value_original",
                    "unit", "value_cny", "source_file", "source_locator", "source_sha256", "published_at",
                    "statement_scope", "revision_flag")}
    required = {(period, metric) for period in (earlier, later) for metric in ("revenue", "cost_of_revenue")}
    if not required <= values.keys():
        raise ValueError("毛利变化解释需要两期营业收入和营业成本；缺失值不能补零。")
    if any(values[(p, "revenue")] <= 0 for p in (earlier, later)):
        raise ValueError("两期收入须为正数。")

    with localcontext() as context:
        context.prec = 40
        revenue0, revenue1 = (values[(p, "revenue")] for p in (earlier, later))
        gross0 = revenue0 - values[(earlier, "cost_of_revenue")]
        gross1 = revenue1 - values[(later, "cost_of_revenue")]
        margin0, margin1 = gross0 / revenue0, gross1 / revenue1
        revenue_effect = (revenue1 - revenue0) * margin0
        margin_effect = revenue1 * (margin1 - margin0)

        def number(value):
            return str(value.quantize(Decimal("0.000001")))

        def source(period, metrics):
            return [refs[(period, metric)] for metric in metrics if (period, metric) in refs]

        indicators = []

        def indicator(key, label, value0, value1, unit, metrics, change_kind="amount"):
            change = value1 - value0
            indicators.append({"id": key, "指标": label, "前期": number(value0), "本期": number(value1),
                               "变化": number(change), "单位": unit, "变化口径": change_kind,
                               "同比百分比": number(change / value0 * 100) if value0 > 0 and change_kind == "amount" else None,
                               "sources": source(earlier, metrics) + source(later, metrics)})

        indicator("revenue", "营业收入", revenue0, revenue1, "元", ["revenue"])
        indicator("gross_profit", "毛利", gross0, gross1, "元", ["revenue", "cost_of_revenue"])
        indicator("gross_margin", "毛利率", margin0 * 100, margin1 * 100, "%", ["revenue", "cost_of_revenue"], "百分点")
        for metric in ("net_profit_parent", "net_profit", "operating_cash_flow", "capex_cash_paid"):
            if all((p, metric) in values for p in (earlier, later)):
                indicator(metric, LABELS[metric], values[(earlier, metric)], values[(later, metric)], "元", [metric])
        warnings = []
        if all((p, m) in values for p in (earlier, later) for m in ("operating_cash_flow", "net_profit")):
            if all(values[(p, "net_profit")] > 0 for p in (earlier, later)):
                indicator("cash_conversion", "经营现金流／合并净利润", values[(earlier, "operating_cash_flow")] / values[(earlier, "net_profit")],
                          values[(later, "operating_cash_flow")] / values[(later, "net_profit")], "倍", ["operating_cash_flow", "net_profit"], "倍数差")
            else:
                warnings.append("合并净利润非正，未计算经营现金流／净利润比率。")
        if all((p, m) in values for p in (earlier, later) for m in ("operating_cash_flow", "capex_cash_paid")):
            indicator("ocf_less_capex", "经营现金流减购建长期资产支出", values[(earlier, "operating_cash_flow")] - values[(earlier, "capex_cash_paid")],
                      values[(later, "operating_cash_flow")] - values[(later, "capex_cash_paid")], "元", ["operating_cash_flow", "capex_cash_paid"])

        bridge = [{"因素": "收入变化贡献（固定前期毛利率）", "贡献_元": number(revenue_effect),
                   "公式": "(收入1-收入0)×毛利率0", "sources": source(earlier, ["revenue", "cost_of_revenue"]) + source(later, ["revenue"])},
                  {"因素": "毛利率变化贡献（按本期收入）", "贡献_元": number(margin_effect),
                   "公式": "收入1×(毛利率1-毛利率0)", "sources": source(earlier, ["revenue", "cost_of_revenue"]) + source(later, ["revenue", "cost_of_revenue"])}]
        target, change = "毛利", gross1 - gross0
        profit_fields = ("pretax_profit", "income_tax_expense", "net_profit", "net_profit_parent")
        missing = [f"{period}：{LABELS[m]}" for period in (earlier, later) for m in profit_fields if (period, m) not in values]
        if not missing:
            for p in (earlier, later):
                if abs(values[(p, "pretax_profit")] - values[(p, "income_tax_expense")] - values[(p, "net_profit")]) > Decimal("0.01"):
                    raise ValueError("利润总额－所得税费用与合并净利润不勾稽；请核对口径及原件。")
            pre0, pre1 = (values[(p, "pretax_profit")] for p in (earlier, later))
            minority0, minority1 = (values[(p, "net_profit")] - values[(p, "net_profit_parent")] for p in (earlier, later))
            residual = (pre1 - gross1) - (pre0 - gross0)
            tax = -(values[(later, "income_tax_expense")] - values[(earlier, "income_tax_expense")])
            minority = -(minority1 - minority0)
            for label, amount, formula, metrics in [
                ("其余税前项目净变化（待拆解）", residual, "(利润总额1-毛利1)-(利润总额0-毛利0)", ["pretax_profit", "revenue", "cost_of_revenue"]),
                ("所得税费用变化", tax, "-(所得税费用1-所得税费用0)", ["income_tax_expense"]),
                ("少数股东损益变化", minority, "-[(合并净利1-归母净利1)-(合并净利0-归母净利0)]", ["net_profit", "net_profit_parent"])]:
                bridge.append({"因素": label, "贡献_元": number(amount), "公式": formula,
                               "sources": source(earlier, metrics) + source(later, metrics)})
            target = "归母净利润"
            change = values[(later, "net_profit_parent")] - values[(earlier, "net_profit_parent")]
        else:
            warnings.append("归母净利桥缺少字段，当前仅分解毛利；未填零。")
        total = sum(Decimal(row["贡献_元"]) for row in bridge)
        if abs(total - change) > Decimal("0.01"):
            raise ValueError("贡献合计不能复算目标变化，请核对输入。")
        findings = [f"毛利率变化 {number((margin1-margin0)*100)} 个百分点；其对应的毛利变化贡献为 {number(margin_effect)} 元。",
                    "收入贡献尚未区分销量、价格或产品结构，需要同口径销量与平均售价数据。",
                    "其余税前项目含费用、投资收益、减值等净影响，不能自动解释为技术突破贡献。"]
        if margin_effect < 0 and gross1 > gross0:
            findings.insert(0, "毛利增加同时毛利率下降；毛利增加不能解释为毛利率改善。")
        return {"status": "accounting_decomposition_not_causal_identification", "identity": groups[0]["identity"],
                "earlier": earlier, "later": later, "indicators": indicators, "bridge_target": target, "bridge": bridge,
                "target_change_cny": number(change), "bridge_sum_cny": number(total), "rounding_residual_cny": number(change-total),
                "missing_fields": missing, "warnings": warnings, "findings": findings,
                "limitations": ["已确认报表数据的会计分解，不是技术、订单或客户的因果贡献。",
                                "两期采用同一披露版本；比较数也使用该原件实际披露日。",
                                "分解次序将收入与毛利率的交互项计入毛利率贡献；不是唯一的分摊方法。",
                                "经营现金流减购建长期资产支出仅为现金差额，未经调整不能称为估值用FCFF。",
                                "合并范围、会计政策或产品分部变化仍需人工查看附注；本模块未自动认证可比性。"]}


def save_diagnostics(run: Run, result: dict) -> None:
    run.write("earnings_diagnostics.json", result)
    indicators = [{k: v for k, v in row.items() if k != "sources"} for row in result["indicators"]]
    bridge = [{k: v for k, v in row.items() if k != "sources"} for row in result["bridge"]]
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        pd.DataFrame(indicators).to_excel(writer, sheet_name="两期指标", index=False)
        pd.DataFrame(bridge).to_excel(writer, sheet_name="盈利变化桥", index=False)
        sources = [ref for row in result["indicators"] for ref in row["sources"]]
        pd.DataFrame(sources).drop_duplicates().to_excel(writer, sheet_name="原件定位", index=False)
        for sheet in writer.book:
            for row in sheet:
                for cell in row:
                    if isinstance(cell.value, str) and cell.value.startswith("="):
                        cell.data_type = "s"
    run.write("earnings_diagnostics.xlsx", buffer.getvalue())
    text = ["# 盈利变化研究底稿", "", f"{result['identity']['company']}：{result['earlier']} → {result['later']}",
            f"实际来源披露日：{result['identity']['published_at']}。", "", "## 会计分解", "",
            f"{result['bridge_target']}变化：{result['target_change_cny']} 元；贡献合计：{result['bridge_sum_cny']} 元。", ""]
    text += [f"- {r['因素']}：{r['贡献_元']} 元；{r['公式']}" for r in bridge]
    text += ["", "## 研究发现与待查问题", ""] + ["- " + line for line in result["findings"] + result["warnings"]]
    text += ["", "## 适用边界", ""] + ["- " + line for line in result["limitations"]]
    text += ["", "各计算的原件、页码、指纹与原值见 earnings_diagnostics.json；可编辑底稿见同名 XLSX。"]
    run.write("earnings_diagnostics.md", "\n".join(text))
    run.event("earnings_diagnostics_completed", target=result["bridge_target"], earlier=result["earlier"], later=result["later"])
