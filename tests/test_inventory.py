import pytest

from coal_mine_footprint.combustion import CombustionType, Fuel, fuel_combustion
from coal_mine_footprint.inventory import (
    FuelUse,
    InventoryInput,
    MethaneTier,
    compute_inventory,
)
from coal_mine_footprint.methane import EmissionFactorLevel


def lines_by_source(result):
    return {line.source: line for line in result.lines}


def test_full_inventory_tier1():
    inp = InventoryInput(
        coal_production_t=1_000_000,
        recovered_combusted_m3=1_000_000,
        fuels=[
            FuelUse(Fuel.DIESEL, CombustionType.MOBILE, 600_000),
            FuelUse(Fuel.DIESEL, CombustionType.MOBILE, 400_000),
        ],
        electricity_kwh=50_000_000,
        grid_ef_t_per_mwh=0.6,
        explosives_kg=200_000,
    )
    result = compute_inventory(inp)
    lines = lines_by_source(result)

    # CH4 khai thác: (18.000.000 - 1.000.000) m³ x 0,67 kg/m³ = 11.390 t
    assert lines["CH4 thoát ra trong khai thác hầm lò"].gases.ch4_t == pytest.approx(11_390)
    assert lines["CH4 phát thải sau khai thác"].gases.ch4_t == pytest.approx(1_675)
    # Đốt 670 t CH4 thu hồi -> 670 x 44/16 t CO2
    assert lines["Đốt CH4 thu hồi tại mỏ"].gases.co2_t == pytest.approx(670 * 44 / 16)
    # Hai dòng diesel di động được gộp thành một
    diesel = lines["Đốt nhiên liệu: Dầu diesel (nguồn di động)"].gases
    expected = fuel_combustion(Fuel.DIESEL, 1_000_000, CombustionType.MOBILE)
    assert (diesel.co2_t, diesel.ch4_t, diesel.n2o_t) == pytest.approx(
        (expected.co2_t, expected.ch4_t, expected.n2o_t)
    )
    assert lines["Sử dụng vật liệu nổ"].gases.co2_t == pytest.approx(200 * 0.17)
    assert lines["Điện năng mua từ lưới"].scope == 2
    assert lines["Điện năng mua từ lưới"].gases.co2_t == pytest.approx(30_000)

    assert result.scope_co2e_t(2) == pytest.approx(30_000)
    assert result.total_co2e_t == pytest.approx(result.scope_co2e_t(1) + 30_000)
    assert result.intensity_kg_per_t == pytest.approx(result.total_co2e_t * 1000 / 1_000_000)


def test_tier1_level():
    inp = InventoryInput(coal_production_t=1000, methane_level=EmissionFactorLevel.HIGH)
    lines = lines_by_source(compute_inventory(inp))
    assert lines["CH4 thoát ra trong khai thác hầm lò"].gases.ch4_t == pytest.approx(25 * 0.67)
    assert lines["CH4 phát thải sau khai thác"].gases.ch4_t == pytest.approx(4 * 0.67)


def test_tier2_requires_factors():
    with pytest.raises(ValueError):
        compute_inventory(InventoryInput(coal_production_t=1000, methane_tier=MethaneTier.TIER2))
    inp = InventoryInput(
        coal_production_t=1000, methane_tier=MethaneTier.TIER2, mining_ef=10, post_mining_ef=1
    )
    lines = lines_by_source(compute_inventory(inp))
    assert lines["CH4 thoát ra trong khai thác hầm lò"].gases.ch4_t == pytest.approx(6.7)


def test_tier3_measured():
    inp = InventoryInput(
        coal_production_t=1000, methane_tier=MethaneTier.TIER3, measured_mining_m3=100_000
    )
    lines = lines_by_source(compute_inventory(inp))
    assert lines["CH4 thoát ra trong khai thác hầm lò"].gases.ch4_t == pytest.approx(67)
    # Sau khai thác mặc định dùng hệ số trung bình Tier 1
    assert lines["CH4 phát thải sau khai thác"].gases.ch4_t == pytest.approx(2.5 * 0.67)


def test_zero_production_has_no_intensity():
    result = compute_inventory(InventoryInput())
    assert result.total_co2e_t == 0
    assert result.intensity_kg_per_t is None


@pytest.mark.parametrize(
    "kwargs",
    [
        {"coal_production_t": -1},
        {"electricity_kwh": -1},
        {"explosives_kg": -1},
        {"recovered_combusted_m3": 1e12},
        {"gwp": "AR3"},
        {"methane_tier": MethaneTier.TIER3},
    ],
)
def test_rejects_invalid_input(kwargs):
    with pytest.raises(ValueError):
        compute_inventory(InventoryInput(**{"coal_production_t": 1000, **kwargs}))
