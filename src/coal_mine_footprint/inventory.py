"""Tổng hợp kiểm kê khí nhà kính (KNK) cho mỏ than hầm lò.

Gom các nguồn phát thải của một kỳ báo cáo thành danh sách dòng kết quả theo
phạm vi của GHG Protocol:

- Scope 1: CH4 khai thác và sau khai thác, đốt CH4 thu hồi, đốt nhiên liệu,
  vật liệu nổ.
- Scope 2: điện năng mua từ lưới (phương pháp theo vị trí).
"""

from dataclasses import dataclass, field
from enum import IntEnum

from coal_mine_footprint.combustion import (
    FUELS,
    CombustionType,
    Fuel,
    fuel_combustion,
    fuel_use_label,
)
from coal_mine_footprint.ghg import DEFAULT_GWP, GasEmissions, gwp_factors
from coal_mine_footprint.methane import (
    TIER1_MINING_EF,
    TIER1_POST_MINING_EF,
    EmissionFactorLevel,
    MiningMethod,
    m3_to_tonnes,
)

# Tỷ lệ khối lượng CO2 / CH4 khi đốt cháy hoàn toàn (44 / 16).
CO2_PER_CH4 = 44 / 16

# Hệ số CO2 của thuốc nổ (t CO2 / t thuốc nổ): ước tính cho ANFO gồm khoảng
# 94,5% amoni nitrat và 5,5% dầu diesel, carbon trong dầu cháy hết thành CO2.
# Nên thay bằng hệ số theo thành phần thuốc nổ thực tế của mỏ.
DEFAULT_EXPLOSIVE_EF = 0.17


class MethaneTier(IntEnum):
    TIER1 = 1  # hệ số mặc định của IPCC
    TIER2 = 2  # hệ số riêng của mỏ / bể than
    TIER3 = 3  # thể tích CH4 đo thực tế


@dataclass(frozen=True)
class FuelUse:
    """Một loại nhiên liệu tiêu thụ trong kỳ, theo đơn vị ``FUELS[fuel].unit``."""

    fuel: Fuel
    combustion: CombustionType
    quantity: float


@dataclass
class InventoryInput:
    """Toàn bộ số liệu đầu vào của một kỳ kiểm kê."""

    facility_name: str = ""
    address: str = ""
    reporting_year: int = 2025
    prepared_by: str = ""
    gwp: str = DEFAULT_GWP

    coal_production_t: float = 0.0

    methane_tier: MethaneTier = MethaneTier.TIER1
    methane_level: EmissionFactorLevel = EmissionFactorLevel.AVERAGE
    mining_ef: float | None = None  # m³/t, Tier 2
    post_mining_ef: float | None = None  # m³/t, Tier 2 (tùy chọn ở Tier 3)
    measured_mining_m3: float | None = None  # m³, Tier 3
    recovered_combusted_m3: float = 0.0  # CH4 thu hồi và đốt tại mỏ

    fuels: list[FuelUse] = field(default_factory=list)
    densities_kg_per_l: dict[Fuel, float] = field(
        default_factory=lambda: {
            f: p.density_kg_per_l for f, p in FUELS.items() if p.density_kg_per_l
        }
    )

    electricity_kwh: float = 0.0
    grid_ef_t_per_mwh: float = 0.0

    explosives_kg: float = 0.0
    explosives_ef_t_per_t: float = DEFAULT_EXPLOSIVE_EF


@dataclass(frozen=True)
class MethaneBasis:
    """Thể tích CH4 phát sinh và hệ số (m³/t) đã dùng để tính."""

    mining_m3: float
    post_mining_m3: float
    mining_ef: float | None  # None khi dùng số đo Tier 3
    post_mining_ef: float


@dataclass(frozen=True)
class EmissionLine:
    scope: int
    source: str
    gases: GasEmissions


@dataclass(frozen=True)
class InventoryResult:
    lines: tuple[EmissionLine, ...]
    gwp: str
    coal_production_t: float

    def scope_co2e_t(self, scope: int) -> float:
        return sum(line.gases.co2e_t(self.gwp) for line in self.lines if line.scope == scope)

    @property
    def total_co2e_t(self) -> float:
        return sum(line.gases.co2e_t(self.gwp) for line in self.lines)

    @property
    def intensity_kg_per_t(self) -> float | None:
        """Cường độ phát thải (kgCO2e / tấn than); None nếu sản lượng bằng 0."""
        if self.coal_production_t <= 0:
            return None
        return self.total_co2e_t * 1000 / self.coal_production_t


