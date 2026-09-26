import pytest

from coal_mine_footprint.combustion import CombustionType, Fuel, fuel_combustion


def test_diesel_mobile_per_1000_litres():
    # 1.000 lít x 0,84 kg/lít = 0,84 t; x 43 TJ/Gg = 0,03612 TJ
    g = fuel_combustion(Fuel.DIESEL, 1000, CombustionType.MOBILE)
    assert g.co2_t == pytest.approx(0.03612 * 74.1)  # khoảng 2,68 t CO2
    assert g.ch4_t == pytest.approx(0.03612 * 4.15 / 1000)
    assert g.n2o_t == pytest.approx(0.03612 * 28.6 / 1000)


def test_diesel_stationary_uses_stationary_factors():
    g = fuel_combustion("diesel", 1000, "stationary")
    assert g.ch4_t == pytest.approx(0.03612 * 3 / 1000)
    assert g.n2o_t == pytest.approx(0.03612 * 0.6 / 1000)


def test_custom_density():
    g = fuel_combustion(Fuel.DIESEL, 1000, CombustionType.MOBILE, density_kg_per_l=0.86)
    assert g.co2_t == pytest.approx(0.86 * 43 / 1000 * 74.1)


def test_fuel_oil_in_tonnes():
    g = fuel_combustion(Fuel.FUEL_OIL, 10, CombustionType.STATIONARY)
    assert g.co2_t == pytest.approx(10 * 40.4 / 1000 * 77.4)


def test_mobile_not_supported_for_fuel_oil():
    with pytest.raises(ValueError):
        fuel_combustion(Fuel.FUEL_OIL, 10, CombustionType.MOBILE)


@pytest.mark.parametrize("kwargs", [{"quantity": -1}, {"quantity": 1, "density_kg_per_l": 0}])
def test_rejects_invalid_input(kwargs):
    with pytest.raises(ValueError):
        fuel_combustion(Fuel.DIESEL, combustion=CombustionType.MOBILE, **kwargs)
