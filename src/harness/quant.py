"""Daily long-only research with explicit next-close execution and paid turnover."""
from __future__ import annotations

from .module_stamp import source_stamp
_c2v_loaded_source_hash = source_stamp(__file__)

import math
import re

import numpy as np
import pandas as pd

from .store import Run


def prepare(frame: pd.DataFrame, mapping: dict, strategy: str) -> pd.DataFrame:
    required = ["date", "stock", "close"] + (["factor", "available_at"] if strategy == "factor" else [])
    if len(set(mapping.get(k) for k in required)) != len(required) or any(mapping.get(k) not in frame for k in required):
        raise ValueError("列映射缺失或重复。")
    data = frame[[mapping[k] for k in required]].copy()
    data.columns = required
    data["stock"] = data["stock"].astype(str).str.strip()
    if not data["stock"].map(lambda s: bool(re.fullmatch(r"[0-9]{6}", s))).all():
        raise ValueError("股票代码须为六位文本；Excel 丢失前导零时请先修正，不自动猜代码。")
    if not data["date"].astype(str).str.fullmatch(r"\d{4}-\d{2}-\d{2}").all():
        raise ValueError("交易日期须为 YYYY-MM-DD。")
    data["date"] = pd.to_datetime(data["date"], errors="raise")
    if data.duplicated(["date", "stock"]).any():
        raise ValueError("同一交易日、股票有重复记录；请先处理更正版本。")
    data["close"] = pd.to_numeric(data["close"], errors="raise")
    if not np.isfinite(data["close"]).all() or (data["close"] <= 0).any():
        raise ValueError("复权收盘价须为有限正数，缺失价格不能按零收益处理。")
    nstocks = data["stock"].nunique()
    if not data.groupby("date")["stock"].nunique().eq(nstocks).all():
        raise ValueError("本版要求日期×股票完整面板；请上传共同覆盖区间。停牌、上市退出与缺失价格不自动填充。")
    if len(data) > 1000000:
        raise ValueError("本版最多处理 100 万行。")
    if strategy == "factor":
        data["factor"] = pd.to_numeric(data["factor"].replace("", np.nan), errors="raise")
        if np.isinf(data["factor"].to_numpy()).any():
            raise ValueError("因子不能为无穷值。")
        # Require an explicit intraday timestamp; date-only availability is ambiguous.
        if not data["available_at"].astype(str).str.contains(r"[T ]\d{2}:\d{2}", regex=True).all():
            raise ValueError("因子可得时间须包含时分，如 2025-01-02T14:30:00+08:00。")
        stamps = pd.to_datetime(data["available_at"], errors="raise", utc=True, format="mixed")
        if not data["available_at"].astype(str).str.contains(r"(?:Z|[+-]\d{2}:?\d{2})$", regex=True).all():
            raise ValueError("因子可得时间须包含时区。")
        cutoff = (data["date"] + pd.Timedelta(hours=15)).dt.tz_localize("Asia/Shanghai").dt.tz_convert("UTC")
        data["eligible"] = stamps <= cutoff
        data["factor"] = data["factor"].where(data["eligible"])
    return data.sort_values(["date", "stock"]).reset_index(drop=True)


