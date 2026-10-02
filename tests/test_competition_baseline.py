from datetime import date, timedelta

import numpy as np
import pandas as pd
import pytest

from competition.baseline import FACTORS, STOCKS, daily_features, fit_days, predict_days, select_twenty, write_holdings, read_days, iso_date


def synthetic_days(count=8):
    rng = np.random.default_rng(712)
    result = []
    for i in range(count):
        d = date(2015, 1, 2) + timedelta(days=i)
        frame = pd.DataFrame(rng.normal(size=(400, 100)), columns=FACTORS)
        frame["date"] = d
        frame["asof_date"] = d - timedelta(days=1)
        frame["stock_id"] = STOCKS
        x, _ = daily_features(frame)
        frame["return"] = .002 * x[:, 0] + rng.normal(0, .0001, 400)
        result.append(frame)
    return result


def test_same_row_signal_is_learned_without_label_shift():
    days = synthetic_days()
    model = fit_days(days[:4], .001)
    assert model["coef"][0] > .0015
    output = list(predict_days(model, days[4:]))
    for (date, chosen), frame in zip(output, days[4:]):
        assert len(set(chosen)) == 20
        assert frame.set_index("stock_id").loc[list(chosen), "return"].mean() > .002


def test_future_factor_changes_do_not_change_prefix_holdings():
    days = synthetic_days()
    model = fit_days(days[:4], .001)
    expected = list(predict_days(model, days[4:], hold_bonus=.0004))
    mutated = [day.copy() for day in days[4:]]
    mutated[-1].loc[:, FACTORS] *= -100
    actual = list(predict_days(model, mutated, hold_bonus=.0004))
    assert actual[:-1] == expected[:-1]


def test_validation_returns_never_enter_decisions_or_preprocessing():
    days = synthetic_days()
    model = fit_days(days[:4], .001)
    expected = list(predict_days(model, days[4:]))
    for day in days[4:]:
        day["return"] = np.nan
    assert list(predict_days(model, days[4:])) == expected


def test_current_day_rank_transform_handles_ties_and_order():
    day = synthetic_days(1)[0]
    day[FACTORS[0]] = 3.
    x, _ = daily_features(day)
    assert np.all(x[:, 0] == 0)
    shuffled, _ = daily_features(day.sample(frac=1, random_state=4))
    assert np.array_equal(x, shuffled)


def test_overlap_or_out_of_order_is_rejected():
    days = synthetic_days()
    model = fit_days(days[:4], .001)
    with pytest.raises(ValueError):
        list(predict_days(model, days[3:]))
    with pytest.raises(ValueError):
        fit_days(days[::-1], .001)


def test_complete_stock_universe_and_information_date_required():
    day = synthetic_days(1)[0]
    with pytest.raises(ValueError):
        daily_features(day.iloc[:399])
    day["asof_date"] = day["date"]
    with pytest.raises(ValueError):
        daily_features(day)


def test_ties_incumbent_bonus_and_strict_csv(tmp_path):
    first = select_twenty(np.zeros(400))
    assert first == STOCKS[:20]
    previous = STOCKS[-20:]
    assert select_twenty(np.zeros(400), previous, .0008) == previous
    output = tmp_path / "holdings.csv"
    assert write_holdings(output, [("2020-01-02", first)]) == 20
    lines = output.read_text().splitlines()
    assert lines[0] == "date,stock_id"
    assert len(lines) == 21
    with pytest.raises(ValueError):
        select_twenty(np.zeros(400), previous, -1)


def test_saved_model_predictions_reproduce(tmp_path):
    import json
    days = synthetic_days()
    model = fit_days(days[:4], .001)
    restored = json.loads(json.dumps(model))
    assert list(predict_days(model, days[4:])) == list(predict_days(restored, days[4:]))


def test_monthly_reader_never_requests_validation_labels_for_prediction():
    data = pd.concat(synthetic_days(), ignore_index=True).drop(columns=["return"])
    class Reader:
        def read_data(self, path, start=None, end=None, columns=None):
            assert "return" not in columns
            selected = data
            if start:
                selected = selected[selected.date >= date.fromisoformat(start)]
            if end:
                selected = selected[selected.date <= date.fromisoformat(end)]
            return selected[columns]
    result = list(read_days("unused", Reader(), "2015-01-03", "2015-01-06"))
    assert len(result) == 4
    assert result[0].date.iloc[0] == date(2015, 1, 3)


@pytest.mark.parametrize("value", ["20200101", "2020-02-30", "2020-1-1"])
def test_only_canonical_valid_dates_are_accepted(value):
    with pytest.raises(ValueError):
        iso_date(value)


def test_validation_command_emits_model_official_accounting_and_control(monkeypatch, tmp_path):
    import json
    import sys
    from competition import baseline
    days = synthetic_days()
    calls = []
    class ToolContract:
        def read_data(self, path, start=None, end=None, columns=None):
            return pd.concat(days[4:], ignore_index=True)[columns]
        def backtest(self, path, train_path, start, end):
            table = pd.read_csv(path)
            assert list(table.columns) == ["date", "stock_id"]
            assert len(table) == 80
            assert all(group.stock_id.nunique() == 20 for _, group in table.groupby("date"))
            calls.append(Path(path).name)
            return {"status": "OK", "sharpe": .1, "final_nav": 1.01}
    from pathlib import Path
    monkeypatch.setattr(baseline, "official_tools", lambda path: ToolContract())
    monkeypatch.setattr(baseline, "verify_data", lambda *args: None)
    monkeypatch.setattr(baseline, "read_days", lambda *args, **kwargs: iter(days[:4] if kwargs.get("labels") else days[4:]))
    out = tmp_path / "validation"
    monkeypatch.setattr(sys, "argv", ["baseline", "validate", "--tools", "tools.py", "--train", "train.parquet",
                                      "--train-end", "2015-01-05", "--valid-start", "2015-01-06", "--valid-end", "2015-01-09", "--out", str(out)])
    baseline.main()
    result = json.loads((out / "run_summary.json").read_text())
    assert calls == ["validation.csv", "fixed20_validation.csv"]
    assert result["status"] == "COMPLETE"
    assert result["fixed20_validation"]["status"] == "OK"
    assert (out / "model.json").is_file()
