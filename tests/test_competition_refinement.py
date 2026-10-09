import copy

import numpy as np
import pytest

from competition import refinement as r
from test_competition_baseline import synthetic_days


def test_quadratic_signal_is_learned_without_linear_direction():
    days = synthetic_days(8)
    for day in days:
        x, _ = r.features(day, "quadratic")
        day["return"] = 0.004 * x[:, 100]
    model = r.fit(days[:4], "quadratic")
    assert model["coef"][100] > 0.003
    selected = list(r.holdings(r.scores(model, days[4:]), "daily_2std"))
    assert all(len(set(stocks)) == 20 for _, stocks in selected)
    assert days[4].set_index("stock_id").loc[list(selected[0][1]), "return"].mean() > 0.004


@pytest.mark.parametrize("kind", r.FEATURES)
@pytest.mark.parametrize("policy", r.POLICIES)
def test_future_factors_and_realized_returns_do_not_change_prefix(kind, policy):
    days = synthetic_days(7)
    model = r.fit(days[:3], kind)
    expected = list(r.holdings(r.scores(model, days[3:]), policy))
    changed = copy.deepcopy(days[3:])
    for day in changed:
        day["return"] = np.nan
    changed[-1].loc[:, r.b.FACTORS] *= -100
    actual = list(r.holdings(r.scores(model, changed), policy))
    assert actual[:-1] == expected[:-1]


def test_overlapping_dates_empty_training_and_bad_models_are_rejected():
    days = synthetic_days(4)
    model = r.fit(days[:2], "linear")
    with pytest.raises(ValueError):
        list(r.scores(model, days[1:]))
    with pytest.raises(ValueError):
        r.fit([], "linear")
    model["coef"][0] = float("nan")
    with pytest.raises(ValueError):
        list(r.scores(model, days[2:]))
