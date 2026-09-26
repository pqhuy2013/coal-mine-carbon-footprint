import pytest

from carbon_pricing import carbon_cost, price_path


def test_carbon_cost():
    assert carbon_cost(1250, 85.0) == pytest.approx(106250.0)


def test_carbon_cost_rejects_negative():
    with pytest.raises(ValueError):
        carbon_cost(-1, 10)
    with pytest.raises(ValueError):
        carbon_cost(1, -10)


def test_price_path():
    assert price_path(50.0, 0.05, 3) == pytest.approx([50.0, 52.5, 55.125])


def test_price_path_empty():
    assert price_path(50.0, 0.05, 0) == []


def test_price_path_rejects_invalid_growth():
    with pytest.raises(ValueError):
        price_path(50.0, -1.0, 3)
