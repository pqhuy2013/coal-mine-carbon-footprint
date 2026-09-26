"""Phát thải khí mê-tan (CH4) từ khai thác than.

Phương pháp theo IPCC 2006 Guidelines, Tập 2, Chương 4.1 (Coal mining and
handling):

    CH4 = sản lượng than x hệ số phát thải x khối lượng riêng CH4

tính riêng cho giai đoạn khai thác và sau khai thác, rồi trừ đi lượng CH4
được thu hồi để sử dụng hoặc đốt bỏ. CO2 sinh ra khi đốt CH4 thu hồi không
tính ở đây.

- Tier 1: dùng hệ số mặc định của IPCC (``level`` = low / average / high).
- Tier 2: truyền hệ số riêng của quốc gia hoặc bể than qua ``mining_ef`` và
  ``post_mining_ef``.
- Tier 3: tạo trực tiếp ``MethaneEmissions`` từ thể tích CH4 đo được tại mỏ.
"""

from dataclasses import dataclass
from enum import Enum


class MiningMethod(str, Enum):
    """Phương pháp khai thác."""

    UNDERGROUND = "underground"  # hầm lò
    SURFACE = "surface"  # lộ thiên


class EmissionFactorLevel(str, Enum):
    """Mức hệ số phát thải mặc định của IPCC (Tier 1).

    Hầm lò: ``LOW`` cho mỏ sâu dưới 200 m, ``HIGH`` cho mỏ sâu trên 400 m.
    Lộ thiên: ``LOW`` cho tầng phủ dày dưới 25 m, ``HIGH`` cho tầng phủ dày
    trên 50 m. Các trường hợp còn lại dùng ``AVERAGE``.
    """

    LOW = "low"
    AVERAGE = "average"
    HIGH = "high"


# Khối lượng riêng của CH4 ở 20 °C và 1 atm (kg/m³), theo IPCC 2006.
CH4_DENSITY_KG_PER_M3 = 0.67

# Hệ số phát thải mặc định Tier 1 của IPCC 2006 (m³ CH4 / tấn than).
TIER1_MINING_EF: dict[MiningMethod, dict[EmissionFactorLevel, float]] = {
    MiningMethod.UNDERGROUND: {
        EmissionFactorLevel.LOW: 10.0,
        EmissionFactorLevel.AVERAGE: 18.0,
        EmissionFactorLevel.HIGH: 25.0,
    },
    MiningMethod.SURFACE: {
        EmissionFactorLevel.LOW: 0.3,
        EmissionFactorLevel.AVERAGE: 1.2,
        EmissionFactorLevel.HIGH: 2.0,
    },
}

TIER1_POST_MINING_EF: dict[MiningMethod, dict[EmissionFactorLevel, float]] = {
    MiningMethod.UNDERGROUND: {
        EmissionFactorLevel.LOW: 0.9,
        EmissionFactorLevel.AVERAGE: 2.5,
        EmissionFactorLevel.HIGH: 4.0,
    },
    MiningMethod.SURFACE: {
        EmissionFactorLevel.LOW: 0.0,
        EmissionFactorLevel.AVERAGE: 0.1,
        EmissionFactorLevel.HIGH: 0.2,
    },
}

# Hệ số tiềm năng nóng lên toàn cầu 100 năm của CH4 theo báo cáo IPCC.
# AR6 dùng giá trị cho CH4 có nguồn gốc hóa thạch.
GWP100_CH4: dict[str, float] = {"AR4": 25.0, "AR5": 28.0, "AR6": 29.8}


@dataclass(frozen=True)
class MethaneEmissions:
    """Thể tích CH4 phát thải (m³) của một mỏ trong kỳ báo cáo."""

    mining_m3: float
    post_mining_m3: float
    recovered_m3: float = 0.0

    def __post_init__(self) -> None:
        if min(self.mining_m3, self.post_mining_m3, self.recovered_m3) < 0:
            raise ValueError("thể tích CH4 phải không âm")
        if self.recovered_m3 > self.mining_m3 + self.post_mining_m3:
            raise ValueError("lượng CH4 thu hồi vượt quá lượng CH4 phát sinh")

    @property
    def net_m3(self) -> float:
        """Thể tích CH4 thực phát thải ra khí quyển (m³)."""
        return self.mining_m3 + self.post_mining_m3 - self.recovered_m3

    @property
    def ch4_tonnes(self) -> float:
        """Khối lượng CH4 thực phát thải (tấn)."""
        return self.net_m3 * CH4_DENSITY_KG_PER_M3 / 1000

    def co2e_tonnes(self, gwp: str = "AR6") -> float:
        """Phát thải quy đổi ra tấn CO2 tương đương theo GWP đã chọn."""
        if gwp not in GWP100_CH4:
            raise ValueError(f"gwp phải là một trong {sorted(GWP100_CH4)}")
        return self.ch4_tonnes * GWP100_CH4[gwp]


def fugitive_methane(
    production_tonnes: float,
    method: MiningMethod,
    *,
    level: EmissionFactorLevel = EmissionFactorLevel.AVERAGE,
    mining_ef: float | None = None,
    post_mining_ef: float | None = None,
    recovered_m3: float = 0.0,
) -> MethaneEmissions:
    """Tính phát thải CH4 từ khai thác và sau khai thác than.

    ``production_tonnes`` là sản lượng than nguyên khai (tấn). Nếu không truyền
    ``mining_ef`` / ``post_mining_ef`` (m³ CH4 / tấn), hàm dùng hệ số mặc định
    Tier 1 của IPCC theo ``method`` và ``level``.
    """
    if production_tonnes < 0:
        raise ValueError("production_tonnes phải không âm")
    method = MiningMethod(method)
    level = EmissionFactorLevel(level)
    if mining_ef is None:
        mining_ef = TIER1_MINING_EF[method][level]
    if post_mining_ef is None:
        post_mining_ef = TIER1_POST_MINING_EF[method][level]
    if mining_ef < 0 or post_mining_ef < 0:
        raise ValueError("hệ số phát thải phải không âm")
    return MethaneEmissions(
        mining_m3=production_tonnes * mining_ef,
        post_mining_m3=production_tonnes * post_mining_ef,
        recovered_m3=recovered_m3,
    )