def backtest(data: pd.DataFrame, *, strategy: str = "momentum", lookback: int = 20,
             top_n: int = 10, fee_bps: float = 10, direction: str = "high") -> dict:
    if strategy not in {"momentum", "factor"} or direction not in {"high", "low"}:
        raise ValueError("仅支持动量或已有因子排序，方向 high/low。")
    prices = data.pivot(index="date", columns="stock", values="close").sort_index()
    if not 1 <= top_n <= len(prices.columns) or not 1 <= lookback <= 252:
        raise ValueError("持仓数不得超过股票数；动量窗口须为 1—252 个交易日。")
    if not math.isfinite(fee_bps) or not 0 <= fee_bps <= 1000:
        raise ValueError("单边交易费率须为 0—1000 bps。")
    scores = prices / prices.shift(lookback) - 1 if strategy == "momentum" else data.pivot(index="date", columns="stock", values="factor").reindex_like(prices)
    if np.isinf(scores.to_numpy()).any():
        raise ValueError("信号计算溢出，请核对价格范围。")
    enough = scores.notna().sum(axis=1) >= top_n
    ranked = scores.rank(axis=1, method="first", ascending=direction == "low")
    # With ascending=False, rank 1 is highest. Stable stock-code tie break.
    targets = ((ranked <= top_n) & enough.to_numpy()[:, None]).astype(float) / top_n
    # Signal at T close, execute T+1 close, return begins T+1 -> T+2.
    executed = targets.shift(1).fillna(0)
    held = executed.shift(1).fillna(0)
    asset_returns = prices / prices.shift(1) - 1
    if np.isinf(asset_returns.to_numpy()).any():
        raise ValueError("收益计算溢出，请核对价格范围。")
    gross = (held * asset_returns).sum(axis=1, min_count=len(prices.columns)).fillna(0)
    # Turnover includes drift caused by price moves, including equal-weight rebalances.
    pretrade = held * (1 + asset_returns.fillna(0)).div(1 + gross, axis=0)
    turnover = (executed - pretrade).abs().sum(axis=1)
    cost = turnover * fee_bps / 10000
    # Fee measured as a fraction of pre-trade NAV; scale the remaining risky exposure.
    net = (1 + gross) * (1 - cost) - 1
    active = executed.sum(axis=1).gt(0) | held.sum(axis=1).gt(0) | turnover.gt(0)
    if not active.any():
        raise ValueError("没有可成交信号；请增加样本或核对因子可得时间、窗口和持仓数。")
    start = active[active].index[0]
    daily = pd.DataFrame({"gross_return": gross, "turnover_two_sided": turnover,
                          "cost_fraction_pretrade_nav": cost, "net_return": net}).loc[start:].copy()
    daily["nav"] = (1 + daily["net_return"]).cumprod()
    # Peak includes initial NAV=1, so an initial fee cannot vanish from drawdown.
    peak = daily["nav"].cummax().clip(lower=1)
    daily["drawdown"] = daily["nav"] / peak - 1
    # Same entry date, equal-weight daily rebalance and fee model for the benchmark.
    benchmark_gross = asset_returns.mean(axis=1).loc[start:].copy()
    benchmark_gross.iloc[0] = 0
    benchmark_drift = (1 + asset_returns.loc[start:]).div(1 + benchmark_gross, axis=0) / len(prices.columns)
    benchmark_turnover = (1 / len(prices.columns) - benchmark_drift).abs().sum(axis=1)
    benchmark_turnover.iloc[0] = 1
    benchmark_net = (1 + benchmark_gross) * (1 - benchmark_turnover * fee_bps / 10000) - 1
    daily["benchmark_nav"] = (1 + benchmark_net).cumprod()
    daily["benchmark_net_return"] = benchmark_net
    if not np.isfinite(daily.to_numpy()).all() or (daily["nav"] <= 0).any():
        raise ValueError("净值计算溢出或下溢，请核对数据和样本范围。")
    std = daily["net_return"].std(ddof=1)
    metrics = {"days": len(daily), "stocks": len(prices.columns), "total_return": float(daily["nav"].iloc[-1] - 1),
               "annualized_return_252": float(daily["nav"].iloc[-1] ** (252 / len(daily)) - 1),
               "sharpe_zero_rf_252": None if not std or not math.isfinite(std) else float(daily["net_return"].mean() / std * np.sqrt(252)),
               "max_drawdown": float(daily["drawdown"].min()), "total_turnover": float(turnover.loc[start:].sum()),
               "strategy": strategy, "lookback": lookback if strategy == "momentum" else None,
               "top_n": top_n, "fee_bps_single_side": fee_bps, "direction": direction,
               "execution": "signal_close_T; trade_close_T+1; earn_T+1_to_T+2",
               "limitations": ["用户确认复权价格；工具不核验复权算法", "完整面板、每日等权再平衡、允许碎股",
                               "未模拟涨跌停、停牌、冲击成本、成交量限制", "样本内研究，不表示样本外收益",
                               "不在样本末尾强制清仓；基准同日进入、每日等权再平衡并扣费"]}
    # Positions are portfolio weights after execution; net NAV is saved separately.
    positions = []
    dates = list(prices.index)
    for i, dt in enumerate(dates):
        if i == 0 or not executed.loc[dt].any():
            continue
        for stock, weight in executed.loc[dt].items():
            if weight > 0:
                positions.append({"signal_date": dates[i - 1].date().isoformat(), "execution_date": dt.date().isoformat(),
                                  "first_return_date": None if i + 1 == len(dates) else dates[i + 1].date().isoformat(),
                                  "stock": stock, "target_weight_after_trade": float(weight)})
    # Forward return is used for evaluation only, never to choose positions.
    forward = prices.shift(-2) / prices.shift(-1) - 1
    ic_rows = []
    for dt in scores.index:
        pair = pd.DataFrame({"score": scores.loc[dt], "future": forward.loc[dt]}).dropna()
        ic = None
        if len(pair) >= 3 and pair["score"].nunique() > 1 and pair["future"].nunique() > 1:
            ic = float(pair["score"].rank().corr(pair["future"].rank()))
        ic_rows.append({"signal_date": dt.date().isoformat(), "pairs": len(pair), "rank_ic": ic})
    return {"daily": daily, "positions": pd.DataFrame(positions), "ic": pd.DataFrame(ic_rows), "metrics": metrics}


def save(run: Run, data: pd.DataFrame, result: dict) -> None:
    run.write("cleaned_data.csv", data.to_csv(index=False).encode("utf-8-sig"))
    run.write("daily.csv", result["daily"].to_csv(index_label="date").encode("utf-8-sig"))
    run.write("positions.csv", result["positions"].to_csv(index=False).encode("utf-8-sig"))
    run.write("rank_ic.csv", result["ic"].to_csv(index=False).encode("utf-8-sig"))
    run.write("metrics.json", result["metrics"])
    metrics = result["metrics"]
    run.write("quant_report.md", "# 量化研究记录\n\n" +
              f"样本收益：{metrics['total_return']:.2%}；最大回撤：{metrics['max_drawdown']:.2%}。"
              "这两个数字仅对应上传样本和所选参数，不是比赛测试成绩。\n\n"
              "信号在 T 日收盘后确定，T+1 日收盘成交，T+2 日计入第一笔持仓收益。费用按双向换手和单边 bps 扣除。"
              "买入费用在首次成交日计入；样本末尾不强制清仓。\n\n" +
              "\n".join("- " + text for text in metrics["limitations"]) + "\n")
    run.event("quant_completed", observations=len(data), evaluation_days=metrics["days"])
