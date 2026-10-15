"""Shared sampling rules and compatibility with the two public model APIs."""
from copy import deepcopy
from pathlib import Path

import pytest

from farm_strategy import comparison, model


def weather_rows():
    return [{"year": year, "label": str(year)}
            for year in (2025, 2015, 2017, 2016, 2019, 2020, 2006)]


@pytest.mark.parametrize("q, expected", [
    (0, 0), (0.1, 3.0), (0.25, 7.5), (0.5, 15.0), (0.9, 27.0), (1, 30),
])
def test_quantile_interpolates_sorted_values_without_mutating_input(q, expected):
    from farm_strategy.sampling import quantile

    values = [30, 0, 20, 10]
    assert quantile(values, q) == pytest.approx(expected)
    assert values == [30, 0, 20, 10]


def test_quantile_single_observation_and_legacy_imports():
    from farm_strategy.sampling import quantile

    assert quantile([7], 0.1) == 7
    assert quantile([7], 0.9) == 7
    assert model.quantile is quantile
    assert comparison.quantile is quantile


def test_quantile_keeps_empty_input_error():
    from farm_strategy.sampling import quantile

    with pytest.raises(IndexError):
        quantile([], 0.5)


@pytest.mark.parametrize("window, expected_years", [
    ("recent10", [2025, 2017, 2016, 2019, 2020]),
    ("all20", [2025, 2015, 2017, 2016, 2019, 2020, 2006]),
])
def test_choose_pool_preserves_order_rows_and_source_weather(window, expected_years):
    from farm_strategy.sampling import choose_pool

    weather = weather_rows()
    original = deepcopy(weather)
    pool = choose_pool(weather, window)
    assert [row["year"] for row in pool] == expected_years
    assert weather == original
    assert pool is not weather
    assert all(any(row is source for source in weather) for row in pool)
    assert comparison.choose_pool(weather, window) == pool


@pytest.mark.parametrize("window", ["recent5", None, 2016])
def test_choose_pool_rejects_unknown_window_before_observation_count(window):
    from farm_strategy.sampling import choose_pool

    with pytest.raises(ValueError, match="^window must be recent10 or all20$"):
        choose_pool([], window)


def test_choose_pool_accepts_caller_specific_window_error():
    from farm_strategy.sampling import choose_pool

    with pytest.raises(ValueError, match="^Invalid window$"):
        choose_pool([], "recent5", invalid_window_message="Invalid window")


@pytest.mark.parametrize("window", ["recent10", "all20"])
def test_choose_pool_requires_five_selected_observations(window):
    from farm_strategy.sampling import choose_pool

    weather = [{"year": year} for year in (2016, 2017, 2018, 2019)]
    if window == "recent10":
        weather.insert(0, {"year": 2015})
    with pytest.raises(ValueError, match="^Need >=5 annual observations$"):
        choose_pool(weather, window)


@pytest.mark.parametrize("operation, message", [
    (model.simulate, "Invalid window"),
    (comparison.compare_plans, "window must be recent10 or all20"),
])
def test_public_callers_keep_their_window_errors(operation, message):
    with pytest.raises(ValueError, match=f"^{message}$"):
        if operation is model.simulate:
            operation("field_trial", "base", [], {}, paths=1, window="recent5")
        else:
            operation([], {}, paths=1, window="recent5")


def test_public_callers_keep_insufficient_observations_error():
    with pytest.raises(ValueError, match="^Need >=5 annual observations$"):
        model.simulate("field_trial", "base", [], {}, paths=1)
    with pytest.raises(ValueError, match="^Need >=5 annual observations$"):
        comparison.compare_plans([], {}, paths=1)


def test_public_callers_keep_path_validation_before_window_validation():
    with pytest.raises(ValueError, match="^paths must be 1–100,000$"):
        model.simulate("field_trial", "base", [], {}, paths=0, window="recent5")
    with pytest.raises(ValueError, match="^paths must be 1–100,000$"):
        comparison.compare_plans([], {}, paths=0, window="recent5")


def test_simulate_keeps_legacy_fractional_path_error():
    with pytest.raises(TypeError, match="cannot be interpreted as an integer"):
        model.simulate("field_trial", "base", weather_rows(), {}, paths=1.5)
    with pytest.raises(ValueError, match="^paths must be 1–100,000$"):
        comparison.compare_plans(weather_rows(), {}, paths=1.5)


def test_simulate_keeps_legacy_boolean_path_acceptance():
    root = Path(__file__).resolve().parents[1]
    config = model.read_config(root / "configs/base.json")
    weather = model.read_weather(root / "data/processed/annual_weather.csv")

    assert model.simulate("field_trial", "base", weather, config, paths=True)["paths"] is True
    with pytest.raises(ValueError, match="^paths must be 1–100,000$"):
        comparison.compare_plans(weather, config, paths=True)