def methane_basis(inp: InventoryInput) -> MethaneBasis:
    """Xác định thể tích CH4 khai thác và sau khai thác theo Tier đã chọn."""
    level = EmissionFactorLevel(inp.methane_level)
    tier1_mining = TIER1_MINING_EF[MiningMethod.UNDERGROUND][level]
    tier1_post = TIER1_POST_MINING_EF[MiningMethod.UNDERGROUND][level]
    production = inp.coal_production_t
    tier = MethaneTier(inp.methane_tier)

    if tier is MethaneTier.TIER1:
        mining_ef, post_ef = tier1_mining, tier1_post
    elif tier is MethaneTier.TIER2:
        if inp.mining_ef is None or inp.post_mining_ef is None:
            raise ValueError("Tier 2 cần nhập hệ số CH4 khai thác và sau khai thác")
        mining_ef, post_ef = inp.mining_ef, inp.post_mining_ef
    else:
        if inp.measured_mining_m3 is None:
            raise ValueError("Tier 3 cần nhập thể tích CH4 đo được")
        if inp.measured_mining_m3 < 0:
            raise ValueError("Thể tích CH4 đo được phải không âm")
        mining_ef = None
        post_ef = tier1_post if inp.post_mining_ef is None else inp.post_mining_ef

    if (mining_ef is not None and mining_ef < 0) or post_ef < 0:
        raise ValueError("Hệ số phát thải CH4 phải không âm")
    mining_m3 = inp.measured_mining_m3 if mining_ef is None else production * mining_ef
    return MethaneBasis(mining_m3, production * post_ef, mining_ef, post_ef)


def compute_inventory(inp: InventoryInput) -> InventoryResult:
    """Tính kết quả kiểm kê KNK từ số liệu đầu vào."""
    gwp_factors(inp.gwp)
    for label, value in [
        ("Sản lượng than", inp.coal_production_t),
        ("CH4 thu hồi", inp.recovered_combusted_m3),
        ("Điện năng tiêu thụ", inp.electricity_kwh),
        ("Hệ số phát thải lưới điện", inp.grid_ef_t_per_mwh),
        ("Khối lượng thuốc nổ", inp.explosives_kg),
        ("Hệ số phát thải thuốc nổ", inp.explosives_ef_t_per_t),
    ]:
        if value < 0:
            raise ValueError(f"{label} phải không âm")

    basis = methane_basis(inp)
    if inp.recovered_combusted_m3 > basis.mining_m3:
        raise ValueError("Lượng CH4 thu hồi vượt quá lượng CH4 phát sinh trong khai thác")

    lines = [
        EmissionLine(
            1,
            "CH4 thoát ra trong khai thác hầm lò",
            GasEmissions(ch4_t=m3_to_tonnes(basis.mining_m3 - inp.recovered_combusted_m3)),
        ),
        EmissionLine(
            1, "CH4 phát thải sau khai thác", GasEmissions(ch4_t=m3_to_tonnes(basis.post_mining_m3))
        ),
    ]
    if inp.recovered_combusted_m3 > 0:
        co2 = m3_to_tonnes(inp.recovered_combusted_m3) * CO2_PER_CH4
        lines.append(EmissionLine(1, "Đốt CH4 thu hồi tại mỏ", GasEmissions(co2_t=co2)))

    # Gộp các dòng nhiên liệu trùng loại và trùng loại nguồn.
    fuel_totals: dict[tuple[Fuel, CombustionType], GasEmissions] = {}
    for use in inp.fuels:
        key = (Fuel(use.fuel), CombustionType(use.combustion))
        gases = fuel_combustion(
            key[0], use.quantity, key[1], density_kg_per_l=inp.densities_kg_per_l.get(key[0])
        )
        fuel_totals[key] = fuel_totals.get(key, GasEmissions()) + gases
    for (fuel, combustion), gases in fuel_totals.items():
        lines.append(EmissionLine(1, f"Đốt nhiên liệu: {fuel_use_label(fuel, combustion)}", gases))

    lines.append(
        EmissionLine(
            1,
            "Sử dụng vật liệu nổ",
            GasEmissions(co2_t=inp.explosives_kg / 1000 * inp.explosives_ef_t_per_t),
        )
    )
    lines.append(
        EmissionLine(
            2,
            "Điện năng mua từ lưới",
            GasEmissions(co2_t=inp.electricity_kwh / 1000 * inp.grid_ef_t_per_mwh),
        )
    )
    return InventoryResult(tuple(lines), inp.gwp, inp.coal_production_t)
