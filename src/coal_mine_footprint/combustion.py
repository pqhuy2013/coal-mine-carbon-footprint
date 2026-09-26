"""Phát thải từ đốt nhiên liệu tại mỏ (Scope 1).

Phương pháp Tier 1 theo IPCC 2006 Guidelines, Tập 2:

- Nguồn cố định (máy phát điện, lò hơi): Chương 2, Bảng 2.3.
- Nguồn di động: Chương 3. Dầu diesel dùng hệ số cho máy móc phi đường bộ
  trong công nghiệp (Bảng 3.3.1); xăng dùng hệ số cho xe đường bộ chưa có bộ
  xúc tác (Bảng 3.2.2).

Hệ số CO2 và nhiệt trị thực (NCV) lấy từ Bảng 1.2 và 1.4, Chương 1. Giả định
nhiên liệu cháy hoàn toàn (hệ số oxy hóa bằng 1).
"""

from dataclasses import dataclass
from enum import Enum

from coal_mine_footprint.ghg import GasEmissions


class Fuel(str, Enum):
    DIESEL = "diesel"
    GASOLINE = "gasoline"
    FUEL_OIL = "fuel_oil"
    LPG = "lpg"


class CombustionType(str, Enum):
    STATIONARY = "stationary"  # nguồn cố định
    MOBILE = "mobile"  # nguồn di động


@dataclass(frozen=True)
class FuelProperties:
    label: str
    unit: str  # đơn vị nhập số lượng: "lít" hoặc "tấn"
    density_kg_per_l: float | None  # chỉ dùng cho nhiên liệu nhập theo lít
    ncv_tj_per_gg: float
    co2_kg_per_tj: float
    stationary_kg_per_tj: tuple[float, float]  # (CH4, N2O)
    mobile_kg_per_tj: tuple[float, float] | None  # (CH4, N2O)


FUELS: dict[Fuel, FuelProperties] = {
    Fuel.DIESEL: FuelProperties("Dầu diesel", "lít", 0.84, 43.0, 74_100, (3.0, 0.6), (4.15, 28.6)),
    Fuel.GASOLINE: FuelProperties("Xăng", "lít", 0.74, 44.3, 69_300, (3.0, 0.6), (33.0, 3.2)),
    Fuel.FUEL_OIL: FuelProperties("Dầu FO", "tấn", None, 40.4, 77_400, (3.0, 0.6), None),
    Fuel.LPG: FuelProperties("LPG", "tấn", None, 47.3, 63_100, (1.0, 0.1), None),
}


def fuel_use_label(fuel: Fuel, combustion: CombustionType) -> str:
    """Tên hiển thị của một loại nhiên liệu theo loại nguồn, ví dụ "Dầu diesel (nguồn di động)"."""
    kind = "cố định" if CombustionType(combustion) is CombustionType.STATIONARY else "di động"
    return f"{FUELS[Fuel(fuel)].label} (nguồn {kind})"


def fuel_combustion(
    fuel: Fuel,
    quantity: float,
    combustion: CombustionType,
    *,
    density_kg_per_l: float | None = None,
) -> GasEmissions:
    """Tính phát thải CO2, CH4, N2O khi đốt một lượng nhiên liệu.

    ``quantity`` tính theo đơn vị ``FUELS[fuel].unit``. Với nhiên liệu nhập
    theo lít, có thể truyền ``density_kg_per_l`` để thay khối lượng riêng mặc
    định.
    """
    fuel = Fuel(fuel)
    combustion = CombustionType(combustion)
    props = FUELS[fuel]
    if quantity < 0:
        raise ValueError(f"Số lượng {props.label} phải không âm")

    if props.unit == "lít":
        density = props.density_kg_per_l if density_kg_per_l is None else density_kg_per_l
        if density <= 0:
            raise ValueError(f"Khối lượng riêng của {props.label} phải lớn hơn 0")
        mass_t = quantity * density / 1000
    else:
        mass_t = quantity

    if combustion is CombustionType.STATIONARY:
        ch4_ef, n2o_ef = props.stationary_kg_per_tj
    elif props.mobile_kg_per_tj is not None:
        ch4_ef, n2o_ef = props.mobile_kg_per_tj
    else:
        raise ValueError(f"{props.label} chưa được hỗ trợ cho nguồn di động")

    energy_tj = mass_t * props.ncv_tj_per_gg / 1000
    return GasEmissions(
        co2_t=energy_tj * props.co2_kg_per_tj / 1000,
        ch4_t=energy_tj * ch4_ef / 1000,
        n2o_t=energy_tj * n2o_ef / 1000,
    )
