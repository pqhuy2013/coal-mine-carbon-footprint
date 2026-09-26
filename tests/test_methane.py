import pytest

from coal_mine_footprint import (
    EmissionFactorLevel,
    MethaneEmissions,
    MiningMethod,
    fugitive_methane,
)


def test_underground_tier1_average():
    # 1.000.000 t x (18 + 2,5) m³/t = 20.500.000 m³ CH4
    result = fugitive_methane(1_000_000, MiningMethod.UNDERGROUND)
    assert result.net_m3 == pytest.approx(20_500_000)
    # 20.500.000 m³ x 0,67 kg/m³ = 13.735 t CH4
    assert result.ch4_tonnes == pytest.approx(13_735)
    assert result.co2e_tonnes("AR6") == pytest.approx(13_735 * 29.8)
    assert result.co2e_tonnes("AR5") == pytest.approx(13_735 * 28)


def test_surface_tier1_levels():
    low = fugitive_methane(1000, "surface", level="low")
    high = fugitive_methane(1000, MiningMethod.SURFACE, level=EmissionFactorLevel.HIGH)
    assert low.net_m3 == pytest.approx(300)
    assert high.net_m3 == pytest.approx(2200)


def test_tier2_custom_factors():
    result = fugitive_methane(500, MiningMethod.UNDERGROUND, mining_ef=12.0, post_mining_ef=1.5)
    assert result.mining_m3 == pytest.approx(6000)
    assert result.post_mining_m3 == pytest.approx(750)


def test_recovered_methane_is_subtracted():
    result = fugitive_methane(1000, MiningMethod.UNDERGROUND, recovered_m3=5000)
    assert result.net_m3 == pytest.approx(20_500 - 5000)


def test_tier3_measured_volumes():
    result = MethaneEmissions(mining_m3=1_000_000, post_mining_m3=0)
    assert result.ch4_tonnes == pytest.approx(670)


def test_zero_production():
    assert fugitive_methane(0, MiningMethod.SURFACE).co2e_tonnes() == 0


@pytest.mark.parametrize(
    "kwargs",
    [
        {"production_tonnes": -1},
        {"production_tonnes": 1000, "mining_ef": -1.0},
        {"production_tonnes": 1000, "recovered_m3": -1.0},
        {"production_tonnes": 1000, "recovered_m3": 1e9},
    ],
)
def test_rejects_invalid_input(kwargs):
    with pytest.raises(ValueError):
        fugitive_methane(method=MiningMethod.UNDERGROUND, **kwargs)


def test_rejects_unknown_gwp():
    with pytest.raises(ValueError):
        fugitive_methane(1000, MiningMethod.SURFACE).co2e_tonnes("AR3")
